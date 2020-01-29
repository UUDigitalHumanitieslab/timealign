import glob
import os
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from annotations.models import Language, Corpus, Source, Document, SubCorpus, SubSentence, corpus_path


class Command(BaseCommand):
    help = 'Adds sources to documents in a corpus'

    def add_arguments(self, parser):
        parser.add_argument('corpus', type=str)
        parser.add_argument('path', type=str)

        parser.add_argument('--replace', action='store_true', dest='replace', default=False,
                            help='Replace existing Sources')

    def handle(self, *args, **options):
        try:
            corpus = Corpus.objects.get(title=options['corpus'])
        except Corpus.DoesNotExist:
            raise CommandError('Corpus with title {} does not exist'.format(options['corpus']))

        filenames = glob.glob('{}/**/*.xml'.format(options['path']))

        for document in corpus.documents.all():
            print('Sources for: {}'.format(document.title))
            matches = [f for f in filenames if f.endswith(document.title)]
            for m in matches:
                language_iso = m.split(os.path.sep)[-2]
                try:
                    language = Language.objects.get(iso=language_iso)
                except Language.DoesNotExist:
                    print('Skipping unknown language: {}'.format(language_iso))

                if options['replace']:
                    document.source_set.filter(language=language).delete()
                source = Source.objects.create(language=language, document=document)

                path = corpus_path(source, document.title)
                os.makedirs(os.path.split(path)[0], exist_ok=True)
                shutil.copy(m, os.path.join(settings.MEDIA_ROOT, path))
                source.xml_file = path
                source.save()
                print('Added {} for {}'.format(document.title, language.title))
