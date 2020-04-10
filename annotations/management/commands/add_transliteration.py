from django.core.management.base import BaseCommand
from polyglot.transliteration import Transliterator

from annotations.models import Transliteration, Word


class Command(BaseCommand):
    help = 'Adds transliteration for all existing fragments in a corpus (per language)'

    def add_arguments(self, parser):
        parser.add_argument('corpus', type=str)
        parser.add_argument('language-code', type=str)

    def handle(self, *args, **options):
        lang = options['language-code']
        tr = Transliterator(source_lang=lang)

        words = Word.objects.filter(sentence__fragment__document__corpus__id=options['corpus'],
                                    sentence__fragment__language__iso=lang)
        for word in words:
            text = tr.transliterate(word.word)
            t = Transliteration.objects.create(word=word, text=text)
            t.save()
