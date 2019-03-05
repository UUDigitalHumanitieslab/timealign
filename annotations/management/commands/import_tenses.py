# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError

from annotations.models import Language, Tense, Annotation, Fragment


class Command(BaseCommand):
    help = 'Imports tenses for Annotations'

    def add_arguments(self, parser):
        parser.add_argument('language', type=str)
        parser.add_argument('filenames', nargs='+', type=str)
        parser.add_argument('--use_other_label', action='store_true', dest='use_other_label', default=False)
        parser.add_argument('--model', action='store', dest='model', default='annotation')

    def handle(self, *args, **options):
        try:
            language = Language.objects.get(iso=options['language'])
        except Language.DoesNotExist:
            raise CommandError('Language {} does not exist'.format(options['language']))

        for filename in options['filenames']:
            with open(filename, 'rb') as csvfile:
                try:
                    process_file(csvfile, language, options['use_other_label'], options['model'])
                    self.stdout.write('Successfully imported labels')
                except ValueError as e:
                    raise CommandError(e.message)


def process_file(f, language, use_other_label, model='annotation'):
    for n, row in enumerate(f):
        if n == 0:
            continue

        row = row.strip()
        if row:
            encoded = [c.decode('utf-8') for c in row.split('\t')]

            if model == 'annotation':
                update_annotation(language, encoded, use_other_label)
            elif model == 'fragment':
                update_fragment(language, encoded, use_other_label)
            else:
                raise ValueError(u'Unknown model {}'.format(model))


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
        raise ValueError(u'Annotation with pk {} not found.'.format(row[0]))
    except Tense.DoesNotExist:
        raise ValueError(u'Tense with title "{}" not found.'.format(row[1]))


def update_fragment(language, row, use_other_label=False):
    try:
        # Retrieve Fragment
        fragment = Fragment.objects.get(pk=row[0], language=language)

        # Add Tense or other_label
        if use_other_label:
            fragment.other_label = row[1]
        else:
            fragment.tense = Tense.objects.get(title__iexact=row[1], language=language)

        # Save Fragment
        fragment.save()
    except Fragment.DoesNotExist:
        raise ValueError(u'Fragment with pk {} not found.'.format(row[0]))
    except Tense.DoesNotExist:
        raise ValueError(u'Tense with title "{}" not found.'.format(row[1]))
