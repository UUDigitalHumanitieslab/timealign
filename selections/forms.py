from django import forms

from .models import Selection, Word


class SelectionForm(forms.ModelForm):
    class Meta:
        model = Selection
        fields = [
            'is_no_target', 'words',
        ]

    def __init__(self, *args, **kwargs):
        """
        Filters the Words on the translated language.
        """
        self.fragment = kwargs.pop('fragment', None)
        sentences = self.fragment.sentence_set.all()

        super(SelectionForm, self).__init__(*args, **kwargs)
        self.fields['words'].queryset = Word.objects.filter(sentence__in=sentences)

    def clean(self):
        """
        Check for conditional requirements:
        - If is_no_target is not set, make sure Words have been selected
        """
        cleaned_data = super(SelectionForm, self).clean()

        if not cleaned_data['is_no_target']:
            if not cleaned_data['words']:
                self.add_error('is_translation', 'Please select the words composing the verb phrase.')
