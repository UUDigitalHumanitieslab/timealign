import csv

from lxml import etree

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from annotations.management.commands.add_fragments import add_sentences
from annotations.models import Language, Corpus, Document, Fragment, Sentence, Alignment


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
                    if n == 0:
                        language_from = Language.objects.get(iso=row[5])
                        languages_to = dict()
                        for i in xrange(10, 15, 5):
                            if not row[i]:
                                break
                            else:
                                languages_to[i] = Language.objects.get(iso=row[i])
                        continue

                    with transaction.atomic():
                        doc = Document.objects.get(corpus=corpus, title=row[0])
                        xml_id = get_first_sentence_id(row[4])

                        # Retrieve the matching sentence
                        sentences = Sentence.objects.filter(xml_id=xml_id,
                                                            fragment__language=language_from,
                                                            fragment__document=doc)

                        if not sentences:
                            print 'No match found for {}'.format(xml_id)
                            continue

                        sentence = None
                        if sentences.count() >= 1:
                            # Find the matching sentence using the target id's
                            for s in sentences:
                                if [w.xml_id for w in s.word_set.filter(is_target=True)] == row[3].split(' '):
                                    sentence = s

                            if sentence is None:
                                print 'No match found for {}'.format(xml_id)
                                continue
                        else:
                            sentence = sentences.first()

                        # Create the Fragment and Alignment
                        for m, language_to in languages_to.items():
                            if row[m]:
                                to_fragment = Fragment.objects.create(language=language_to,
                                                                      document=doc)
                                add_sentences(to_fragment, row[m - 1])

                                Alignment.objects.create(original_fragment=sentence.fragment,
                                                         translated_fragment=to_fragment,
                                                         type=row[m - 2])

                    print 'Line {} processed'.format(n)


def get_first_sentence_id(xml):
    for s in etree.fromstring(xml).xpath('.//s'):
        return s.get('id')