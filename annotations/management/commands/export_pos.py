# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError

import codecs
import csv
import cStringIO

from annotations.models import Corpus, Annotation, Fragment, Word


class Command(BaseCommand):
    help = 'Exports existing (correct) Annotations with POS tags for the given languages'

    def add_arguments(self, parser):
        parser.add_argument('corpus', type=str)
        parser.add_argument('languages', nargs='+', type=str)
        parser.add_argument('--add_sources', action='store_true', dest='add_sources', default=False)

    def handle(self, *args, **options):
        # Retrieve the Corpus from the database
        try:
            corpus = Corpus.objects.get(title=options['corpus'])
        except Corpus.DoesNotExist:
            raise CommandError('Corpus with title {} does not exist'.format[options['corpus']])

        for language in options['languages']:
            if not corpus.languages.filter(iso=language):
                raise CommandError('Language {} does not exist'.format(language))

            with open('pos_' + language + '.csv', 'wb') as csvfile:
                csvfile.write(u'\uFEFF'.encode('utf-8'))  # the UTF-8 BOM to hint Excel we are using that...
                csv_writer = UnicodeWriter(csvfile, delimiter=';')

                header = ['id', 'tense', 'source/target'
                          'w1', 'w2', 'w3', 'w4', 'w5',
                          'pos1', 'pos2', 'pos3', 'pos4', 'pos5',
                          'full fragment']
                csv_writer.writerow(header)

                annotations = Annotation.objects. \
                    filter(is_no_target=False, is_translation=True,
                           alignment__translated_fragment__language=language,
                           alignment__translated_fragment__document__corpus=corpus)
                for annotation in annotations:
                    words = annotation.words.all()
                    w = [word.word for word in words]
                    pos = [word.pos for word in words]
                    f = annotation.alignment.translated_fragment.full()
                    csv_writer.writerow([str(annotation.pk), annotation.tense, 'target'] + pad_list(w, 5) + pad_list(pos, 5) + [f])

                if options['add_sources']:
                    fragments = Fragment.objects.filter(language=language)
                    for fragment in fragments:
                        words = Word.objects.filter(sentence__fragment=fragment, is_target=True)
                        if words:
                            w = [word.word for word in words]
                            pos = [word.pos for word in words]
                            f = fragment.full()
                            csv_writer.writerow([str(fragment.pk), 'pp', 'source'] + pad_list(w, 5) + pad_list(pos, 5) + [f])


def pad_list(l, pad_length):
    """
    Pads a list with empty items
    Copied from http://stackoverflow.com/a/3438818/3710392
    :param l: the original list
    :param pad_length: the length of the list
    :return: the resulting, padded list
    """
    return l + [''] * (pad_length - len(l))


class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    Copied from https://docs.python.org/2/library/csv.html#examples
    """

    def __init__(self, f, dialect=csv.excel, encoding='utf-8', **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode('utf-8') for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode('utf-8')
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
