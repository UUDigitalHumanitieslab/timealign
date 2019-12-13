from django import forms

from .models import Annotation, Word, Language, Tense
from .management.commands.import_tenses import process_file


class LabelsField(forms.MultipleChoiceField):
    # MultipleChoiceField only allows entering predefined choices
    # however, we want users to be able to introduce new labels,
    # which is why it's necessary to override the default clean() method
    def clean(self, value):
        return value


class AnnotationForm(forms.ModelForm):
    # a frontend field for adding multiple labels, which are saved as a
    # comma separated string in other_label
    labels = LabelsField()

    # a hidden field used to remember the user's prefered selection tool
    select_segment = forms.BooleanField(widget=forms.HiddenInput(),
                                        required=False)

    class Meta:
        model = Annotation
        fields = [
            'is_no_target', 'is_translation',
            'is_not_labeled_structure', 'is_not_same_structure',
            'tense', 'labels', 'other_label',
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
        corpus = self.alignment.original_fragment.document.corpus
        label = self.alignment.original_fragment.label()
        structure = self.alignment.original_fragment.get_formal_structure_display()

        self.user = kwargs.pop('user', None)
        select_segment = kwargs.pop('select_segment', False)

        super(AnnotationForm, self).__init__(*args, **kwargs)
        self.fields['words'].queryset = Word.objects.filter(sentence__fragment=translated_fragment)
        self.fields['is_no_target'].label = self.fields['is_no_target'].label.format(label)
        self.fields['is_not_labeled_structure'].label = self.fields['is_not_labeled_structure'].label.format(structure)
        self.fields['tense'].queryset = Tense.objects.filter(language=self.alignment.translated_fragment.language)
        self.fields['select_segment'].initial = select_segment

        # auto-complete labels based on all the existing labels in the corpus
        choices = set()
        existing_labels = Annotation.objects.filter(
            alignment__original_fragment__document__corpus=corpus).values_list('other_label', flat=True).distinct()
        for labels in existing_labels:
            for label in labels.split(','):
                choices.add(label)
        self.fields['labels'].choices = [(x, x) for x in choices if x]

        # when editing an existing annotation, populate the labels field
        if kwargs['instance']:
            self.fields['labels'].initial = kwargs['instance'].other_label.split(',')

        if not corpus.check_structure:
            del self.fields['is_not_labeled_structure']
            del self.fields['is_not_same_structure']

        # Only allow to edit tense/other_label if the current User has this permission
        if not self.user.has_perm('annotations.edit_labels_in_interface'):
            del self.fields['tense']
            del self.fields['other_label']

    def clean(self):
        """
        Check for conditional requirements:
        - If is_translation is set, make sure Words have been selected
        """
        cleaned_data = super(AnnotationForm, self).clean()

        if not cleaned_data['is_no_target'] and cleaned_data['is_translation']:
            if not cleaned_data['words']:
                self.add_error('is_translation', 'Please select the words composing the translation.')

    def clean_other_label(self):
        # store the labels selected in the front-end only labels field
        return ','.join(sorted(self.data.getlist('labels')))


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
    use_other_label = forms.BooleanField(
        initial=False,
        required=False,
        label='The imported labels are not tense/aspect-labels, but other labels',
    )

    def save(self):
        data = self.cleaned_data

        process_file(data['label_file'], data['language'], data['use_other_label'], data['model'])


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
