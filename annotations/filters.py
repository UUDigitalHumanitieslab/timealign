from django_filters import FilterSet, CharFilter, ModelChoiceFilter, OrderingFilter, MultipleChoiceFilter

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
    labels = MultipleChoiceFilter(choices=Label.objects.all())

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

    def __init__(self, l1, l2, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = kwargs['request']
        self.filters['original_tense'].queryset = Tense.objects.filter(language__iso=l1)
        self.filters['tense'].queryset = Tense.objects.filter(language__iso=l2)
        labels_queryset = Label.objects.all()
        if kwargs['data'] and kwargs['data']['corpus']:
            labels_queryset = labels_queryset.filter(key__corpora=kwargs['data']['corpus'])

        self.filters['labels'] = MultipleChoiceFilter(label='Labels',
                                                      field_name='labels',
                                                      choices=[(label.pk, '{}:{}'.format(label.key.title, label.title))
                                                               for label in labels_queryset])
