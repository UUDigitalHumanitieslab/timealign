from django import forms

from annotations.utils import get_tenses

from .models import Selection, Word


class SelectionForm(forms.ModelForm):
    class Meta:
        model = Selection
        fields = [
            'is_no_target', 'tense', 'comments', 'words',
        ]
        widgets = {
            'tense': forms.Select(),
            'comments': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        """
        Filters the Words on the translated language.
        """
        self.fragment = kwargs.pop('fragment', None)
        self.user = kwargs.pop('user', None)
        sentences = self.fragment.sentence_set.all()
        tenses = get_tenses(self.fragment.language)

        super(SelectionForm, self).__init__(*args, **kwargs)
        self.fields['words'].queryset = Word.objects.filter(sentence__in=sentences)
        self.fields['tense'].widget.choices = tuple(zip(tenses, tenses))

    def clean(self):
        """
        Check for conditional requirements:
        - If is_no_target is not set, make sure Words have been selected
        """
        cleaned_data = super(SelectionForm, self).clean()

        if not cleaned_data['is_no_target']:
            if not cleaned_data['words']:
                self.add_error('is_no_target', 'Please select the words composing the verb phrase.')
