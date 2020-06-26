from django import forms


class ScenarioForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ScenarioForm, self).__init__(*args, **kwargs)

        # If the Corpus has been set, filter the Documents based on the Corpus
        document_field = self.fields['documents']
        if self.instance.corpus_id:
            document_field.queryset = document_field.queryset.filter(corpus=self.instance.corpus)

        # Select the Corpus to prevent queries being fired on the __str__ method
        document_field.queryset = document_field.queryset.select_related('corpus')


class ScenarioLanguageForm(forms.ModelForm):
    class Meta:
        widgets = {
            'include_keys': forms.CheckboxSelectMultiple,
            'include_labels': forms.CheckboxSelectMultiple
        }

    def __init__(self, *args, **kwargs):
        super(ScenarioLanguageForm, self).__init__(*args, **kwargs)

        # If the Scenario has been set, filter the Languages based on the Corpus
        if self.instance.scenario_id:
            self.fields['language'].queryset = self.instance.scenario.corpus.languages.all()

        # If the Language has been set, filter the Tenses based on the Language
        if self.instance.language_id:
            self.fields['tenses'].queryset = self.fields['tenses'].queryset.filter(language=self.instance.language)

            qs = self.fields['include_labels'].queryset
            qs = qs.filter(language=self.instance.language) | qs.filter(language=None)
            qs = qs.filter(key__corpora=self.instance.scenario.corpus)
            labels = []
            for label in qs:
                labels.append((label.pk, '{}:{}'.format(label.key.title, label.title)))
            self.fields['include_labels'].choices = labels

            self.fields['include_keys'].queryset = self.fields['include_keys'].queryset.filter(corpora=self.instance.scenario.corpus)

    def clean(self):
        """
        Check that either as_from or as_to has been set for a ScenarioLanguage.
        """
        cleaned_data = super(ScenarioLanguageForm, self).clean()

        if not (cleaned_data['as_from'] or cleaned_data['as_to']):
            self.add_error('language', 'For each language in the Scenario, "as from" or "as to" has to be selected')

        if not (cleaned_data['use_tenses'] or cleaned_data['use_labels']):
            self.add_error('language', 'Please select at least one of "use tenses" and "use labels"')
