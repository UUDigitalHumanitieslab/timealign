# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError

import csv

from annotations.models import Annotation, Fragment


class Command(BaseCommand):
    help = 'Exports existing (correct) Annotations with POS tags for the given languages'

    def add_arguments(self, parser):
        parser.add_argument('corpus', type=str)
        parser.add_argument('languages', nargs='+', type=str)

    def handle(self, *args, **options):
        for language in options['languages']:
            if language not in [l[0] for l in Fragment.LANGUAGES]:
                raise CommandError('Language {} does not exist'.format(language))

            with open('pos_' + language + '.csv', 'wb') as csvfile:
                csvfile.write(u'\uFEFF'.encode('utf-8'))  # the UTF-8 BOM to hint Excel we are using that...
                csv_writer = csv.writer(csvfile, delimiter=';')
                csv_writer.writerow(['id', 'cat?',
                                     'w1', 'w2', 'w3', 'w4', 'w5',
                                     'pos1', 'pos2', 'pos3', 'pos4', 'pos5',
                                     'full fragment'])

                annotations = Annotation.objects. \
                    filter(is_no_target=False, is_translation=True,
                           alignment__translated_fragment__language=language,
                           alignment__translated_fragment__document__corpus__title=options['corpus'])
                for annotation in annotations:
                    words = annotation.words.all()
                    w = [word.word.encode('utf8') for word in words]
                    pos = [word.pos for word in words]
                    f = annotation.alignment.translated_fragment.full().encode('utf8')
                    csv_writer.writerow([annotation.pk, ''] + pad_list(w, 5) + pad_list(pos, 5) + [f])


def pad_list(l, pad_length):
    """
    Pads a list with empty items
    Copied from http://stackoverflow.com/a/3438818/3710392
    :param l: the original list
    :param pad_length: the length of the list
    :return: the resulting, padded list
    """
    return l + [''] * (pad_length - len(l))
