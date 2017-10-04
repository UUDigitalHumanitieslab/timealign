from django import forms


class ScenarioLanguageForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ScenarioLanguageForm, self).__init__(*args, **kwargs)

        # If the Language has been set, filter the Tenses based on the Language
        if self.instance.language_id:
            self.fields['tenses'].queryset = self.fields['tenses'].queryset.filter(language=self.instance.language)
