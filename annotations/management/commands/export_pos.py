# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError

from annotations.models import Corpus
from annotations.exports import export_pos_file


class Command(BaseCommand):
    help = 'Exports existing (correct) Annotations with POS tags for the given languages'

    def add_arguments(self, parser):
        parser.add_argument('corpus', type=str)
        parser.add_argument('languages', nargs='+', type=str)
        parser.add_argument('--add_sources', action='store_true', dest='add_sources', default=False)
        parser.add_argument('--add_lemmata', action='store_true', dest='add_lemmata', default=False)
        parser.add_argument('--include_non_targets', action='store_true', dest='include_non_targets', default=False)
        parser.add_argument('--xlsx', action='store_true', dest='format_xlsx', default=False)
        parser.add_argument('--doc', dest='document')

    def handle(self, *args, **options):
        # Retrieve the Corpus from the database
        try:
            corpus = Corpus.objects.get(title=options['corpus'])
        except Corpus.DoesNotExist:
            raise CommandError('Corpus with title {} does not exist'.format(options['corpus']))

        format_ = 'xlsx' if options['format_xlsx'] else 'csv'
        for language in options['languages']:
            if not corpus.languages.filter(iso=language):
                raise CommandError('Language {} does not exist'.format(language))

            filename = 'pos_{lang}.{ext}'.format(lang=language, ext=format_)
            export_pos_file(filename, format_, corpus, language,
                            document=options['document'],
                            add_sources=options['add_sources'],
                            include_non_targets=options['include_non_targets'],
                            add_lemmata=options['add_lemmata'])
