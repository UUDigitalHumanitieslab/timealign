import codecs

from django import forms

from .models import Annotation, Word, Language
from .management.commands.import_tenses import process_file


class AnnotationForm(forms.ModelForm):
    class Meta:
        model = Annotation
        fields = [
            'is_no_target', 'is_translation', 'is_not_labeled_structure', 'is_not_same_structure', 'comments', 'words',
        ]
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        """
        Filters the Words on the translated language.
        """
        self.alignment = kwargs.pop('alignment', None)
        translated_sentences = self.alignment.translated_fragment.sentence_set.all()
        corpus = self.alignment.original_fragment.document.corpus
        label = self.alignment.original_fragment.label()
        structure = self.alignment.original_fragment.get_formal_structure_display()

        super(AnnotationForm, self).__init__(*args, **kwargs)
        self.fields['words'].queryset = Word.objects.filter(sentence__in=translated_sentences)
        self.fields['is_no_target'].label = self.fields['is_no_target'].label.format(label)
        self.fields['is_not_labeled_structure'].label = self.fields['is_not_labeled_structure'].label.format(structure)

        if not corpus.check_structure:
            del self.fields['is_not_labeled_structure']
            del self.fields['is_not_same_structure']

    def clean(self):
        """
        Check for conditional requirements:
        - If is_translation is set, make sure Words have been selected
        """
        cleaned_data = super(AnnotationForm, self).clean()

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
    use_other_label = forms.BooleanField(
        initial=False,
        required=False,
        label='The imported labels are not tense/aspect-labels, but other labels',
    )

    def save(self):
        data = self.cleaned_data

        process_file(data['label_file'], data['language'], data['use_other_label'], data['model'])
