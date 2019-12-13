# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from annotations.models import Language, Corpus, Document, SubCorpus, SubSentence


class Command(BaseCommand):
    help = 'Adds a SubCorpus programmatically from a tab-separated file'

    def add_arguments(self, parser):
        parser.add_argument('corpus', type=str)
        parser.add_argument('language', type=str)
        parser.add_argument('subcorpus', type=str)
        parser.add_argument('filename', type=str)
        parser.add_argument('--delete', action='store_true', dest='delete', default=False,
                            help='Delete existing SubSentences for this SubCorpus')

    def handle(self, *args, **options):
        try:
            language = Language.objects.get(iso=options['language'])
            corpus = Corpus.objects.get(title=options['corpus'])
        except Language.DoesNotExist:
            raise CommandError('Language with iso {} does not exist'.format(options['language']))
        except Corpus.DoesNotExist:
            raise CommandError('Corpus with title {} does not exist'.format(options['corpus']))

        subcorpus, _ = SubCorpus.objects.get_or_create(title=options['subcorpus'], corpus=corpus, language=language)

        if options['delete']:
            SubSentence.objects.filter(subcorpus=subcorpus).delete()

        with open(options['filename'], 'r') as f:
            try:
                process_file(corpus, subcorpus, f)
                self.stdout.write(self.style.SUCCESS('Successfully created SubCorpus {}'.format(subcorpus.title)))
            except ValueError as e:
                raise CommandError(e.message)


def process_file(corpus, subcorpus, f):
    with transaction.atomic():
        for n, row in enumerate(f):
            if n == 0:
                continue

            row = row.strip()
            if row:
                encoded = [c.decode('utf-8') for c in row.split('\t')]
                create_subsentence(corpus, subcorpus, encoded)


def create_subsentence(corpus, subcorpus, row):
    try:
        document = Document.objects.get(corpus=corpus, title=row[0])
        SubSentence.objects.create(subcorpus=subcorpus, document=document, xml_id=row[1])
    except Document.DoesNotExist:
        raise ValueError('Document with title {} not found.'.format(row[0]))
