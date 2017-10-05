from django import forms


class ScenarioLanguageForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ScenarioLanguageForm, self).__init__(*args, **kwargs)

        # If the Scenario has been set, filter the Languages based on the Corpus
        if self.instance.scenario_id:
            self.fields['language'].queryset = self.instance.scenario.corpus.languages.all()

        # If the Language has been set, filter the Tenses based on the Language
        if self.instance.language_id:
            self.fields['tenses'].queryset = self.fields['tenses'].queryset.filter(language=self.instance.language)
