import csv

from lxml import etree

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from .constants import COLUMN_DOCUMENT, COLUMN_IDS, COLUMN_XML
from .add_fragments import retrieve_languages, create_to_fragments
from annotations.models import Corpus, Document, Sentence


class Command(BaseCommand):
    help = 'Appends new Fragments (and creates Alignments) to existing Fragments.'

    def add_arguments(self, parser):
        parser.add_argument('corpus', type=str)
        parser.add_argument('filenames', type=str, nargs='+')

    def handle(self, *args, **options):
        # Retrieve the Corpus from the database
        try:
            corpus = Corpus.objects.get(title=options['corpus'])
        except Corpus.DoesNotExist:
            raise CommandError('Corpus with title {} does not exist'.format(options['corpus']))

        if len(options['filenames']) == 0:
            raise CommandError('No documents specified')

        for filename in options['filenames']:
            with open(filename, 'rb') as f:
                csv_reader = csv.reader(f, delimiter=';')
                for n, row in enumerate(csv_reader):
                    # Retrieve the languages from the first row of the output
                    if n == 0:
                        language_from, languages_to = retrieve_languages(row)
                        continue

                    with transaction.atomic():
                        doc = Document.objects.get(corpus=corpus, title=row[COLUMN_DOCUMENT])
                        xml_id = get_first_sentence_id(row[COLUMN_XML])

                        # Retrieve the matching sentence
                        sentences = Sentence.objects.filter(xml_id=xml_id,
                                                            fragment__language=language_from,
                                                            fragment__document=doc)

                        if not sentences:
                            self.stdout.write(self.style.WARNING('No match found for {}'.format(xml_id)))
                            continue

                        sentence = None
                        if sentences.count() >= 1:
                            # Find the matching sentence using the target id's
                            for s in sentences:
                                if [w.xml_id for w in s.word_set.filter(is_target=True)] == row[COLUMN_IDS].split(' '):
                                    sentence = s

                            if sentence is None:
                                self.stdout.write(self.style.WARNING('No match found for {}'.format(xml_id)))
                                continue
                        else:
                            sentence = sentences.first()

                        # Create the Fragment and Alignment
                        create_to_fragments(doc, sentence.fragment, languages_to, row)

                    self.stdout.write(self.style.SUCCESS('Line {} processed'.format(n)))


def get_first_sentence_id(xml):
    for s in etree.fromstring(xml).xpath('.//s'):
        return s.get('id')
