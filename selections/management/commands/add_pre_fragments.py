import csv

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from annotations.models import Language, Corpus, Document
from annotations.management.commands.add_fragments import add_sentences
from annotations.management.commands.constants import COLUMN_DOCUMENT, COLUMN_XML

from selections.models import PreProcessFragment


class Command(BaseCommand):
    help = 'Reads in a .csv-file and creates PreProcessFragments.'

    def add_arguments(self, parser):
        parser.add_argument('corpus', type=str)
        parser.add_argument('filenames', type=str, nargs='+')

        parser.add_argument('--delete', action='store_true', dest='delete', default=False,
                            help='Delete existing PreProcessFragments (and contents) for this Corpus')

    def handle(self, *args, **options):
        # Retrieve the Corpus from the database
        try:
            corpus = Corpus.objects.get(title=options['corpus'])
        except Corpus.DoesNotExist:
            raise CommandError('Corpus with title {} does not exist'.format(options['corpus']))

        if len(options['filenames']) == 0:
            raise CommandError('No documents specified')

        if options['delete']:
            PreProcessFragment.objects.filter(document__corpus=corpus).delete()

        for filename in options['filenames']:
            with open(filename, 'r') as f:
                csv_reader = csv.reader(f, delimiter=';')
                for n, row in enumerate(csv_reader):
                    # Retrieve language from header row
                    if n == 0:
                        language = Language.objects.get(iso=row[COLUMN_XML])
                        continue

                    with transaction.atomic():
                        doc, _ = Document.objects.get_or_create(corpus=corpus, title=row[COLUMN_DOCUMENT])

                        from_fragment = PreProcessFragment.objects.create(language=language, document=doc)
                        add_sentences(from_fragment, row[COLUMN_XML])

                    self.stdout.write(self.style.SUCCESS('Line {} processed'.format(n)))
