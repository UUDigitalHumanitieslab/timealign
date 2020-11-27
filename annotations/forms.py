from django import forms

from .models import Annotation, Word, Language, Tense, Label, Corpus, Fragment, LabelKey
from .management.commands.import_tenses import process_file as process_labels_file
from .management.commands.add_fragments import process_file as process_fragments_file


class LabelField(forms.ModelChoiceField):
    """A text field for labels with auto completion (provided by select2 in JS).
    Tied to a specific LabelKey"""

    def __init__(self, label_key, language, *args, **kwargs):
        self._key = label_key
        self._language = language
        queryset = label_key.labels.all()
        if self._key.language_specific:
            queryset = queryset.filter(language=language)
        kwargs['queryset'] = queryset

        super(LabelField, self).__init__(*args, **kwargs)
        if self.is_adding_labels_allowed():
            self.widget.attrs['class'] = 'labels-field-tags'
        else:
            self.widget.attrs['class'] = 'labels-field'

    def is_adding_labels_allowed(self):
        return self._key.open_label_set

    # MultipleChoiceField only allows entering predefined choices
    # however, we want users to be able to introduce new labels,
    # which is why it's necessary to override the default clean() method
    def clean(self, value):
        if value.isdigit():
            # it's a pk of an existing label
            return Label.objects.get(pk=int(value))
        if not value:
            # labels cannot be empty
            return None
        if self._key.language_specific:
            label, created = Label.objects.get_or_create(
                title=value, key=self._key, language=self._language)
        else:
            label, created = Label.objects.get_or_create(title=value, key=self._key)

        if created:
            if self.is_adding_labels_allowed():
                label.save()
            else:
                # user attempted to add a new label but is not allowed
                return None
        return label


class LabelFormMixin(forms.Form):
    def __init__(self, *args, **kwargs):
        super(LabelFormMixin, self).__init__(*args, **kwargs)

        # add a label field for each label key
        for key in self.corpus.label_keys.all():
            existing_label = self.instance.labels.filter(key=key).first() if self.instance.id else None
            field = LabelField(required=False,
                               label_key=key,
                               language=self.language,
                               initial=existing_label)
            self.fields[key.symbol()] = field

        # hide the original field for labels.
        # we still need this field defined in fields of the Form, otherwise
        # the value set in clean() will not be used when submitting the form.
        del self.fields['labels']

    def clean(self):
        cleaned_data = super(LabelFormMixin, self).clean()

        # construct a value for Annotation/Fragment/PreProcessFragment.labels based on the individual label fields
        fields = [key.symbol() for key in self.corpus.label_keys.all()]
        cleaned_data['labels'] = [cleaned_data[field] for field in fields if cleaned_data[field]]

        return cleaned_data

    @property
    def corpus(self) -> Corpus:
        raise NotImplementedError

    @property
    def language(self) -> Language:
        raise NotImplementedError


class SegmentSelectMixin(forms.Form):
    # a hidden field used to remember the user's preferred selection tool
    select_segment = forms.BooleanField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        select_segment = kwargs.pop('select_segment', False)

        super(SegmentSelectMixin, self).__init__(*args, **kwargs)
        self.fields['select_segment'].initial = select_segment


class AnnotationForm(LabelFormMixin, SegmentSelectMixin, forms.ModelForm):
    class Meta:
        model = Annotation
        fields = [
            'is_no_target', 'is_translation',
            'is_not_labeled_structure', 'is_not_same_structure',
            'tense', 'labels',
            'comments', 'words',
            'select_segment'
        ]
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        """
        - formats the form labels with actual values
        - filters the words/tense field based on the translated Fragment
        - removes formal_structure and sentence_function fields if the structure needs not to be checked
        - allow to edit Tense if the current User has this permission
        - move comments to the end
        """
        self.alignment = kwargs.pop('alignment')
        self.user = kwargs.pop('user', None)

        translated_fragment = self.alignment.translated_fragment
        label = self.alignment.original_fragment.get_labels()
        structure = self.alignment.original_fragment.get_formal_structure_display()

        super(AnnotationForm, self).__init__(*args, **kwargs)

        self.fields['is_no_target'].label = self.fields['is_no_target'].label.format(label)
        self.fields['is_not_labeled_structure'].label = self.fields['is_not_labeled_structure'].label.format(structure)

        self.fields['tense'].queryset = Tense.objects.filter(language=translated_fragment.language)
        self.fields['words'].queryset = Word.objects.filter(sentence__fragment=translated_fragment)

        if not self.corpus.check_structure:
            del self.fields['is_not_labeled_structure']
            del self.fields['is_not_same_structure']

        if not self.user.has_perm('annotations.edit_labels_in_interface') or not self.corpus.tense_based:
            del self.fields['tense']

        self.fields.move_to_end('comments')

    def clean(self):
        """
        Check for conditional requirements:
        - If is_translation is set, make sure Words have been selected
        """
        cleaned_data = super(AnnotationForm, self).clean()

        if not cleaned_data['is_no_target'] and cleaned_data['is_translation']:
            if not cleaned_data['words']:
                self.add_error('is_translation', 'Please select the words composing the translation.')

        return cleaned_data

    @property
    def corpus(self):
        return self.alignment.original_fragment.document.corpus

    @property
    def language(self):
        return self.alignment.translated_fragment.language


