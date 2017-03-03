from django.contrib.auth.models import User
from django.test import TestCase

from annotations.models import Language, Corpus, Document, Sentence, Word

from .models import PreProcessFragment, Selection
from .utils import get_random_fragment


class VPSelectTestCase(TestCase):
    fixtures = ['languages']

    def setUp(self):
        c = Corpus.objects.create(title='test')
        d = Document.objects.create(title='test', corpus=c)
        en = Language.objects.get(iso='en')

        self.u1 = User.objects.create_user(username='test1', email='test@test.com', password='secret')
        self.u2 = User.objects.create_user(username='test2', email='test@test.com', password='secret')

        c.annotators = User.objects.all()
        c.save()

        self.f1 = PreProcessFragment.objects.create(language=en, document=d)
        s = Sentence.objects.create(xml_id='en1', fragment=self.f1)
        for n, w in enumerate('This is hard to test'.split()):
            Word.objects.create(word=w, sentence=s)

        self.f2 = PreProcessFragment.objects.create(language=en, document=d)
        s = Sentence.objects.create(xml_id='en2', fragment=self.f2)
        for n, w in enumerate('" Mary has just played a great move " , said John'.split()):
            Word.objects.create(word=w, sentence=s)

    def test_target_words(self):
        s = Selection.objects.create(fragment=self.f1, selected_by=self.u1)
        s.words = Word.objects.filter(sentence__fragment=self.f1, word='is')
        s.save()

        f = get_random_fragment(self.u1, Language.objects.get(iso='en'))
        self.assertEquals(f, self.f2)
