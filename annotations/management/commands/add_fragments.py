import csv

from lxml import etree

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Case, When

from .constants import COLUMN_DOCUMENT, COLUMN_TYPE, COLUMN_IDS, COLUMN_XML, FROM_WIDTH, TO_WIDTH
from annotations.models import Language, Tense, Corpus, Document, Fragment, Sentence, Word, Alignment, LabelKey


class Command(BaseCommand):
    help = 'Reads in the Fragments for a Document and creates Alignments.'

    def add_arguments(self, parser):
        parser.add_argument('corpus', type=str)
        parser.add_argument('filenames', type=str, nargs='+')

        parser.add_argument('--label_titles', dest='label_titles', nargs='+')
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
                    process_file(f, corpus, label_titles=options['label_titles'])
                    self.stdout.write(self.style.SUCCESS('Successfully imported fragments'))
                except Exception as e:
                    raise CommandError(e)


def process_file(f, corpus, label_pks=None, label_titles=None):
    lines = f.read().decode('utf-8-sig').splitlines()
    csv_reader = csv.reader(lines, delimiter=';')

    # Solution to preserve order taken from https://stackoverflow.com/a/37648265
    label_keys = LabelKey.objects.none()
    if label_pks:
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(label_pks)])
        label_keys = LabelKey.objects.filter(pk__in=label_pks).order_by(preserved)
    elif label_titles:
        preserved = Case(*[When(title=title, then=pos) for pos, title in enumerate(label_titles)])
        label_keys = LabelKey.objects.filter(title__in=label_titles, corpora=corpus).order_by(preserved)
    additional_columns = len(label_keys) - 1 if label_keys else 0

    for n, row in enumerate(csv_reader):
        # Retrieve the languages from the first row of the output
        if n == 0:
            language_from, languages_to = retrieve_languages(row, additional_columns)
            continue

        # For every other line, create a Fragment and its Alignments
        with transaction.atomic():
            doc, _ = Document.objects.get_or_create(corpus=corpus, title=row[COLUMN_DOCUMENT])

            from_fragment = Fragment.objects.create(language=language_from, document=doc)

            # Add Labels or Tense (the default) to Fragment
            if label_keys:
                for i, label_key in enumerate(label_keys):
                    label_title = row[COLUMN_TYPE + i]
                    label, _ = label_key.labels.get_or_create(language=language_from, title=label_title)
                    from_fragment.labels.add(label)
            else:
                tense_title = row[COLUMN_TYPE]
                try:
                    from_fragment.tense = Tense.objects.get(language=language_from, title=tense_title)
                except Tense.DoesNotExist:
                    raise ValueError('Unknown tense: {}'.format(tense_title))

            from_fragment.save()

            # Add Sentences to Fragment
            xml_column = row[COLUMN_XML + additional_columns]
            ids_column = row[COLUMN_IDS + additional_columns]
            add_sentences(from_fragment, xml_column, ids_column.split(' '))

            # Create the Fragments in other Languages and add the Alignment object
            create_to_fragments(doc, from_fragment, languages_to, row)


def create_to_fragments(document, from_fragment, languages_to, row):
    for m, language_to in list(languages_to.items()):
        if row[m]:
            to_fragment = Fragment.objects.create(language=language_to, document=document)
            add_sentences(to_fragment, row[m])

            Alignment.objects.create(original_fragment=from_fragment,
                                     translated_fragment=to_fragment,
                                     type=row[m - 1])


def retrieve_languages(row, additional_columns=0):
    xml_column = row[COLUMN_XML + additional_columns]
    language_from = Language.objects.get(iso=xml_column)

    languages_to = dict()
    for i in range(FROM_WIDTH + additional_columns + 1, len(row), TO_WIDTH):
        try:
            languages_to[i] = Language.objects.get(iso=row[i])
        except Language.DoesNotExist:
            raise ValueError('Unknown lanugage code: {}'.format(row[i]))
    return language_from, languages_to


def add_sentences(fragment, xml, target_ids=[]):
    for s in etree.fromstring(xml).xpath('.//s'):
        sentence = Sentence.objects.create(xml_id=s.get('id'), fragment=fragment)
        for w in s.xpath('.//w'):
            xml_id = w.get('id')
            pos = w.get('tree') or w.get('pos') or w.get('hun') or '?'
            is_in_dialogue_prob = float(w.get('dialog', 0))
            is_in_dialogue = is_in_dialogue_prob > 0
            is_target = xml_id in target_ids
            Word.objects.create(xml_id=xml_id,
                                word=w.text,
                                pos=pos,
                                lemma=w.get('lem', '?'),
                                is_in_dialogue_prob=is_in_dialogue_prob,
                                is_in_dialogue=is_in_dialogue,
                                is_target=is_target,
                                sentence=sentence)
