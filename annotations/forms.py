from django import forms

from .models import Annotation, Word, Language, Tense, Label
from .management.commands.import_tenses import process_file


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

        super().__init__(*args, **kwargs)
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


class AnnotationForm(forms.ModelForm):
    # a hidden field used to remember the user's prefered selection tool
    select_segment = forms.BooleanField(widget=forms.HiddenInput(),
                                        required=False)

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
        Filters the Words on the translated language.
        """
        self.alignment = kwargs.pop('alignment', None)
        translated_fragment = self.alignment.translated_fragment
        label = self.alignment.original_fragment.get_labels()
        structure = self.alignment.original_fragment.get_formal_structure_display()

        self.user = kwargs.pop('user', None)
        select_segment = kwargs.pop('select_segment', False)

        super(AnnotationForm, self).__init__(*args, **kwargs)
        self.fields['words'].queryset = Word.objects.filter(sentence__fragment=translated_fragment)
        self.fields['is_no_target'].label = self.fields['is_no_target'].label.format(label)
        self.fields['is_not_labeled_structure'].label = self.fields['is_not_labeled_structure'].label.format(structure)
        self.fields['tense'].queryset = Tense.objects.filter(language=self.alignment.translated_fragment.language)
        self.fields['select_segment'].initial = select_segment

        language = self.alignment.translated_fragment.language
        # add a label field for each label key
        for key in self.corpus.label_keys.all():
            existing_label = self.instance.labels.filter(key=key).first() if self.instance.id else None
            field = LabelField(required=False,
                               label_key=key,
                               language=language,
                               initial=existing_label)
            self.fields[key.symbol()] = field

        # hide the original field for labels.
        # we still need this field defined in AnnotationForm.fields, otherwise
        # the value set in AnnotationForm.clean() will not be used when submitting the form.
        del self.fields['labels']

        if not self.corpus.check_structure:
            del self.fields['is_not_labeled_structure']
            del self.fields['is_not_same_structure']

        # Only allow to edit tense/other_label if the current User has this permission
        if not self.user.has_perm('annotations.edit_labels_in_interface'):
            del self.fields['tense']

        # Comments should be the last form field
        self.fields.move_to_end('comments')

    @property
    def corpus(self):
        return self.alignment.original_fragment.document.corpus

    def clean(self):
        """
        Check for conditional requirements:
        - If is_translation is set, make sure Words have been selected
        """
        cleaned_data = super(AnnotationForm, self).clean()
        # construct a value for Annotation.labels based on the individual label fields
        fields = [key.symbol() for key in self.corpus.label_keys.all()]
        cleaned_data['labels'] = [cleaned_data[field] for field in fields]

        if not cleaned_data['is_no_target'] and cleaned_data['is_translation']:
            if not cleaned_data['words']:
                self.add_error('is_translation', 'Please select the words composing the translation.')


class LabelImportForm(forms.Form):
    label_file = forms.FileField(
        help_text='This should be a tab-separated file, with id and label as columns.'
                  'The first row (header) will not be imported.')
    language = forms.ModelChoiceField(
        queryset=Language.objects.all()
    )
    model = forms.ChoiceField(
        choices=(('annotation', 'Annotation'), ('fragment', 'Fragment'),),
        initial='annotation',
        help_text='Select Fragment in case you want to import labels for the source Fragments, '
                  'rather than the Annotations.')

    def save(self):
        data = self.cleaned_data

        process_file(data['label_file'], data['language'], data['model'])


class SubSentenceFormSet(forms.BaseInlineFormSet):
    def get_form_kwargs(self, index):
        kwargs = super(SubSentenceFormSet, self).get_form_kwargs(index)
        kwargs['subcorpus'] = self.instance
        return kwargs


class SubSentenceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.subcorpus = kwargs.pop('subcorpus', None)
        super(SubSentenceForm, self).__init__(*args, **kwargs)

        # If the Corpus has been set, filter the Documents based on the Corpus
        if self.subcorpus:
            self.fields['document'].queryset = self.fields['document'].queryset.filter(corpus=self.subcorpus.corpus)
