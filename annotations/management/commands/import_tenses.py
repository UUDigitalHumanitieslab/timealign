# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError

import codecs
import csv

from annotations.models import Annotation


class Command(BaseCommand):
    help = 'Imports tenses for Annotations'

    def add_arguments(self, parser):
        parser.add_argument('filenames', nargs='+', type=str)

    def handle(self, *args, **options):
        for filename in options['filenames']:
            with codecs.open(filename, 'rb', 'utf-8') as csvfile:
                csv_reader = unicode_csv_reader(csvfile, delimiter='\t')
                next(csv_reader)  # skip header

                for row in csv_reader:
                    try:
                        annotation = Annotation.objects.get(pk=row[0])
                        annotation.tense = row[1]
                        annotation.save()
                    except Annotation.DoesNotExist:
                        raise CommandError('Annotation with pk {} not found'.format(row[0]))


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