from django_filters import FilterSet, CharFilter, OrderingFilter

from .models import Annotation


class AnnotationFilter(FilterSet):
    word_in_source = CharFilter(label='Word in source',
                                name='alignment__original_fragment__sentence__word__word',
                                lookup_expr='iexact',
                                help_text='Use this to filter for words in the source text (case-insensitive)')

    o = OrderingFilter(
        fields=(
            ('annotated_at', 'annotated_at'),
            ('last_modified_at', 'last_modified_at'),
            ('alignment__original_fragment__document', 'document'),
        ),
    )

    class Meta:
        model = Annotation
        fields = ['is_no_target', 'is_translation', 'tense', 'word_in_source', 'annotated_by']
