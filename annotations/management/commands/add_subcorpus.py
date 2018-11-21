# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError

from annotations.models import Language, Corpus, Document, FocusSet, FocusSentence


class Command(BaseCommand):
    help = 'Adds a FocusSet programmatically from a tab-separated file'

    def add_arguments(self, parser):
        parser.add_argument('corpus', type=str)
        parser.add_argument('language', type=str)
        parser.add_argument('focusset', type=str)
        parser.add_argument('filename', type=str)
        parser.add_argument('--delete', action='store_true', dest='delete', default=False,
                            help='Delete existing FocusSentences for this FocusSet')

    def handle(self, *args, **options):
        try:
            language = Language.objects.get(iso=options['language'])
            corpus = Corpus.objects.get(title=options['corpus'])
        except Language.DoesNotExist:
            raise CommandError('Language with iso {} does not exist'.format(options['language']))
        except Corpus.DoesNotExist:
            raise CommandError('Corpus with title {} does not exist'.format(options['corpus']))

        focus_set, _ = FocusSet.objects.get_or_create(title=options['focusset'], corpus=corpus, language=language)

        if options['delete']:
            FocusSentence.objects.filter(focus_set=focus_set).delete()

        with open(options['filename'], 'rb') as f:
            try:
                process_file(corpus, focus_set, f)
                self.stdout.write('Successfully created a FocusSet')
            except ValueError as e:
                raise CommandError(e.message)


def process_file(corpus, focus_set, f):
    for n, row in enumerate(f):
        if n == 0:
            continue

        row = row.strip()
        if row:
            encoded = [c.decode('utf-8') for c in row.split('\t')]
            create_focus_sentence(corpus, focus_set, encoded)


def create_focus_sentence(corpus, focus_set, row):
    try:
        document = Document.objects.get(corpus=corpus, title=row[0])
        FocusSentence.objects.create(focus_set=focus_set, document=document, xml_id=row[1])
    except Document.DoesNotExist:
        raise ValueError(u'Document with title {} not found.'.format(row[0]))
