# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError

from annotations.models import Corpus, Document, Language
from annotations.exports import export_annotations_inline
from core.utils import CSV, XLSX


class Command(BaseCommand):
    help = 'Exports Annotations for the given Corpus and Languages (one file for all languages)'

    def add_arguments(self, parser):
        parser.add_argument('corpus', type=str)
        parser.add_argument('source_language', type=str)
        parser.add_argument('languages', nargs='+', type=str)
        parser.add_argument('--document')
        parser.add_argument('--formal_structure', dest='formal_structure')
        parser.add_argument('--include_non_targets', action='store_true', dest='include_non_targets', default=False)
        parser.add_argument('--xlsx', action='store_true', dest='format_xlsx', default=False)

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
                raise CommandError('Language {} does not exist for Corpus {}'.format(language, corpus))
        languages = Language.objects.filter(iso__in=options['languages']).order_by('iso')

        document = None
        if options['document']:
            try:
                document = Document.objects.get(corpus=corpus, title=options['document'])
            except Document.DoesNotExist:
                raise CommandError('Document with title {} does not exist'.format(options['document']))

        format_ = XLSX if options['format_xlsx'] else CSV

        filename = '{corpus}_{iso}.{ext}'.format(corpus=corpus.title, iso=source_language.iso, ext=format_)
        export_annotations_inline(filename, format_, corpus, source_language, languages,
                                  document=document,
                                  include_non_targets=options['include_non_targets'],
                                  formal_structure=options['formal_structure'])
