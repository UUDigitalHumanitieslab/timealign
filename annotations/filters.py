from django_filters import FilterSet, CharFilter, ModelChoiceFilter, OrderingFilter

from .models import Annotation, Corpus, Tense, Label


class AnnotationFilter(FilterSet):
    corpus = ModelChoiceFilter(label='Corpus',
                               field_name='alignment__original_fragment__document__corpus',
                               queryset=Corpus.objects.all())
    word_in_source = CharFilter(label='Word in source',
                                field_name='alignment__original_fragment__sentence__word__word',
                                lookup_expr='iexact',
                                help_text='Use this to filter for words in the source text (case-insensitive)')
    original_tense = ModelChoiceFilter(label='Original Tense',
                                       field_name='alignment__original_fragment__tense',
                                       queryset=Tense.objects.all())

    o = OrderingFilter(
        fields=(
            ('annotated_at', 'annotated_at'),
            ('last_modified_at', 'last_modified_at'),
            ('alignment__original_fragment__document', 'document'),
        ),
    )

    class Meta:
        model = Annotation
        fields = ['corpus', 'is_no_target', 'is_translation', 'tense', 'original_tense',
                  'labels', 'word_in_source', 'annotated_by']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = kwargs['request']
        # there might be a better way to access these parameters
        params = request.resolver_match.kwargs
        self.filters['original_tense'].queryset = Tense.objects.filter(language__iso=params['l1'])
        self.filters['tense'].queryset = Tense.objects.filter(language__iso=params['l2'])
        self.filters['labels'].queryset = Label.objects.filter(language__iso__in=[params['l1'], params['l2']])
