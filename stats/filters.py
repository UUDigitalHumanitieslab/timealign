from django import forms
from django.db.models import Case, When

from django_filters import FilterSet, BooleanFilter, CharFilter, OrderingFilter

from .models import Scenario, Fragment, Document


class ScenarioFilter(FilterSet):
    title = CharFilter(lookup_expr='icontains')
    is_test = BooleanFilter(field_name='is_test',
                            label='Hide test scenarios',
                            widget=forms.CheckboxInput,
                            method='filter_test')
    current_user_is_owner = BooleanFilter(field_name='owner',
                                          label='Only show my scenarios',
                                          widget=forms.CheckboxInput,
                                          method='filter_owned')

    def filter_test(self, queryset, name, value):
        return queryset.filter(**{name: False}) if value else queryset

    def filter_owned(self, queryset, name, value):
        return queryset.filter(**{name: self.request.user}) if value else queryset

    class Meta:
        model = Scenario
        fields = ['corpus', 'scenariolanguage__language', 'title', 'is_test', 'current_user_is_owner']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters['scenariolanguage__language'].label = 'Language'


class FragmentFilter(FilterSet):
    class Meta:
        model = Fragment
        fields = ['document', 'formal_structure', 'sentence_function']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        fragment = self.queryset.first()
        self.filters['document'].queryset = Document.objects. \
            filter(corpus=fragment.document.corpus). \
            select_related('corpus')