class FragmentForm(LabelFormMixin, SegmentSelectMixin, forms.ModelForm):
    words = forms.ModelMultipleChoiceField(queryset=Word.objects.none(), required=False)

    class Meta:
        model = Fragment
        fields = [
            'tense', 'labels',
            'formal_structure', 'sentence_function',
            'words',
            'select_segment'
        ]

    def __init__(self, *args, **kwargs):
        """
        - filters the words/tense field based on the translated Fragment
        - sets initial value for the words field
        - removes formal_structure and sentence_function fields if the structure needs not to be checked
        - removes tense fields if the corpus is not tense-based
        """
        self.fragment = kwargs.get('instance')

        super(FragmentForm, self).__init__(*args, **kwargs)

        self.fields['tense'].queryset = Tense.objects.filter(language=self.language)
        self.fields['words'].queryset = Word.objects.filter(sentence__fragment=self.fragment)
        self.fields['words'].initial = self.fragment.targets()

        if not self.corpus.check_structure:
            del self.fields['formal_structure']
            del self.fields['sentence_function']

        if not self.corpus.tense_based:
            del self.fields['tense']

    def clean(self):
        """
        - make sure Words have been selected
        """
        cleaned_data = super(FragmentForm, self).clean()

        if not cleaned_data['words']:
            self.add_error(None, 'Please select target words.')

        return cleaned_data

    @property
    def corpus(self):
        return self.fragment.document.corpus

    @property
    def language(self):
        return self.fragment.language


class LabelImportForm(forms.Form):
    label_file = forms.FileField(
        help_text='This should be a tab-separated file, with id and label as columns.'
                  'The first row (header) will not be imported.')
    language = forms.ModelChoiceField(queryset=Language.objects.all())
    model = forms.ChoiceField(
        choices=(('annotation', 'Annotation'), ('selection', 'Selection'), ('fragment', 'Fragment'),),
        initial='annotation',
        help_text='Select Annotation for importing labels for TimeAlign, '
                  'select Selection for importing labels for Preselect. '
                  'Select Fragment in case you want to import labels for the source Fragments, '
                  'rather than the Annotations.')

    def save(self):
        data = self.cleaned_data
        process_labels_file(data['label_file'], data['language'], data['model'])


class AddFragmentsForm(forms.Form):
    corpus = forms.ModelChoiceField(queryset=Corpus.objects.all())

    def __init__(self, *args, **kwargs):
        self.corpus = kwargs.pop('corpus')

        super().__init__(*args, **kwargs)

        if self.corpus:
            corpus = int(self.corpus)
            self.fields['corpus'].initial = corpus
            self.fields['fragment_file'] = forms.FileField(
                help_text='This should be a .csv-file generated by PerfectExtractor')
            choices = [('tense', 'Tense')]
            choices += LabelKey.objects.filter(corpora=corpus).values_list('pk', 'title').order_by('title')
            self.fields['annotation_types'] = forms.MultipleChoiceField(
                label='Treat type column(s) as:',
                choices=choices)

    def save(self):
        data = self.cleaned_data
        label_pks = data['annotation_types'] if data['annotation_types'] != ['tense'] else None
        process_fragments_file(data['fragment_file'], data['corpus'], label_pks=label_pks)


class SubSentenceFormSet(forms.BaseInlineFormSet):
    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs['subcorpus'] = self.instance
        return kwargs


class SubSentenceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.subcorpus = kwargs.pop('subcorpus', None)
        super().__init__(*args, **kwargs)

        qs = self.fields['document'].queryset
        # Select the Corpus to prevent queries being fired on the __str__ method
        qs = qs.select_related('corpus')
        # If the Corpus has been set on the SubCorpus, filter the Documents based on the Corpus
        if hasattr(self.subcorpus, 'corpus'):
            qs = qs.filter(corpus=self.subcorpus.corpus)
        self.fields['document'].queryset = qs
