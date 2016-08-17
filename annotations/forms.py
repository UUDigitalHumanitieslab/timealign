from django import forms

from .models import Annotation, Word


class AnnotationForm(forms.ModelForm):
    class Meta:
        model = Annotation
        fields = [
            'is_no_target', 'is_translation', 'tense', 'words',
        ]

    def __init__(self, *args, **kwargs):
        """
        Filters the Words on the translated language.
        """
        self.alignment = kwargs.pop('alignment', None)
        translated_sentences = self.alignment.translated_fragment.sentence_set.all()

        super(AnnotationForm, self).__init__(*args, **kwargs)
        self.fields['words'].queryset = Word.objects.filter(sentence__in=translated_sentences)

    def clean(self):
        """
        Check for conditional requirements:
        - If is_translation is set, make sure Words have been selected
        """
        cleaned_data = super(AnnotationForm, self).clean()

        if not cleaned_data['is_no_target'] and cleaned_data['is_translation']:
            if not cleaned_data['words']:
                self.add_error('is_translation', 'Please select the words composing the translation.')


