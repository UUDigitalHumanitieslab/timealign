# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError

from annotations.models import Corpus, Annotation, Fragment, Word
from .utils import open_csv, open_xlsx, pad_list


class Command(BaseCommand):
    help = 'Exports existing (correct) Annotations with POS tags for the given languages'

    def add_arguments(self, parser):
        parser.add_argument('corpus', type=str)
        parser.add_argument('--add_sources', action='store_true', dest='add_sources', default=False)
        parser.add_argument('languages', nargs='+', type=str)
        parser.add_argument('--xlsx', action='store_true', dest='format_xlsx', default=False)
        parser.add_argument('--doc', dest='document')

    def handle(self, *args, **options):
        # Retrieve the Corpus from the database
        try:
            corpus = Corpus.objects.get(title=options['corpus'])
        except Corpus.DoesNotExist:
            raise CommandError('Corpus with title {} does not exist'.format(options['corpus']))

        format_ = 'xlsx' if options['format_xlsx'] else 'csv'
        for language in options['languages']:
            if not corpus.languages.filter(iso=language):
                raise CommandError('Language {} does not exist'.format(language))

            self.export_language(language, corpus, format_,
                                 add_sources=options['add_sources'],
                                 document=options['document'])

    def export_language(self, language, corpus, format_, add_sources=False, document=None):
        filename = 'pos_{lang}.{ext}'.format(lang=language, ext=format_)

        if format_ == 'xlsx':
            opener = open_xlsx
        else:
            opener = open_csv

        with opener(filename) as writer:
            header = ['id', 'tense', 'source/target',
                      'w1', 'w2', 'w3', 'w4', 'w5', 'w6', 'w7', 'w8',
                      'pos1', 'pos2', 'pos3', 'pos4', 'pos5', 'pos6', 'pos7', 'pos8', 'comments',
                      'full fragment', 'source words', 'source fragment']
            writer.writerow(header)

            annotations = Annotation.objects. \
                filter(is_no_target=False, is_translation=True,
                       alignment__translated_fragment__language__iso=language,
                       alignment__translated_fragment__document__corpus=corpus)

            if document is not None:
                annotations = annotations.filter(alignment__translated_fragment__document__title=document)

            for annotation in annotations:
                words = annotation.words.all()
                w = [word.word for word in words]
                pos = [word.pos for word in words]
                tf = annotation.alignment.translated_fragment
                of = annotation.alignment.original_fragment
                writer.writerow([str(annotation.pk), annotation.label(), 'target'] +
                                pad_list(w, 8) +
                                pad_list(pos, 8) +
                                [annotation.comments, tf.full(), of.target_words(), of.full()])

            if add_sources:
                fragments = Fragment.objects.filter(language__iso=language, document__corpus=corpus)
                for fragment in fragments:
                    words = Word.objects.filter(sentence__fragment=fragment, is_target=True)
                    if words:
                        w = [word.word for word in words]
                        pos = [word.pos for word in words]
                        f = fragment.full()
                        writer.writerow([str(fragment.pk), fragment.tense.title, 'source'] +
                                        pad_list(w, 8) +
                                        pad_list(pos, 8) +
                                        ['', f, '', ''])
