from django.contrib.auth.models import User
from django.test import TestCase

from annotations.models import Language, Corpus, Document, Sentence, Word

from .models import PreProcessFragment, Selection
from .utils import get_random_fragment, get_open_fragments, get_selection_order


class VPSelectTestCase(TestCase):
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
        self.assertEquals(2, get_open_fragments(self.u1, self.en).count())
        self.assertEquals(2, get_open_fragments(self.u2, self.en).count())

        s = Selection.objects.create(fragment=self.f1, selected_by=self.u1)
        s.words = Word.objects.filter(sentence__fragment=self.f1, word='is')
        s.save()

        self.assertEquals(1, get_open_fragments(self.u1, self.en).count())
        self.assertEquals(1, get_open_fragments(self.u2, self.en).count())

        f = get_random_fragment(self.u1, self.en)
        self.assertEquals(self.f2, f)

        o = get_selection_order(self.f2, self.u1)
        s = Selection.objects.create(fragment=self.f2, selected_by=self.u1, order=o, is_final=False)
        s.words = Word.objects.filter(sentence__fragment=self.f2, word='has') | \
                  Word.objects.filter(sentence__fragment=self.f2, word='played')
        s.save()

        self.assertEquals(1, o)
        self.assertEquals(1, get_open_fragments(self.u1, self.en).count())
        self.assertEquals(1, get_open_fragments(self.u2, self.en).count())

        o = get_selection_order(self.f2, self.u1)
        s = Selection.objects.create(fragment=self.f2, selected_by=self.u1, order=o)
        s.words = Word.objects.filter(sentence__fragment=self.f2, word='said')
        s.save()

        self.assertEquals(2, o)
        self.assertEquals(0, get_open_fragments(self.u1, self.en).count())
        self.assertEquals(0, get_open_fragments(self.u2, self.en).count())

        # Adding a new Fragment with a coordinated VP
        self.f3 = PreProcessFragment.objects.create(language=self.en, document=self.d)
        s = Sentence.objects.create(xml_id='en2', fragment=self.f2)
        for n, w in enumerate('He could enter and leave in two minutes'.split()):
            Word.objects.create(word=w, sentence=s)

        f = get_random_fragment(self.u1, self.en)
        self.assertEquals(self.f3, f)

        o = get_selection_order(self.f3, self.u1)
        s = Selection.objects.create(fragment=self.f3, selected_by=self.u1, order=o, is_final=False)
        s.words = Word.objects.filter(sentence__fragment=self.f3, word='could') | \
                  Word.objects.filter(sentence__fragment=self.f3, word='enter')
        s.save()

        self.assertEquals(1, o)
        self.assertEquals(1, get_open_fragments(self.u1, self.en).count())
        self.assertEquals(1, get_open_fragments(self.u2, self.en).count())

        o = get_selection_order(self.f3, self.u1)
        s = Selection.objects.create(fragment=self.f3, selected_by=self.u1, order=o, is_final=True)
        s.words = Word.objects.filter(sentence__fragment=self.f3, word='could') | \
                  Word.objects.filter(sentence__fragment=self.f3, word='leave')
        s.save()

        self.assertEquals(2, o)
        self.assertEquals(0, get_open_fragments(self.u1, self.en).count())
        self.assertEquals(0, get_open_fragments(self.u2, self.en).count())
