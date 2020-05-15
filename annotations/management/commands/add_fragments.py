import csv

from lxml import etree

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from .constants import COLUMN_DOCUMENT, COLUMN_TYPE, COLUMN_IDS, COLUMN_XML, FROM_WIDTH, TO_WIDTH
from annotations.models import Language, Tense, Corpus, Document, Fragment, Sentence, Word, Alignment, LabelKey


class Command(BaseCommand):
    help = 'Reads in the Fragments for a Document and creates Alignments.'

    def add_arguments(self, parser):
        parser.add_argument('corpus', type=str)
        parser.add_argument('filenames', type=str, nargs='+')

        parser.add_argument('--use_label', dest='use_label')
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
                    process_file(f, corpus, use_label=options['use_label'])
                    self.stdout.write(self.style.SUCCESS('Successfully imported fragments'))
                except Exception as e:
                    raise CommandError(e)


def process_file(f, corpus, use_label_pk=None, use_label=None):
    lines = f.read().decode('utf-8-sig').splitlines()
    csv_reader = csv.reader(lines, delimiter=';')
    label_key = None
    if use_label_pk:
        label_key = LabelKey.objects.get(pk=use_label_pk)
    elif use_label:
        label_key = LabelKey.objects.get(title=use_label, corpora=corpus)

    for n, row in enumerate(csv_reader):
        # Retrieve the languages from the first row of the output
        if n == 0:
            language_from, languages_to = retrieve_languages(row)
            continue

        # For every other line, create a Fragment and its Alignments
        with transaction.atomic():
            doc, _ = Document.objects.get_or_create(corpus=corpus, title=row[COLUMN_DOCUMENT])

            from_fragment = Fragment.objects.create(language=language_from,
                                                    document=doc)

            type_value = row[COLUMN_TYPE]
            # Add other_label or Tense to Fragment
            if label_key:
                label, _ = label_key.labels.get_or_create(title=type_value)
                from_fragment.labels.add(label)
            else:
                try:
                    from_fragment.tense = Tense.objects.get(language=language_from, title=type_value)
                except Tense.DoesNotExist:
                    raise ValueError('Unknown tense: {}'.format(type_value))

            from_fragment.save()

            # Add Sentences to Fragment
            add_sentences(from_fragment, row[COLUMN_XML], row[COLUMN_IDS].split(' '))

            # Create the Fragments in other Languages and add the Alignment object
            create_to_fragments(doc, from_fragment, languages_to, row)


def create_to_fragments(document, from_fragment, languages_to, row):
    for m, language_to in list(languages_to.items()):
        if row[m]:
            to_fragment = Fragment.objects.create(language=language_to,
                                                  document=document)
            add_sentences(to_fragment, row[m])

            Alignment.objects.create(original_fragment=from_fragment,
                                     translated_fragment=to_fragment,
                                     type=row[m - 1])


def retrieve_languages(row, header_width=FROM_WIDTH):
    languages_to = dict()
    language_from = Language.objects.get(iso=row[COLUMN_XML])
    for i in range(header_width + 1, len(row), TO_WIDTH):
        languages_to[i] = Language.objects.get(iso=row[i])
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
