from django_filters import FilterSet, CharFilter

from .models import Selection


class SelectionFilter(FilterSet):
    word_in_fragment = CharFilter(label='Word in fragment',
                                  name='fragment__sentence__word__word',
                                  lookup_expr='iexact',
                                  help_text='Use this to filter for words in the text (case-insensitive)')

    class Meta:
        model = Selection
        fields = ['is_no_target']
