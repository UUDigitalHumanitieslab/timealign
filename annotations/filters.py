from django_filters import CharFilter, FilterSet, ModelChoiceFilter, MultipleChoiceFilter, OrderingFilter

from .models import Annotation, Corpus, Tense, Label
from .utils import labels_to_choices


class AnnotationFilter(FilterSet):
    corpus = ModelChoiceFilter(label='Corpus',
                               field_name='alignment__original_fragment__document__corpus',
                               queryset=Corpus.objects.all())
    source_tense = ModelChoiceFilter(label='Tense',
                                     field_name='alignment__original_fragment__tense',
                                     queryset=Tense.objects.all())
    source_labels = MultipleChoiceFilter(choices=Label.objects.all())
    word_in_source = CharFilter(label='Word in source',
                                field_name='alignment__original_fragment__sentence__word__word',
                                lookup_expr='iexact',
                                help_text='Filters words in the source text (case-insensitive)',
                                distinct=True)
    word_in_target = CharFilter(label='Word in translation',
                                field_name='alignment__translated_fragment__sentence__word__word',
                                lookup_expr='iexact',
                                help_text='Filters words in the translated text (case-insensitive)',
                                distinct=True)
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
        fields = ['corpus', 'is_no_target', 'is_translation', 'source_tense', 'source_labels', 'word_in_source',
                  'tense', 'labels', 'word_in_target', 'annotated_by']

    def __init__(self, l1, l2, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters['is_no_target'].label = self.filters['is_no_target'].label[:-12]  # Strips HTML tag from label
        self.filters['source_tense'].queryset = Tense.objects.filter(language__iso=l1)
        self.filters['tense'].queryset = Tense.objects.filter(language__iso=l2)
        # match labels in the relevant languages, or labels that are not language specific
        l1_labels_queryset = Label.objects.filter(language__isnull=True) | Label.objects.filter(language__iso=l1)
        l2_labels_queryset = Label.objects.filter(language__isnull=True) | Label.objects.filter(language__iso=l2)
        if kwargs.get('data') and kwargs.get('data').get('corpus'):
            l1_labels_queryset = l1_labels_queryset.filter(key__corpora=kwargs.get('data').get('corpus'))
            l2_labels_queryset = l2_labels_queryset.filter(key__corpora=kwargs.get('data').get('corpus'))

        self.filters['source_labels'] = MultipleChoiceFilter(label='Labels',
                                                             field_name='alignment__original_fragment__labels',
                                                             choices=labels_to_choices(l1_labels_queryset))
        self.filters['labels'] = MultipleChoiceFilter(label='Labels',
                                                      field_name='labels',
                                                      choices=labels_to_choices(l2_labels_queryset))
