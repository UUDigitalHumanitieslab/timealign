# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError

from annotations.models import Document, Fragment, Sentence, Alignment


class Command(BaseCommand):
    help = 'Moves Alignments to a related Document'

    def add_arguments(self, parser):
        parser.add_argument('from_document', type=str)
        parser.add_argument('to_document', type=str)
        parser.add_argument('base_language', type=str)

    def handle(self, *args, **options):
        try:
            from_doc = Document.objects.get(title=options['from_document'])
        except Document.DoesNotExist:
            raise CommandError('Matching document for {} not found'.format(options['from_document']))

        try:
            to_doc = Document.objects.get(title=options['to_document'])
        except Document.DoesNotExist:
            raise CommandError('Matching document for {} not found'.format(options['to_document']))

        for fragment in Fragment.objects.filter(document=from_doc, language=options['base_language']):
            for s in fragment.sentence_set.all():
                r = list(map(str, list(range(int(s.xml_id) - 4, int(s.xml_id) + 4))))
                sentences = Sentence.objects.\
                    filter(fragment__document=to_doc, xml_id__in=r).\
                    filter(fragment__language__iso=options['base_language'])
                for sentence in sentences:
                    if sentence.fragment.target_words() == fragment.target_words():
                        alignments = Alignment.objects.filter(original_fragment=fragment)
                        for alignment in alignments:
                            translated = alignment.translated_fragment
                            translated.document = to_doc
                            translated.save()

                            alignment.original_fragment = sentence.fragment
                            alignment.save()

                        fragment.delete()
                        break