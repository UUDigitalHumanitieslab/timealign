from django import forms

from .models import Annotation, Word


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
        structure = self.alignment.original_fragment.get_formal_structure()

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
