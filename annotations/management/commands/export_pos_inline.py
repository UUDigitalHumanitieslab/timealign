# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Max

from annotations.models import Corpus, Language, Annotation, Fragment, Word
from selections.models import PreProcessFragment
from .utils import open_csv, open_xlsx, pad_list
from core.utils import CSV, XLSX


class Command(BaseCommand):
    help = 'Exports existing (correct) Annotations with POS tags for the given languages'

    def add_arguments(self, parser):
        parser.add_argument('corpus', type=str)
        parser.add_argument('source_language', type=str)
        parser.add_argument('languages', nargs='+', type=str)
        parser.add_argument('--include_non_targets', action='store_true', dest='include_non_targets', default=False)
        parser.add_argument('--xlsx', action='store_true', dest='format_xlsx', default=False)
        parser.add_argument('--doc', nargs='+', dest='document')
        parser.add_argument('--formal_structure', dest='formal_structure')

    def handle(self, *args, **options):
        # Retrieve the Corpus from the database
        try:
            corpus = Corpus.objects.get(title=options['corpus'])
        except Corpus.DoesNotExist:
            raise CommandError('Corpus with title {} does not exist'.format(options['corpus']))

        try:
            source_language = Language.objects.get(iso=options['source_language'])
        except Language.DoesNotExist:
            raise CommandError('Language with iso {} does not exist'.format(options['source_language']))

        for language in options['languages']:
            if not corpus.languages.filter(iso=language):
                raise CommandError('Language {} does not exist'.format(language))

        languages = Language.objects.filter(iso__in=options['languages']).order_by('iso')
        documents = options['document']
        include_non_targets = options['include_non_targets']
        formal_structure = options['formal_structure']
        format_ = XLSX if options['format_xlsx'] else CSV

        header, results = generate_results(source_language, languages, corpus, documents,
                                           formal_structure, include_non_targets)

        if format_ == XLSX:
            opener = open_xlsx
        else:
            opener = open_csv

        filename = 'pos_{lang}.{ext}'.format(lang=source_language.iso, ext=format_)
        with opener(filename) as writer:
            writer.writerow(header, is_header=True)
            writer.writerows(results)


def generate_results(source_language, languages, corpus, documents, formal_structure, include_non_targets):
    # Retrieve the annotations
    annotations = Annotation.objects. \
        filter(alignment__translated_fragment__document__corpus=corpus). \
        filter(alignment__translated_fragment__language__in=languages)
    if not include_non_targets:
        annotations = annotations.filter(is_no_target=False, is_translation=True)
    if documents is not None:
        annotations = annotations.filter(alignment__translated_fragment__document__title__in=documents)

    # TODO: would be nice to group by language, so the max_words value can be set per language
    max_words = annotations.annotate(selected_words=Count('words')). \
        aggregate(Max('selected_words'))['selected_words__max']
    header = generate_header(languages, max_words)

    # Retrieve Fragments, exclude PreProcessFragments
    fragments = Fragment.objects.filter(language=source_language, document__corpus=corpus)
    pp_fragments = PreProcessFragment.objects.filter(language=source_language, document__corpus=corpus)
    fragments = fragments.exclude(pk__in=pp_fragments)

    if documents is not None:
        fragments = fragments.filter(document__title__in=documents)

    if formal_structure is not None:
        if formal_structure == 'narration':
            fragments = fragments.filter(formal_structure=Fragment.FS_NARRATION)
        if formal_structure == 'dialogue':
            fragments = fragments.filter(formal_structure=Fragment.FS_DIALOGUE)
    rows = []

    for fragment in fragments:
        row = []

        words = Word.objects.filter(sentence__fragment=fragment, is_target=True)
        row.append(str(fragment.pk))
        row.append(fragment.document.title)
        row.append(fragment.first_sentence().xml_id)
        row.append(fragment.full(CSV))
        row.append(fragment.label())
        row.append(' '.join([word.word for word in words]))

        # Retrieve the Annotations for this Fragment...
        f_annotations = annotations.filter(alignment__original_fragment=fragment). \
            select_related('alignment__translated_fragment', 'tense'). \
            prefetch_related('words'). \
            order_by('alignment__translated_fragment__language__iso')

        for language in languages:
            has_annotation = False
            for annotation in f_annotations:
                if annotation.alignment.translated_fragment.language == language:
                    w = [word.word for word in annotation.words.all()]
                    row.append(annotation.alignment.translated_fragment.full(CSV, annotation=annotation))
                    row.append(annotation.label())
                    row.extend(pad_list(w, max_words))
                    has_annotation = True
                    break
            if not has_annotation:
                row.extend([''] * (max_words + 2))

        rows.append(row)

    return header, rows


def generate_header(languages, max_words):
    header = ['pk', 'document', 'xml-id', 'sentence', 'tense', 'source words']

    for language in languages:
        language_details = ['sentence', 'tense']
        language_details.extend(['w' + str(i + 1) for i in range(max_words)])
        header.extend(map(lambda x: '{}-{}'.format(language.iso, x), language_details))

    return header
