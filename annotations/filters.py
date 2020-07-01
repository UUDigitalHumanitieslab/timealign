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
    original_labels = MultipleChoiceFilter(choices=Label.objects.all())

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
                  'labels', 'original_labels', 'word_in_source', 'annotated_by']

    def _labels_to_choices(self, queryset):
        return [(label.pk, '{}:{}'.format(label.key.title, label.title)) for label in queryset]

    def __init__(self, l1, l2, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = kwargs['request']
        self.filters['original_tense'].queryset = Tense.objects.filter(language__iso=l1)
        self.filters['tense'].queryset = Tense.objects.filter(language__iso=l2)
        # match labels in the relevant languages, or labels that are not language specific
        l1_labels_queryset = Label.objects.filter(language__isnull=True) | Label.objects.filter(language__iso=l1)
        l2_labels_queryset = Label.objects.filter(language__isnull=True) | Label.objects.filter(language__iso=l2)
        if kwargs['data'] and kwargs['data']['corpus']:
            l1_labels_queryset = l1_labels_queryset.filter(key__corpora=kwargs['data']['corpus'])
            l2_labels_queryset = l2_labels_queryset.filter(key__corpora=kwargs['data']['corpus'])

        self.filters['original_labels'] = MultipleChoiceFilter(label='Original Labels',
                                                               field_name='alignment__original_fragment__labels',
                                                               choices=self._labels_to_choices(l1_labels_queryset))
        self.filters['labels'] = MultipleChoiceFilter(label='Labels',
                                                      field_name='labels',
                                                      choices=self._labels_to_choices(l2_labels_queryset))
