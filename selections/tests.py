from django.contrib.auth.models import User
from django.test import TestCase

from annotations.models import Language, Corpus, Document, Sentence, Word

from .models import PreProcessFragment, Selection
from .utils import get_random_fragment, get_open_fragments, get_selection_order


class SelectionTestCase(TestCase):
    fixtures = ['languages']

    def setUp(self):
        c = Corpus.objects.create(title='test')
        self.d = Document.objects.create(title='test', corpus=c)
        self.en = Language.objects.get(iso='en')

        self.u1 = User.objects.create_user(username='test1', email='test@test.com', password='secret')
        self.u2 = User.objects.create_user(username='test2', email='test@test.com', password='secret')

        c.annotators = User.objects.all()
        c.save()

        self.f1 = PreProcessFragment.objects.create(language=self.en, document=self.d)
        s = Sentence.objects.create(xml_id='en1', fragment=self.f1)
        for n, w in enumerate('This is hard to test'.split()):
            Word.objects.create(word=w, sentence=s)

        self.f2 = PreProcessFragment.objects.create(language=self.en, document=self.d)
        s = Sentence.objects.create(xml_id='en2', fragment=self.f2)
        for n, w in enumerate('" Mary has just played a great move " , said John'.split()):
            Word.objects.create(word=w, sentence=s)

    def test_open_fragments(self):
        self.assertEqual(2, get_open_fragments(self.u1, self.en).count())
        self.assertEqual(2, get_open_fragments(self.u2, self.en).count())

        s1 = Selection.objects.create(fragment=self.f1, selected_by=self.u1)
        s1.words = Word.objects.filter(sentence__fragment=self.f1, word='is')
        s1.save()

        self.assertEqual(1, get_open_fragments(self.u1, self.en).count())
        self.assertEqual(1, get_open_fragments(self.u2, self.en).count())

        f = get_random_fragment(self.u1, self.en)
        self.assertEqual(self.f2, f)

        o = get_selection_order(self.f2, self.u1)
        s2 = Selection.objects.create(fragment=self.f2, selected_by=self.u1, order=o, is_final=False)
        s2.words = Word.objects.filter(sentence__fragment=self.f2, word='has') | \
                  Word.objects.filter(sentence__fragment=self.f2, word='played')
        s2.save()

        self.assertEqual(1, o)
        self.assertEqual(1, get_open_fragments(self.u1, self.en).count())
        self.assertEqual(1, get_open_fragments(self.u2, self.en).count())

        o = get_selection_order(self.f2, self.u1)
        s3 = Selection.objects.create(fragment=self.f2, selected_by=self.u1, order=o)
        s3.words = Word.objects.filter(sentence__fragment=self.f2, word='said')
        s3.save()

        self.assertEqual(2, o)
        self.assertEqual(0, get_open_fragments(self.u1, self.en).count())
        self.assertEqual(0, get_open_fragments(self.u2, self.en).count())

        # Adding a new Fragment with a coordinated VP
        self.f3 = PreProcessFragment.objects.create(language=self.en, document=self.d)
        sentence = Sentence.objects.create(xml_id='en2', fragment=self.f2)
        for n, w in enumerate('He could enter and leave in two minutes'.split()):
            Word.objects.create(word=w, sentence=sentence)

        f = get_random_fragment(self.u1, self.en)
        self.assertEqual(self.f3, f)

        o = get_selection_order(self.f3, self.u1)
        s4 = Selection.objects.create(fragment=self.f3, selected_by=self.u1, order=o, is_final=False)
        s4.words = Word.objects.filter(sentence__fragment=self.f3, word='could') | \
                  Word.objects.filter(sentence__fragment=self.f3, word='enter')
        s4.save()

        self.assertEqual(1, o)
        self.assertEqual(1, get_open_fragments(self.u1, self.en).count())
        self.assertEqual(1, get_open_fragments(self.u2, self.en).count())

        o = get_selection_order(self.f3, self.u1)
        s5 = Selection.objects.create(fragment=self.f3, selected_by=self.u1, order=o, is_final=True)
        s5.words = Word.objects.filter(sentence__fragment=self.f3, word='could') | \
                  Word.objects.filter(sentence__fragment=self.f3, word='leave')
        s5.save()

        self.assertEqual(2, o)
        self.assertEqual(0, get_open_fragments(self.u1, self.en).count())
        self.assertEqual(0, get_open_fragments(self.u2, self.en).count())

        s5.delete()  # Notice that this does not work when we delete s4. TODO: do we consider this a bug?
        self.assertEqual(1, get_open_fragments(self.u1, self.en).count())
        self.assertEqual(1, get_open_fragments(self.u2, self.en).count())

    def test_xml_order(self):
        s = Sentence.objects.create(xml_id='test_order', fragment=self.f1)
        w1 = Word.objects.create(word='w1', sentence=s, xml_id='w1.1.9')
        w2 = Word.objects.create(word='w2', sentence=s, xml_id='w1.2.9')
        w3 = Word.objects.create(word='w3', sentence=s, xml_id='w1.1.10')
        w4 = Word.objects.create(word='w4', sentence=s, xml_id='w2.1.10')

        s1 = Selection.objects.create(fragment=self.f1, selected_by=self.u1)
        s1.words = {w1, w2, w3, w4}
        s1.save()

        self.assertEqual(s1.annotated_words(), ' '.join([w1.word, w3.word, w2.word, w4.word]))

