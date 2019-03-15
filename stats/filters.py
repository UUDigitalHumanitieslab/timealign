from django import forms

from django_filters import FilterSet, BooleanFilter, CharFilter

from .models import Scenario


class ScenarioFilter(FilterSet):
    title = CharFilter(lookup_expr='icontains')
    is_test = BooleanFilter(name='is_test',
                            label='Show test scenarios',
                            widget=forms.CheckboxInput,
                            method='filter_test')
    current_user_is_owner = BooleanFilter(name='owner',
                                          label='Only show my scenarios',
                                          widget=forms.CheckboxInput,
                                          method='filter_owned')

    def filter_test(self, queryset, name, value):
        return queryset if value else queryset.filter(**{name: False})

    def filter_owned(self, queryset, name, value):
        return queryset.filter(**{name: self.request.user}) if value else queryset

    class Meta:
        model = Scenario
        fields = ['corpus', 'scenariolanguage__language', 'title', 'is_test', 'current_user_is_owner']

    def __init__(self, *args, **kwargs):
        super(ScenarioFilter, self).__init__(*args, **kwargs)
        self.filters['scenariolanguage__language'].label = 'Language'