from django_filters import FilterSet, CharFilter, OrderingFilter

from .models import Selection


class SelectionFilter(FilterSet):
    word_in_fragment = CharFilter(label='Word in fragment',
                                  field_name='fragment__sentence__word__word',
                                  lookup_expr='iexact',
                                  help_text='Use this to filter for words in the text (case-insensitive)')

    o = OrderingFilter(
        fields=(
            ('selected_at', 'annotated_at'),
            ('last_modified_at', 'last_modified_at'),
            ('fragment__document', 'document'),
            ('fragment__sentence', 'sentence'),
        ),
    )

    class Meta:
        model = Selection
        fields = ['is_no_target', 'selected_by']
