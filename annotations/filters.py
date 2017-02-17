from django_filters import FilterSet, CharFilter

from .models import Annotation


class AnnotationFilter(FilterSet):
    word_in_source = CharFilter(label='Word in source',
                                name='alignment__original_fragment__sentence__word__word',
                                lookup_expr='iexact',
                                help_text='Use this to filter for words in the source text (case-insensitive)')

    class Meta:
        model = Annotation
        fields = ['is_no_target', 'is_translation', 'tense']
