from django.contrib.auth.models import User
from django.test import TestCase

from .models import Language, Corpus, Document, Fragment, Sentence, Word, Alignment, Annotation, Tense
from .utils import get_random_alignment, get_available_corpora, get_tenses


class FragmentTestCase(TestCase):
    fixtures = ['languages']

    def setUp(self):
        self.c1 = Corpus.objects.create(title='corpus1')
        self.c2 = Corpus.objects.create(title='corpus2')
        self.d = Document.objects.create(title='test', corpus=self.c1)
        self.en = Language.objects.get(iso='en')
        self.nl = Language.objects.get(iso='nl')

        self.u1 = User.objects.create_user(username='test1', email='test@test.com', password='secret', is_superuser=True)
        self.u2 = User.objects.create_user(username='test2', email='test@test.com', password='secret')

        self.c1.annotators = User.objects.filter(username='test1')
        self.c1.save()
        self.c2.annotators = User.objects.filter(username='test2')
        self.c2.save()

        self.f_en = Fragment.objects.create(language=self.en, document=self.d)
        s = Sentence.objects.create(xml_id='en1', fragment=self.f_en)
        for n, w in enumerate('This has always been hard to test'.split()):
            is_target = n in [1, 3]
            Word.objects.create(word=w, is_target=is_target, sentence=s)

        self.f_nl = Fragment.objects.create(language=self.nl, document=self.d)
        s = Sentence.objects.create(xml_id='nl1', fragment=self.f_nl)
        for n, w in enumerate('Dit is altijd moeilijk te testen geweest'.split()):
            is_target = n in [1, 6]
            Word.objects.create(word=w, is_target=is_target, sentence=s)

        self.alignment = Alignment.objects.create(original_fragment=self.f_en, translated_fragment=self.f_nl)

    # Testing utils.py
    def test_available_corpora(self):
        c = get_available_corpora(self.u1)
        self.assertListEqual(list(c), list(Corpus.objects.all()))

        c = get_available_corpora(self.u2)
        self.assertListEqual(list(c), list(Corpus.objects.filter(pk=self.c2.pk)))

    def test_random_alignment(self):
        a = get_random_alignment(self.u1, self.en, self.nl)
        self.assertEqual(a, self.alignment)

        a = get_random_alignment(self.u1, self.en, self.nl, self.c1)
        self.assertEqual(a, self.alignment)

        a = get_random_alignment(self.u1, self.nl, self.en, self.c2)
        self.assertIsNone(a)

        a = get_random_alignment(self.u1, self.en, self.nl, self.c2)
        self.assertIsNone(a)

        a = get_random_alignment(self.u2, self.en, self.nl)
        self.assertIsNone(a)

    def test_get_tenses(self):
        a = Annotation.objects.create(alignment=self.alignment, annotated_by=self.u1)
        a.tense = Tense.objects.get(language=self.nl, title='vtt')
        a.save()

        ts = get_tenses(self.nl)
        self.assertEqual(ts, ['vtt'])

    # Testing models.py
    def test_get_languages(self):
        self.c1.languages = Language.objects.filter(iso__in=['nl', 'en'])
        self.c1.save()

        ls = self.c1.get_languages()
        self.assertEqual(ls, 'en, nl')

    def test_target_words(self):
        self.assertEqual(self.f_en.target_words(), 'has been')
        self.assertEqual(self.f_nl.target_words(), 'is geweest')
