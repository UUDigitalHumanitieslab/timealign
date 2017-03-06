import csv

from lxml import etree

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from annotations.models import Language, Corpus, Document, Sentence, Word
from selections.models import PreProcessFragment


class Command(BaseCommand):
    help = 'Reads in the Fragments for a Document and creates Alignments.'

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
            raise CommandError('Corpus with title {} does not exist'.format[options['corpus']])

        if len(options['filenames']) == 0:
            raise CommandError('No documents specified')

        if options['delete']:
            PreProcessFragment.objects.filter(document__corpus=corpus).delete()

        for filename in options['filenames']:
            with open(filename, 'rb') as f:
                csv_reader = csv.reader(f, delimiter=';')
                for n, row in enumerate(csv_reader):
                    # Skip header row
                    if n == 0:
                        continue

                    with transaction.atomic():
                        language = Language.objects.get(iso=row[1])
                        doc, _ = Document.objects.get_or_create(corpus=corpus, title=row[0])

                        from_fragment = PreProcessFragment.objects.create(language=language, document=doc)
                        add_sentences(from_fragment, row[2])

                    print 'Line {} processed'.format(n)


def add_sentences(fragment, xml):
    for s in etree.fromstring(xml).xpath('.//s'):
        sentence = Sentence.objects.create(xml_id=s.get('id'), fragment=fragment)
        for w in s.xpath('.//w'):
            xml_id = w.get('id')
            pos = w.get('tree') or w.get('pos') or '?'
            Word.objects.create(xml_id=xml_id, word=w.text,
                                pos=pos, lemma=w.get('lem', '?'),
                                sentence=sentence)
