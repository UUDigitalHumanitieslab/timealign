from django.test import TestCase

from .models import Language, Corpus, Document, Fragment, Sentence, Word, Alignment


class FragmentTestCase(TestCase):
    fixtures = ['languages']

    def setUp(self):
        c = Corpus.objects.create(title='test')
        d = Document.objects.create(title='test', corpus=c)
        en = Language.objects.get(iso='en')
        nl = Language.objects.get(iso='nl')

        self.f_en = Fragment.objects.create(language=en, document=d)
        s = Sentence.objects.create(xml_id='en1', fragment=self.f_en)
        for n, w in enumerate('This has always been hard to test'.split()):
            is_target = n in [1, 3]
            Word.objects.create(word=w, is_target=is_target, sentence=s)

        self.f_nl = Fragment.objects.create(language=nl, document=d)
        s = Sentence.objects.create(xml_id='nl1', fragment=self.f_nl)
        for n, w in enumerate('Dit is altijd moeilijk te testen geweest'.split()):
            is_target = n in [1, 6]
            Word.objects.create(word=w, is_target=is_target, sentence=s)

        self.alignment = Alignment.objects.create(original_fragment=self.f_en, translated_fragment=self.f_nl)

    def test_target_words(self):
        self.assertEqual(self.f_en.target_words(), 'has been')
        self.assertEqual(self.f_nl.target_words(), 'is geweest')
