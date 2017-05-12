# -*- coding: utf-8 -*-

import csv

from lxml import etree

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from annotations.models import Language, Corpus, Document, Fragment, Sentence, Word, Alignment
from selections.models import Selection


class Command(BaseCommand):
    help = 'Converts Selections to Fragments.'

    def add_arguments(self, parser):
        parser.add_argument('corpus', type=str)
        parser.add_argument('filenames', type=str, nargs='+')

    def handle(self, *args, **options):
        # Retrieve the Corpus from the database
        try:
            corpus = Corpus.objects.get(title=options['corpus'])
        except Corpus.DoesNotExist:
            raise CommandError('Corpus with title {} does not exist'.format(options['corpus']))

        if len(options['filenames']) == 0:
            raise CommandError('No documents specified')

        sentence_cache = dict()
        selections = Selection.objects \
            .filter(is_no_target=False, fragment__document__corpus=corpus) \
            .exclude(tense=u'passé composé')
        for selection in selections:
            selected_words = []
            for selected_word in selection.words.all():
                selected_words.append(selected_word.xml_id)

            with transaction.atomic():
                f = selection.fragment
                sentences = f.sentence_set.all()

                f.__class__ = Fragment
                f.pk = None
                f.tense = selection.tense
                f.save()

                for sentence in sentences:
                    s = sentence
                    words = s.word_set.all()

                    s.pk = None
                    s.fragment = f
                    s.save()

                    sentence_cache[(f.document.pk, s.xml_id)] = s

                    for word in words:
                        w = word
                        w.pk = None
                        w.sentence = s
                        w.is_target = w.xml_id in selected_words
                        w.save()

        for filename in options['filenames']:
            with open(filename, 'rb') as f:
                csv_reader = csv.reader(f, delimiter=';')
                for n, row in enumerate(csv_reader):
                    if n == 0:
                        languages_to = dict()
                        for i in xrange(3, 21, 2):
                            if i >= len(row):
                                break
                            else:
                                languages_to[i] = Language.objects.get(iso=row[i])
                        continue

                    with transaction.atomic():
                        doc, _ = Document.objects.get_or_create(corpus=corpus, title=row[0])

                        for s in etree.fromstring(row[2]).xpath('.//s'):
                            sentence = sentence_cache.get((doc.pk, s.get('id')))
                            if sentence:
                                for m, language_to in languages_to.items():
                                    if row[m]:
                                        to_fragment = Fragment.objects.create(language=language_to,
                                                                              document=doc)
                                        add_sentences(to_fragment, row[m + 1])

                                        Alignment.objects.create(original_fragment=sentence.fragment,
                                                                 translated_fragment=to_fragment,
                                                                 type=row[m])

def add_sentences(fragment, xml, target_ids=[]):
    for s in etree.fromstring(xml).xpath('.//s'):
        sentence = Sentence.objects.create(xml_id=s.get('id'), fragment=fragment)
        for w in s.xpath('.//w'):
            xml_id = w.get('id')
            pos = w.get('tree') or w.get('pos') or w.get('hun') or '?'
            is_target = xml_id in target_ids
            Word.objects.create(xml_id=xml_id, word=w.text,
                                pos=pos, lemma=w.get('lem', '?'),
                                is_target=is_target, sentence=sentence)
