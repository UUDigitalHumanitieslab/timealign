import csv

from lxml import etree

from django.core.management.base import BaseCommand, CommandError

from annotations.models import Document, Fragment, Sentence, Word, Alignment


class Command(BaseCommand):
    args = '<document...>'
    help = 'Reads in the Sentences for a Document.'

    def handle(self, *args, **options):
        if len(args) == 0:
            raise CommandError('No documents specified')

        # print 'Removing existing documents...'
        # Document.objects.all().delete()

        for filename in args:
            with open(filename, 'rb') as f:
                csv_reader = csv.reader(f, delimiter=';')
                for n, row in enumerate(csv_reader):
                    if n == 0:
                        language_from = row[5]
                        languages_to = dict()
                        for i in xrange(10, 30, 5):
                            if not row[i]:
                                break
                            else:
                                languages_to[i] = row[i]
                        continue

                    doc, _ = Document.objects.get_or_create(title=row[0])

                    from_fragment = Fragment.objects.create(language=language_from,
                                                            speaker_language=row[1],
                                                            document=doc)
                    self.add_sentences(from_fragment, row[4], row[3].split(' '))

                    for m, language_to in languages_to.items():
                        if row[m]:
                            to_fragment = Fragment.objects.create(language=language_to,
                                                                  speaker_language=row[1],
                                                                  document=doc)
                            self.add_sentences(to_fragment, row[m - 1])

                            Alignment.objects.create(original_fragment=from_fragment,
                                                     translated_fragment=to_fragment,
                                                     type=row[m - 2])

                    print 'Line {} processed'.format(n)

    @staticmethod
    def add_sentences(fragment, xml, target_ids=[]):
        for s in etree.fromstring(xml).xpath('.//s'):
            sentence = Sentence.objects.create(xml_id=s.get('id'), fragment=fragment)
            for w in s.xpath('.//w'):
                xml_id = w.get('id')
                pos = w.get('tree') or w.get('pos') or '?'
                is_target = xml_id in target_ids
                Word.objects.create(xml_id=xml_id, word=w.text,
                                    pos=pos, lemma=w.get('lem'),
                                    is_target=is_target, sentence=sentence)
