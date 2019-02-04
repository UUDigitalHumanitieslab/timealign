# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError

from annotations.models import Corpus, SubCorpus, Document
from annotations.exports import export_pos_file
from core.utils import CSV, XLSX


class Command(BaseCommand):
    help = 'Exports existing (correct) Annotations with POS tags for the given languages'

    def add_arguments(self, parser):
        parser.add_argument('corpus', type=str)
        parser.add_argument('languages', nargs='+', type=str)
        parser.add_argument('--subcorpus')
        parser.add_argument('--document')
        parser.add_argument('--formal_structure')
        parser.add_argument('--add_lemmata', action='store_true', dest='add_lemmata', default=False)
        parser.add_argument('--add_indices', action='store_true', dest='add_indices', default=False)
        parser.add_argument('--include_non_targets', action='store_true', dest='include_non_targets', default=False)
        parser.add_argument('--xlsx', action='store_true', dest='format_xlsx', default=False)

    def handle(self, *args, **options):
        # Retrieve the Corpus from the database
        try:
            corpus = Corpus.objects.get(title=options['corpus'])
        except Corpus.DoesNotExist:
            raise CommandError('Corpus with title {} does not exist'.format(options['corpus']))

        subcorpus = None
        if options['subcorpus']:
            try:
                subcorpus = SubCorpus.objects.get(corpus=corpus, title=options['subcorpus'])
            except SubCorpus.DoesNotExist:
                raise CommandError('SubCorpus with title {} does not exist'.format(options['subcorpus']))

        document = None
        if options['document']:
            try:
                document = Document.objects.get(corpus=corpus, title=options['document'])
            except Document.DoesNotExist:
                raise CommandError('Document with title {} does not exist'.format(options['document']))

        format_ = XLSX if options['format_xlsx'] else CSV
        for language in options['languages']:
            if not corpus.languages.filter(iso=language):
                raise CommandError('Language {} does not exist'.format(language))

            filename = 'pos_{lang}.{ext}'.format(lang=language, ext=format_)
            export_pos_file(filename, format_, corpus, language,
                            subcorpus=subcorpus,
                            document=document,
                            include_non_targets=options['include_non_targets'],
                            add_lemmata=options['add_lemmata'],
                            add_indices=options['add_indices'],
                            formal_structure=options['formal_structure'])
