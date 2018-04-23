# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError

import codecs

from annotations.models import Language, Tense, Annotation
from core.utils import unicode_csv_reader


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
        print u'Annotation with pk {} not found'.format(row[0])
    except Tense.DoesNotExist:
        raise CommandError(u'Tense for title {} not found'.format(row[1]))
