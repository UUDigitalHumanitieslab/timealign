from .models import Corpus, Annotation, Tense
from .utils import get_random_alignment, get_available_corpora, get_tenses
from .test_models import BaseTestCase


class UtilsTestCase(BaseTestCase):
    fixtures = ['languages']

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

        Annotation.objects.create(alignment=self.alignment, annotated_by=self.u1)
        a = get_random_alignment(self.u1, self.en, self.nl)
        self.assertIsNone(a)

    def test_get_tenses(self):
        a = Annotation.objects.create(alignment=self.alignment, annotated_by=self.u1)
        a.tense = Tense.objects.get(language=self.nl, title='vtt')
        a.save()

        self.assertEqual(get_tenses(self.nl), ['vtt'])
