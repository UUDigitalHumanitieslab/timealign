from django import forms

from annotations.forms import AddFragmentsForm, LabelFormMixin, SegmentSelectMixin
from annotations.models import Language, Corpus, Tense, Word

from .management.commands.add_pre_fragments import process_file
from .management.commands.convert_to_fragments import convert_selections, retrieve_fragments
from .models import Selection


class SelectionForm(LabelFormMixin, SegmentSelectMixin, forms.ModelForm):
    already_complete = forms.BooleanField(
        label='All targets have already been selected in this fragment', required=False)

    class Meta:
        model = Selection
        fields = [
            'is_no_target', 'already_complete',
            'tense', 'labels',
            'comments', 'words',
            'select_segment'
        ]
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        """
        Allows selection of the target words
        """
        self.fragment = kwargs.pop('fragment', None)
        self.user = kwargs.pop('user', None)

        selected_words = self.fragment.selected_words()

        super(SelectionForm, self).__init__(*args, **kwargs)

        self.fields['tense'].queryset = Tense.objects.filter(language=self.fragment.language)
        self.fields['words'].queryset = Word.objects.filter(sentence__fragment=self.fragment)

        # Allow to select for tense if the Corpus is tense/aspect-based.
        if not self.fragment.document.corpus.tense_based:
            del self.fields['tense']

        if not selected_words:
            del self.fields['already_complete']

        # Move comments to the end of the fields by deleting and then re-adding
        comments = self.fields['comments']
        del self.fields['comments']
        self.fields['comments'] = comments

    @property
    def corpus(self):
        return self.fragment.document.corpus

    @property
    def language(self):
        return self.fragment.language

    def clean(self):
        """
        Check for conditional requirements:
        - If is_no_target is not set, make sure Words have been selected
        """
        cleaned_data = super(SelectionForm, self).clean()

        if not (cleaned_data.get('is_no_target', False) or cleaned_data.get('already_complete', False)):
            if not cleaned_data['words']:
                self.add_error('is_no_target', 'Please select the words composing the target phrase.')

        return cleaned_data


class AddPreProcessFragmentsForm(AddFragmentsForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.corpus:
            del self.fields['annotation_types']

    def save(self):
        data = self.cleaned_data
        process_file(data['fragment_file'], data['corpus'])


class ConvertSelectionsForm(forms.Form):
    language = forms.ModelChoiceField(queryset=Language.objects.all())
    corpus = forms.ModelChoiceField(queryset=Corpus.objects.all())
    alignment_file = forms.FileField(
        help_text='This should be a .csv-file, with the following columns: '
                  'document;sentence;'
                  'type [language iso] (empty);words [language iso] (empty);'
                  'ids [language iso] (empty);[language iso] (empty)'
                  ';alignment type;[language iso];alignment;[language iso]... '
                  'The first row (header) will not be imported.'
    )
    create_new = forms.BooleanField(
        label='If checked, create Fragments from PreSelections, otherwise, use existing Fragments instead.',
        required=False,
    )

    def save(self):
        data = self.cleaned_data
        fragment_cache = retrieve_fragments(data['language'], data['corpus'], create_new=data['create_new'])
        convert_selections(data['alignment_file'], fragment_cache, data['corpus'])
