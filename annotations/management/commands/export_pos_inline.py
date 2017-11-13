# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError

from annotations.models import Corpus, Language, Annotation, Fragment, Word
from .utils import UnicodeWriter, pad_list


class Command(BaseCommand):
    help = 'Exports existing (correct) Annotations with POS tags for the given languages'

    def add_arguments(self, parser):
        parser.add_argument('corpus', type=str)
        parser.add_argument('source_language', type=str)
        parser.add_argument('languages', nargs='+', type=str)

    def handle(self, *args, **options):
        # Retrieve the Corpus from the database
        try:
            corpus = Corpus.objects.get(title=options['corpus'])
        except Corpus.DoesNotExist:
            raise CommandError('Corpus with title {} does not exist'.format(options['corpus']))

        try:
            source_language = Language.objects.get(iso=options['source_language'])
        except Language.DoesNotExist:
            raise CommandError('Language with iso {} does not exist'.format(options['source_language']))

        for language in options['languages']:
            if not corpus.languages.filter(iso=language):
                raise CommandError('Language {} does not exist'.format(language))

        languages = Language.objects.filter(iso__in=options['languages']).order_by('iso')

        with open('pos.csv', 'wb') as csvfile:
            csvfile.write(u'\uFEFF'.encode('utf-8'))  # the UTF-8 BOM to hint Excel we are using that...
            csv_writer = UnicodeWriter(csvfile, delimiter=';')

            top = [''] * 4
            header = ['id', 'source words', 'sentence', 'tense']
            for language in languages:
                header.extend(['sentence', 'tense', 'w1', 'w2', 'w3', 'w4', 'w5'])
                top.extend([language.title] * 6)

            csv_writer.writerow(top)
            csv_writer.writerow(header)

            rows = []
            for fragment in Fragment.objects.filter(language=source_language, document__corpus=corpus):
                row = []

                # Retrieve the Annotations for this Fragment...
                annotations = Annotation.objects \
                    .filter(is_no_target=False, is_translation=True,
                            alignment__original_fragment=fragment,
                            alignment__translated_fragment__language__in=languages) \
                    .order_by('alignment__translated_fragment__language__iso')
                # ... but only allow Fragments that have Alignments in all languages
                if annotations.count() == languages.count():

                    words = Word.objects.filter(sentence__fragment=fragment, is_target=True)
                    row.append(str(fragment.pk))
                    row.append(' '.join([word.word for word in words]))
                    row.append(fragment.full())
                    row.append(fragment.tense.title)

                    for annotation in annotations:
                        w = [word.word for word in annotation.words.all()]
                        row.append(annotation.alignment.translated_fragment.full())
                        row.append(annotation.label())
                        row.extend(pad_list(w, 5))

                    rows.append(row)

            csv_writer.writerows(rows)
