from django import forms

from annotations.utils import get_tenses

from .models import Selection, Word


class SelectionForm(forms.ModelForm):
    already_complete = forms.BooleanField(label='Nothing more to select', required=False)

    class Meta:
        model = Selection
        fields = [
            'is_no_target', 'already_complete', 'tense', 'comments', 'words',
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
        selected_words = self.fragment.selected_words(self.user)

        super(SelectionForm, self).__init__(*args, **kwargs)
        self.fields['words'].queryset = Word.objects.filter(sentence__in=sentences)
        self.fields['tense'].widget.choices = tuple(zip(tenses, tenses))

        if not selected_words:
            del self.fields['already_complete']

    def clean(self):
        """
        Check for conditional requirements:
        - If is_no_target is not set, make sure Words have been selected
        """
        cleaned_data = super(SelectionForm, self).clean()

        if not (cleaned_data.get('is_no_target', False) or cleaned_data.get('already_complete', False)):
            if not cleaned_data['words']:
                self.add_error('is_no_target', 'Please select the words composing the target phrase.')
