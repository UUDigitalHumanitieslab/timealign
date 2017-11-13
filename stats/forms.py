from django import forms


class ScenarioForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ScenarioForm, self).__init__(*args, **kwargs)

        # If the Corpus has been set, filter the Documents based on the Corpus
        if self.instance.corpus_id:
            self.fields['documents'].queryset = self.fields['documents'].queryset.filter(corpus=self.instance.corpus)


class ScenarioLanguageForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ScenarioLanguageForm, self).__init__(*args, **kwargs)

        # If the Scenario has been set, filter the Languages based on the Corpus
        if self.instance.scenario_id:
            self.fields['language'].queryset = self.instance.scenario.corpus.languages.all()

        # If the Language has been set, filter the Tenses based on the Language
        if self.instance.language_id:
            self.fields['tenses'].queryset = self.fields['tenses'].queryset.filter(language=self.instance.language)

    def clean(self):
        """
        Check that either as_from or as_to has been set for a ScenarioLanguage.
        """
        cleaned_data = super(ScenarioLanguageForm, self).clean()

        if not (cleaned_data['as_from'] or cleaned_data['as_to']):
            self.add_error('language', 'For each language in the Scenario, "as from" or "as to" has to be selected')
