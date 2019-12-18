from django import forms

from annotations.utils import get_tenses

from .models import Selection, Word, Label


class LabelField(forms.ModelChoiceField):
    """A text field for labels with auto completion (provided by select2 in JS).
    Tied to a specific LabelCategory"""

    def __init__(self, category, *args, **kwargs):
        self._category = category
        kwargs['queryset'] = category.labels.all()
        super().__init__(*args, **kwargs)
        self.widget.attrs['class'] = 'labels-field'

    # MultipleChoiceField only allows entering predefined choices
    # however, we want users to be able to introduce new labels,
    # which is why it's necessary to override the default clean() method
    def clean(self, value):
        if value.isdigit():
            # it's a pk of an existing label
            return Label.objects.get(pk=int(value))
        label, created = Label.objects.get_or_create(title=value, category=self._category)
        if created:
            label.save()
        return label


class SelectionForm(forms.ModelForm):
    already_complete = forms.BooleanField(label='All targets have already been selected in this fragment', required=False)
    # a hidden field used to remember the user's prefered selection tool
    select_segment = forms.BooleanField(widget=forms.HiddenInput(),
                                        required=False)

    class Meta:
        model = Selection
        fields = [
            'is_no_target', 'already_complete', 'tense', 'labels', 'comments', 'words',
            'select_segment'
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

        selected_words = self.fragment.selected_words()
        select_segment = kwargs.pop('select_segment', False)

        super(SelectionForm, self).__init__(*args, **kwargs)
        self.fields['words'].queryset = Word.objects.filter(sentence__fragment=self.fragment)
        self.fields['select_segment'].initial = select_segment

        # Allow to select for tense if the Corpus is tense/aspect-based.
        if self.fragment.document.corpus.tense_based:
            tenses = get_tenses(self.fragment.language)
            self.fields['tense'].widget.choices = tuple(zip(tenses, tenses))
        else:
            del self.fields['tense']
            # add a label field for each label category
            for cat in self.corpus.label_categories.all():
                existing_label = self.instance.labels.filter(category=cat).first() if self.instance.id else None
                field = LabelField(category=cat, initial=existing_label)
                self.fields[cat.symbol()] = field

        # hide the original field for labels.
        # we still need this field defined in AnnotationForm.fields, otherwise
        # the value set in AnnotationForm.clean() will not be used when submitting the form.
        del self.fields['labels']

        if not selected_words:
            del self.fields['already_complete']

        # Comments should be the last form field
        self.fields.move_to_end('comments')

    @property
    def corpus(self):
        return self.fragment.document.corpus

    def clean(self):
        """
        Check for conditional requirements:
        - If is_no_target is not set, make sure Words have been selected
        """
        cleaned_data = super(SelectionForm, self).clean()
        # construct a value for Annotation.labels based on the individual label fields
        fields = [cat.symbol() for cat in self.corpus.label_categories.all()]
        cleaned_data['labels'] = [cleaned_data[field] for field in fields]

        if not (cleaned_data.get('is_no_target', False) or cleaned_data.get('already_complete', False)):
            if not cleaned_data['words']:
                self.add_error('is_no_target', 'Please select the words composing the target phrase.')
