from django import forms

from .models import Annotation, Word


class AnnotationForm(forms.ModelForm):
    class Meta:
        model = Annotation
        fields = [
            'is_no_target', 'is_translation', 'comments', 'words',
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

        label = self.alignment.original_fragment.label()

        super(AnnotationForm, self).__init__(*args, **kwargs)
        self.fields['words'].queryset = Word.objects.filter(sentence__in=translated_sentences)
        self.fields['is_no_target'].label = u'The selected words in the original fragment do not form an instance of (a/an) <em>{}</em>'.format(label)

    def clean(self):
        """
        Check for conditional requirements:
        - If is_translation is set, make sure Words have been selected
        """
        cleaned_data = super(AnnotationForm, self).clean()

        if not cleaned_data['is_no_target'] and cleaned_data['is_translation']:
            if not cleaned_data['words']:
                self.add_error('is_translation', 'Please select the words composing the translation.')
