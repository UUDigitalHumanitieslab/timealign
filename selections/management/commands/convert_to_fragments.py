# -*- coding: utf-8 -*-

import csv
from collections import defaultdict

from lxml import etree

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from annotations.models import Language, Corpus, Document, Fragment, Tense, Alignment
from annotations.management.commands.add_fragments import retrieve_languages, create_to_fragments
from annotations.management.commands.constants import COLUMN_DOCUMENT, COLUMN_XML

from selections.models import Selection, PreProcessFragment


class Command(BaseCommand):
    help = 'Converts Selections to Fragments.'

    def add_arguments(self, parser):
        parser.add_argument('corpus', type=str)
        parser.add_argument('language', type=str)
        parser.add_argument('filenames', type=str, nargs='+')

        parser.add_argument('--create', action='store_true', dest='create', default=False,
                            help='Create Fragments from PreProcessFragments (instead of looking them up)')
        parser.add_argument('--document', type=str)

    def handle(self, *args, **options):
        # Retrieve the Corpus from the database
        try:
            corpus = Corpus.objects.get(title=options['corpus'])
        except Corpus.DoesNotExist:
            raise CommandError('Corpus with title {} does not exist'.format(options['corpus']))

        # Retrieve the Language from the database
        try:
            language = Language.objects.get(iso=options['language'])
        except Language.DoesNotExist:
            raise CommandError('Language with iso {} does not exist'.format(options['language']))

        # Check whether filenames have been supplied
        if len(options['filenames']) == 0:
            raise CommandError('No documents specified')

        document = None
        if options['document']:
            try:
                document = Document.objects.get(corpus=corpus, title=options['document'])
            except Document.DoesNotExist:
                raise CommandError('Document with title {} does not exist'.format(options['document']))

        fragment_cache = defaultdict(list)

        if options['create']:
            selections = Selection.objects \
                .filter(is_no_target=False) \
                .filter(fragment__document__corpus=corpus) \
                .filter(fragment__language=language) \
                .filter(resulting_fragment__isnull=True)

            if document:
                selections = selections.filter(fragment__document=document)

            for selection in selections:
                selected_words = []
                for selected_word in selection.words.all():
                    selected_words.append(selected_word.xml_id)

                with transaction.atomic():
                    f = selection.fragment
                    sentences = f.sentence_set.all()

                    f.__class__ = Fragment
                    f.pk = None

                    if selection.tense:
                        f.tense = Tense.objects.get(language=f.language, title=selection.tense)
                    if selection.other_label:
                        f.other_label = selection.other_label

                    f.save()

                    # Save the Fragment as resulting Fragment on the Selection
                    selection.resulting_fragment = f
                    selection.save()

                    for sentence in sentences:
                        s = sentence
                        words = s.word_set.all()

                        s.pk = None
                        s.fragment = f
                        s.save()

                        fragment_cache[(f.document.pk, s.xml_id)].append(f)

                        for word in words:
                            w = word
                            w.pk = None
                            w.sentence = s
                            w.is_target = w.xml_id in selected_words
                            w.save()

                    # Re-save the Fragment to set formal_structure and sentence_function if necessary
                    if corpus.check_structure:
                        f.save()
        else:
            # Fetch Fragments that are not PreProcessFragments (TODO: in 1.11, use .difference() for this)
            fragments = Fragment.objects.filter(document__corpus=corpus, language=language)
            pp_fragments = PreProcessFragment.objects.filter(document__corpus=corpus, language=language)
            fragments = fragments.exclude(pk__in=pp_fragments)

            # Create a Fragment cache
            for fragment in fragments:
                for sentence in fragment.sentence_set.all():
                    fragment_cache[(fragment.document.pk, sentence.xml_id)].append(fragment)

        for filename in options['filenames']:
            with open(filename, 'rb') as f:
                csv_reader = csv.reader(f, delimiter=';')
                languages_to = dict()
                for n, row in enumerate(csv_reader):
                    # Retrieve the languages from the first row of the output
                    if n == 0:
                        _, languages_to = retrieve_languages(row)
                        continue

                    with transaction.atomic():
                        doc, _ = Document.objects.get_or_create(corpus=corpus, title=row[COLUMN_DOCUMENT])

                        if document and document != doc:
                            continue

                        for s in etree.fromstring(row[COLUMN_XML]).xpath('.//s'):
                            fragments = fragment_cache.get((doc.pk, s.get('id')))
                            if fragments:
                                for fragment in fragments:
                                    languages = languages_to
                                    for alignment in Alignment.objects.filter(original_fragment=fragment):
                                        languages = {key: val for key, val in languages.items()
                                                     if val != alignment.translated_fragment.language}

                                    create_to_fragments(doc, fragment, languages, row)

                    self.stdout.write(self.style.SUCCESS('Line {} processed'.format(n)))
