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
        self.user = kwargs.pop('user', None)
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
                self.add_error('is_no_target', 'Please select the words composing the verb phrase.')
            else:
                for _, prev_ids in self.fragment.selected_words(self.user).items():
                    if set(prev_ids).intersection([w.xml_id for w in cleaned_data['words']]):
                        self.add_error('is_no_target', 'This word has already been selected.')
