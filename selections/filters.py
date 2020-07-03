from django_filters import FilterSet, CharFilter, OrderingFilter, ModelChoiceFilter, MultipleChoiceFilter

from annotations.models import Corpus, Tense, Label
from .models import Selection


class SelectionFilter(FilterSet):
    word_in_fragment = CharFilter(label='Word in fragment',
                                  field_name='fragment__sentence__word__word',
                                  lookup_expr='iexact',
                                  help_text='Use this to filter for words in the text (case-insensitive)')
    corpus = ModelChoiceFilter(label='Corpus',
                               field_name='resulting_fragment__document__corpus',
                               queryset=Corpus.objects.all())

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
        fields = ['corpus', 'is_no_target', 'selected_by', 'tense', 'labels']

    def _labels_to_choices(self, queryset):
        return [(label['pk'], '{}:{}'.format(label['key__title'], label['title'])) for label in queryset.values('pk', 'key__title', 'title')]

    def __init__(self, language, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters['tense'].queryset = Tense.objects.filter(language__iso=language)
        # match labels in the relevant languages, or labels that are not language specific
        labels_queryset = Label.objects.filter(language__isnull=True) | Label.objects.filter(language__iso=language)
        if kwargs['data'] and kwargs['data']['corpus']:
            labels_queryset = labels_queryset.filter(key__corpora=kwargs['data']['corpus'])

        self.filters['labels'] = MultipleChoiceFilter(label='Labels',
                                                      field_name='labels',
                                                      choices=self._labels_to_choices(labels_queryset))
