from django.contrib.auth.models import User
from django.test import TestCase

from stats.models import Scenario
from .models import Language, Corpus, Document, Fragment, Sentence, Word, \
    Alignment, Annotation, Tense, Label, LabelKey


class BaseTestCase(TestCase):
    def setUp(self):
        self.c1 = Corpus.objects.create(title='corpus1', is_public=True)
        self.c2 = Corpus.objects.create(title='corpus2')
        self.d = Document.objects.create(title='test', corpus=self.c1)
        self.en = Language.objects.get(iso='en')
        self.nl = Language.objects.get(iso='nl')

        self.u1 = User.objects.create_user(username='test1', email='test@test.com', password='secret', is_superuser=True)
        self.u2 = User.objects.create_user(username='test2', email='test@test.com', password='secret')

        self.c1.annotators.set(User.objects.filter(username='test1'))
        self.c1.save()
        self.c2.annotators.set(User.objects.filter(username='test2'))
        self.c2.save()

        self.f_en = Fragment.objects.create(language=self.en, document=self.d)
        s = Sentence.objects.create(xml_id='en1', fragment=self.f_en)
        for n, w in enumerate('This has always been hard to test'.split()):
            is_target = n in [1, 3]
            xml_id = 'w1.1.{}'.format(n + 1)
            Word.objects.create(word=w, xml_id=xml_id, is_target=is_target, sentence=s)

        self.f_nl = Fragment.objects.create(language=self.nl, document=self.d)
        s = Sentence.objects.create(xml_id='nl1', fragment=self.f_nl)
        for n, w in enumerate('Dit is altijd moeilijk te testen geweest'.split()):
            is_target = n in [1, 6]
            xml_id = 'w1.1.{}'.format(n + 1)
            Word.objects.create(word=w, xml_id=xml_id, is_target=is_target, sentence=s)

        self.alignment = Alignment.objects.create(original_fragment=self.f_en, translated_fragment=self.f_nl)

        dummy_mds_labels = {
            'en': [('Tense:19',), ('Tense:19',)],
            'nl': [('Tense:176',), ('Tense:355',)]
        }
        dummy_mds_fragments = [self.f_en.pk, self.f_nl.pk]
        dummy_scenario = Scenario.objects.create(corpus_id=self.c1.pk, owner_id=self.u1.pk, mds_labels=dummy_mds_labels,
                                                 mds_fragments=dummy_mds_fragments)

        self.scenario = dummy_scenario


class ModelsTestCase(BaseTestCase):
    fixtures = ['languages']

    # Testing models.py
    def test_get_languages(self):
        self.c1.languages.set(Language.objects.filter(iso__in=['nl', 'en']))
        self.c1.save()
        self.assertEqual(self.c1.get_languages(), 'en, nl')

    def test_get_annotators(self):
        self.assertEqual(self.c1.get_annotators(), 'test1')
        self.assertEqual(self.c1.get_annotators(), 'test1')

        self.c1.annotators.add(self.u2)
        self.c1.save()
        self.assertEqual(self.c1.get_annotators(), 'test1, test2')

        self.c2.annotators.clear()
        self.c2.save()
        self.assertEqual(self.c2.get_annotators(), 'none')

    def test_target_words(self):
        self.assertEqual(self.f_en.target_words(), 'has been')
        self.assertEqual(self.f_nl.target_words(), 'is geweest')

    def test_get_alignments(self):
        alignments = self.f_en.get_alignments()
        self.assertFalse(list(alignments))

        alignments = self.f_en.get_alignments(as_original=True)
        self.assertListEqual(list(alignments), list(Alignment.objects.all()))

        alignments = self.f_en.get_alignments(as_translation=True)
        self.assertFalse(list(alignments))

    def test_selected_words(self):
        annotation = Annotation.objects.create(alignment=self.alignment)
        annotation.words.add(Word.objects.get(sentence__fragment=self.f_en, xml_id='w1.1.4'))
        annotation.words.add(Word.objects.get(sentence__fragment=self.f_en, xml_id='w1.1.2'))
        annotation.save()
        self.assertEqual(annotation.selected_words(), 'has been')

    def test_label(self):
        label_key = LabelKey.objects.create(title='key')
        label_key.corpora.add(self.alignment.original_fragment.document.corpus)
        label = Label.objects.create(title='other', key=label_key)
        annotation = Annotation.objects.create(alignment=self.alignment)
        annotation.labels.add(label)
        annotation.save()
        self.assertEqual(annotation.get_labels(), 'other')

        annotation.tense = Tense.objects.get(language=self.nl, title='vtt')
        annotation.save()
        self.assertEqual(annotation.get_labels(), 'vtt, other')

    def test_to_html(self):
        html = '<ul><li>This <strong>has</strong> always <strong>been</strong> hard to test </li></ul>'
        self.assertEqual(self.f_en.to_html(), html)
        html = '<ul><li>Dit <strong>is</strong> altijd moeilijk te testen <strong>geweest</strong> </li></ul>'
        self.assertEqual(self.f_nl.to_html(), html)
