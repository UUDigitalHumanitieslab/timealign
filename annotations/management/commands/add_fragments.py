import csv

from lxml import etree

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from annotations.models import Language, Tense, Corpus, Document, Fragment, Sentence, Word, Alignment


class Command(BaseCommand):
    help = 'Reads in the Fragments for a Document and creates Alignments.'

    def add_arguments(self, parser):
        parser.add_argument('corpus', type=str)
        parser.add_argument('filenames', type=str, nargs='+')

        parser.add_argument('--use_other_label', action='store_true', dest='use_other_label', default=False)
        parser.add_argument('--delete', action='store_true', dest='delete', default=False,
                            help='Delete existing Fragments (and contents) for this Corpus')

    def handle(self, *args, **options):
        # Retrieve the Corpus from the database
        try:
            corpus = Corpus.objects.get(title=options['corpus'])
        except Corpus.DoesNotExist:
            raise CommandError('Corpus with title {} does not exist'.format(options['corpus']))

        if len(options['filenames']) == 0:
            raise CommandError('No documents specified')

        if options['delete']:
            Fragment.objects.filter(document__corpus=corpus).delete()

        for filename in options['filenames']:
            with open(filename, 'rb') as f:
                csv_reader = csv.reader(f, delimiter=';')
                for n, row in enumerate(csv_reader):
                    # Retrieve the languages from the first row of the output
                    if n == 0:
                        language_from = Language.objects.get(iso=row[1])
                        languages_to = dict()
                        for i in range(6, len(row), 2):
                            languages_to[i] = Language.objects.get(iso=row[i])
                        continue

                    # For every other line, create a Fragment and its Alignments
                    with transaction.atomic():
                        doc, _ = Document.objects.get_or_create(corpus=corpus, title=row[0])

                        from_fragment = Fragment.objects.create(language=language_from,
                                                                document=doc)

                        # Add other_label or Tense to Fragment
                        if options['use_other_label']:
                            from_fragment.other_label = row[1]
                        else:
                            from_fragment.tense = Tense.objects.get(language=language_from, title=row[1])
                        from_fragment.save()

                        # Add Sentences to Fragment
                        add_sentences(from_fragment, row[4], row[3].split(' '))

                        # Create the Fragments in other Languages and add the Alignment object
                        for m, language_to in languages_to.items():
                            if row[m]:
                                to_fragment = Fragment.objects.create(language=language_to,
                                                                      document=doc)
                                add_sentences(to_fragment, row[m])

                                Alignment.objects.create(original_fragment=from_fragment,
                                                         translated_fragment=to_fragment,
                                                         type=row[m - 1])

                    print 'Line {} processed'.format(n)


def add_sentences(fragment, xml, target_ids=[]):
    for s in etree.fromstring(xml).xpath('.//s'):
        sentence = Sentence.objects.create(xml_id=s.get('id'), fragment=fragment)
        for w in s.xpath('.//w'):
            xml_id = w.get('id')
            pos = w.get('tree') or w.get('pos') or w.get('hun') or '?'
            is_target = xml_id in target_ids
            Word.objects.create(xml_id=xml_id, word=w.text,
                                pos=pos, lemma=w.get('lem', '?'),
                                is_target=is_target, sentence=sentence)
