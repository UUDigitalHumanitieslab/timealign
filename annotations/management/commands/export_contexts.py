# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError

import pickle

from annotations.models import Corpus, Annotation, Fragment, Word
from .utils import UnicodeWriter, pad_list


class Command(BaseCommand):
    help = 'Exports all contexts for a Corpus'

    def add_arguments(self, parser):
        parser.add_argument('corpus', type=str)

    def handle(self, *args, **options):
        # Retrieve the Corpus from the database
        try:
            corpus = Corpus.objects.get(title=options['corpus'])
        except Corpus.DoesNotExist:
            raise CommandError('Corpus with title {} does not exist'.format(options['corpus']))

        with open('contexts.csv', 'wb') as csvfile:
            csvfile.write(u'\uFEFF'.encode('utf-8'))  # the UTF-8 BOM to hint Excel we are using that...
            csv_writer = UnicodeWriter(csvfile, delimiter=';')

            header = ['id'] \
                     + corpus.languages.count() \
                       * ['language', 'tense',
                          'w1', 'w2', 'w3', 'w4', 'w5',
                          'pos1', 'pos2', 'pos3', 'pos4', 'pos5',
                          'full fragment']
            csv_writer.writerow(header)

            pre = 'plots/{}_'.format(corpus.pk)
            fragment_ids = pickle.load(open(pre + 'fragments.p', 'rb'))

            for fragment_id in fragment_ids:
                fragment = Fragment.objects.get(pk=fragment_id)
                row = [str(fragment.pk)]

                words = Word.objects.filter(sentence__fragment=fragment, is_target=True)
                w = [word.word for word in words]
                pos = [word.pos for word in words]
                f = fragment.full()
                row += [fragment.language.iso, 'pp'] + pad_list(w, 5) + pad_list(pos, 5) + [f]

                annotations = Annotation.objects \
                    .filter(alignment__original_fragment=fragment) \
                    .order_by('alignment__original_fragment__language__iso')
                for annotation in annotations:
                    fragment = annotation.alignment.translated_fragment
                    w = [word.word for word in annotation.words.all()]
                    pos = [word.pos for word in annotation.words.all()]
                    f = fragment.full()
                    row += [fragment.language.iso, annotation.tense.title] + pad_list(w, 5) + pad_list(pos, 5) + [f]

                csv_writer.writerow(row)
