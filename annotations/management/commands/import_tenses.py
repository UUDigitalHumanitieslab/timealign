# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError

import codecs
import csv

from annotations.models import Language, Tense, Annotation


class Command(BaseCommand):
    help = 'Imports tenses for Annotations'

    def add_arguments(self, parser):
        parser.add_argument('language', type=str)
        parser.add_argument('filenames', nargs='+', type=str)
        parser.add_argument('--use_other_label', action='store_true', dest='use_other_label', default=False)

    def handle(self, *args, **options):
        try:
            language = Language.objects.get(iso=options['language'])
        except Language.DoestNotExist:
            raise CommandError('Language {} does not exist'.format(options['language']))

        for filename in options['filenames']:
            with codecs.open(filename, 'rb', 'utf-8') as csvfile:
                csv_reader = unicode_csv_reader(csvfile, delimiter='\t')
                next(csv_reader)  # skip header

                for row in csv_reader:
                    if row:
                        update_annotation(language, row, options['use_other_label'])


def update_annotation(language, row, use_other_label=False):
    try:
        # Retrieve Annotation
        annotation = Annotation.objects.get(pk=row[0])

        # Add Tense or other_label
        if use_other_label:
            annotation.other_label = row[1]
        else:
            annotation.tense = Tense.objects.get(title__iexact=row[1], language=language)

        # Add comments
        if len(row) == 3:
            annotation.comments = row[2]

        # Save Annotation
        annotation.save()
    except Annotation.DoesNotExist:
        raise CommandError(u'Annotation with pk {} not found'.format(row[0]))
    except Tense.DoesNotExist:
        raise CommandError(u'Tense for title {} not found'.format(row[1]))


def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                            dialect=dialect, **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
        yield [unicode(cell, 'utf-8') for cell in row]


def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')
