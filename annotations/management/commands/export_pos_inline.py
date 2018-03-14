# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Max

from annotations.models import Corpus, Language, Annotation, Fragment, Word
from .utils import UnicodeWriter, pad_list


class Command(BaseCommand):
    help = 'Exports existing (correct) Annotations with POS tags for the given languages'

    def add_arguments(self, parser):
        parser.add_argument('corpus', type=str)
        parser.add_argument('source_language', type=str)
        parser.add_argument('languages', nargs='+', type=str)
        parser.add_argument('--doc', dest='document')

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

            annotations = Annotation.objects. \
                filter(alignment__translated_fragment__language__iso=language,
                       alignment__translated_fragment__document__corpus=corpus)
            annotations = annotations.filter(is_no_target=False, is_translation=True)

            if options['document'] is not None:
                annotations = annotations.filter(alignment__translated_fragment__document__title=options['document'])

            # TODO: would be nice to group by language, so the max_words value can be set per language
            annotations = annotations.select_related().annotate(selected_words=Count('words'))
            max_words = annotations.aggregate(Max('selected_words'))['selected_words__max']

            fragments = Fragment.objects.filter(language=source_language, document__corpus=corpus)
            if options['document'] is not None:
                fragments = fragments.filter(document__title=options['document'])

            rows = []
            for fragment in fragments:
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
                        row.extend(pad_list(w, max_words))

                    rows.append(row)

            for language in languages:
                top.extend([language.title] * (max_words + 2))
                header.extend(['sentence', 'tense'])
                header.extend(['w' + str(i + 1) for i in range(max_words)])

            csv_writer.writerow(top)
            csv_writer.writerow(header)
            csv_writer.writerows(rows)
