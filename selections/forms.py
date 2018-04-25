from django import forms

from annotations.utils import get_tenses

from .models import Selection, Word


class SelectionForm(forms.ModelForm):
    already_complete = forms.BooleanField(label='All targets have already been selected in this fragment', required=False)

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
        Allows selection of the target words
        """
        self.fragment = kwargs.pop('fragment', None)
        self.user = kwargs.pop('user', None)

        sentences = self.fragment.sentence_set.all()
        selected_words = self.fragment.selected_words()

        super(SelectionForm, self).__init__(*args, **kwargs)
        self.fields['words'].queryset = Word.objects.filter(sentence__in=sentences)

        # Allow to select for tense is the Corpus is tense/aspect-based.
        if self.fragment.document.corpus.tense_based:
            tenses = get_tenses(self.fragment.language)
            self.fields['tense'].widget.choices = tuple(zip(tenses, tenses))
        else:
            del self.fields['tense']

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
