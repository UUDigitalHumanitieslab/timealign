import csv

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from annotations.models import Language, Label, Corpus, Document, Fragment, Sentence, Word, Alignment, LabelKey, Annotation


class Command(BaseCommand):
    help = 'Imports Fragments including Labels, directly ready for creating Scenarios'

    def add_arguments(self, parser):
        parser.add_argument('corpus', type=str)
        parser.add_argument('filenames', type=str, nargs='+')

        parser.add_argument('--delete', action='store_true', dest='delete', default=False,
                            help='Delete existing Fragments (and contents) for this Corpus')

    def handle(self, *args, **options):
        # Retrieve the Corpus from the database
        try:
            corpus = Corpus.objects.get(title=options['corpus'])
        except Corpus.DoesNotExist:
            raise CommandError('Corpus with title {} does not exist'.format(options['corpus']))

        if len(options['filenames']) == 0:
            raise CommandError('No documents specified')

        if options['delete']:
            Fragment.objects.filter(document__corpus=corpus).delete()

        for filename in options['filenames']:
            with open(filename, 'rb') as f:
                try:
                    process_file(f, corpus)
                    self.stdout.write(self.style.SUCCESS('Successfully imported fragments'))
                except Exception as e:
                    raise CommandError(e)


def process_file(f, corpus):
    lines = f.read().decode('utf-8').splitlines()
    csv_reader = csv.reader(lines, delimiter=';')

    for n, row in enumerate(csv_reader):
        # Retrieve the languages from the first row of the output
        if n == 0:
            language_from, languages_to = retrieve_languages(row)
            continue

        # For every other line, create a Fragment and its Alignments
        with transaction.atomic():
            document, _ = Document.objects.get_or_create(corpus=corpus, title=row[1])

            from_fragment = Fragment.objects.create(language=language_from, document=document)

            # Add Labels or Tense (the default) to Fragment
            key = LabelKey.objects.get(title='LATE')
            if row[4]:
                label, _ = Label.objects.get_or_create(key=key, language=language_from, title=row[4])
                from_fragment.labels.add(label)
            from_fragment.save()

            sentence = Sentence.objects.create(fragment=from_fragment, xml_id=row[2])
            for i, word in enumerate(row[3].split(), start=1):  # Assumes that the input is tokenized
                xml_id = row[2] + '.' + str(i)
                is_target = word.lower() == row[4].lower()
                Word.objects.create(sentence=sentence, xml_id=xml_id, word=word, is_target=is_target)

            for column, language_to in languages_to.items():
                to_fragment = Fragment.objects.create(language=language_to, document=document)
                sentence = Sentence.objects.create(fragment=to_fragment, xml_id=row[2])
                word = Word.objects.create(sentence=sentence, xml_id=xml_id, word=row[column], is_target=True)

                alignment = Alignment.objects.create(original_fragment=from_fragment,
                                                     translated_fragment=to_fragment,
                                                     type='1 => 1')
                annotation = Annotation.objects.create(alignment=alignment)
                annotation.words.add(word)
                if row[column]:
                    label, _ = Label.objects.get_or_create(key=key, language=language_to, title=row[column])
                    annotation.labels.add(label)


def retrieve_languages(row):
    language_from = Language.objects.get(iso=row[4])

    languages_to = dict()
    for i in range(5, len(row)):
        try:
            languages_to[i] = Language.objects.get(iso=row[i])
        except Language.DoesNotExist:
            raise ValueError('Unknown language code: {}'.format(row[i]))
    return language_from, languages_to
