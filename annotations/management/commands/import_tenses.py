# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError

from annotations.models import Language, Tense, Annotation, Fragment, LabelKey, Label


class Command(BaseCommand):
    help = 'Imports tenses for Annotations'

    def add_arguments(self, parser):
        parser.add_argument('language', type=str)
        parser.add_argument('filenames', nargs='+', type=str)
        parser.add_argument('--model', action='store', dest='model', default='annotation')

    def handle(self, *args, **options):
        try:
            language = Language.objects.get(iso=options['language'])
        except Language.DoesNotExist:
            raise CommandError('Language {} does not exist'.format(options['language']))

        for filename in options['filenames']:
            with open(filename, 'r') as csvfile:
                try:
                    process_file(csvfile, language, options['model'])
                    self.stdout.write('Successfully imported labels')
                except ValueError as e:
                    raise CommandError(e.message)


def process_file(f, language, model='annotation'):
    f = iter(f)
    header = next(f)
    if isinstance(header, bytes):
        header = header.decode()
    header = header.strip().split('\t')

    columns = []
    for h in header[1:]:
        if isinstance(h, bytes):
            h = h.decode()
        if h.lower() in ['tense', 'comments']:
            columns.append(h)
        else:
            try:
                key = LabelKey.objects.get(title__iexact=h)
                columns.append(key)
            except LabelKey.DoesNotExist:
                raise ValueError('Unknown label "{}"'.format(h))

    for row in f:
        row = row.decode().strip()
        if row:
            encoded = row.split('\t')

            if model == 'annotation':
                obj = get_annotation(encoded)
            elif model == 'fragment':
                obj = get_fragment(encoded)
            else:
                raise ValueError('Unknown model {}'.format(model))

            update_fields(obj, language, encoded, columns)


def update_fields(obj, language, row, columns):
    for idx, column in enumerate(columns):
        if idx + 1 >= len(row):
            continue
        cell = row[idx + 1]
        if column == 'tense':
            try:
                obj.tense = Tense.objects.get(title__iexact=cell, language=language)
            except Tense.DoesNotExist:
                raise ValueError('Tense with title "{}" not found.'.format(row[1]))
        elif column == 'comments':
            if isinstance(obj, Annotation):
                obj.comments = cell
            else:
                raise ValueError('Cannot add comments to Fragment')
        elif isinstance(column, LabelKey):
            label, created = Label.objects.get_or_create(title=cell,
                                                         key=column,
                                                         language=language)
            if created:
                label.save()

            obj.labels.add(label)

    obj.save()


def get_annotation(row):
    try:
        return Annotation.objects.get(pk=row[0])

    except Annotation.DoesNotExist:
        raise ValueError('Annotation with pk {} not found.'.format(row[0]))


def get_fragment(row):
    try:
        return Fragment.objects.get(pk=row[0])

    except Fragment.DoesNotExist:
        raise ValueError('Fragment with pk {} not found.'.format(row[0]))
