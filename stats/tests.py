import numpy as np


from annotations.test_models import BaseTestCase
from annotations.models import Alignment, Annotation, Label, LabelKey, Sentence, Fragment, Word, Tense, TenseCategory
from .models import Scenario, ScenarioLanguage
from .utils import run_mds


def label_symbol(label):
    return 'Label:{}'.format(label.id)


class ScenarioTenseTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.scenario = Scenario.objects.create(title='Test Scenario',
                                                description='Test Scenario', corpus=self.c1,)
        self.scenario.documents.add(self.d)
        self.scenario.save()

        l1 = ScenarioLanguage(scenario=self.scenario, language=self.en,
                              as_from=True, as_to=False, use_labels=True)
        l1.save()

        l2 = ScenarioLanguage(scenario=self.scenario, language=self.nl,
                              as_from=False, as_to=True, use_labels=True)
        l2.save()

        self.tense_category = TenseCategory.objects.create(title='Tense Category')
        self.tense_1 = Tense.objects.create(title='Source Tense', language=self.en, category=self.tense_category)
        self.tense_2 = Tense.objects.create(title='Target Tense', language=self.nl, category=self.tense_category)

        self.f_en.tense = self.tense_1
        self.f_en.save()
        self.annotation = Annotation.objects.create(alignment=self.alignment, tense=self.tense_2)
        self.annotation.save()

    def test_mds_single_point(self):
        run_mds(self.scenario)
        # expect one label per language
        self.assertEqual(self.scenario.mds_labels['en'], [('Tense:{}'.format(self.tense_1.id),)])
        self.assertEqual(self.scenario.mds_labels['nl'], [('Tense:{}'.format(self.tense_2.id),)])
        self.assertEqual(self.scenario.mds_model, [[0.0, 0.0, 0.0, 0.0, 0.0]])  # 5 dimensions by default


class ScenarioLabelsTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.scenario = Scenario.objects.create(
            title='Test Scenario', description='Test Scenario',
            corpus=self.c1,
        )
        self.scenario.documents.add(self.d)
        self.scenario.save()

        self.l1 = ScenarioLanguage(
            scenario=self.scenario, language=self.en,
            as_from=True, as_to=False,
            use_labels=True
        )
        self.l1.save()

        self.l2 = ScenarioLanguage(
            scenario=self.scenario, language=self.nl,
            as_from=False, as_to=True,
            use_labels=True
        )
        self.l2.save()

        self.label_key = LabelKey.objects.create(title='Label Key')
        self.label_key.corpora.add(self.c1)
        self.label_1 = Label.objects.create(title='Label1 (en)', key=self.label_key)
        self.label_2 = Label.objects.create(title='Label2 (nl)', key=self.label_key)

        # assign label to fragment
        self.f_en.labels.add(self.label_1)
        # create annotation with label
        self.annotation = Annotation.objects.create(alignment=self.alignment)
        self.annotation.labels.add(self.label_2)
        self.annotation.save()

    def make_fragment(self, text, language, target_word, label=None, xml_id='en1'):
        fragment = Fragment.objects.create(language=language, document=self.d)
        if label:
            fragment.labels.add(label)
        s = Sentence.objects.create(xml_id=xml_id, fragment=fragment)
        for n, w in enumerate(text.split()):
            is_target = w == target_word
            xml_id = 'w1.1.{}'.format(n + 1)
            Word.objects.create(word=w, xml_id=xml_id, is_target=is_target, sentence=s)
        return fragment

    def make_annotation_with_alignment(self, original, translated, label):
        alignment = Alignment.objects.create(
            original_fragment=original,
            translated_fragment=translated,
        )
        annotation = Annotation.objects.create(alignment=alignment)
        annotation.labels.add(label)
        return annotation

    def test_mds_single_point(self):
        run_mds(self.scenario)
        # expect one label per language
        self.assertEqual(self.scenario.mds_labels['en'], [('Label:{}'.format(self.label_1.id),)])
        self.assertEqual(self.scenario.mds_labels['nl'], [('Label:{}'.format(self.label_2.id),)])
        self.assertEqual(self.scenario.mds_model, [[0.0, 0.0, 0.0, 0.0, 0.0]])  # 5 dimensions by default

    def test_mds_two_points(self):
        label_3 = Label.objects.create(title='Label3 (nl)', key=self.label_key)

        self.make_annotation_with_alignment(
            self.make_fragment('Another sentence', self.en, 'sentence', self.label_1),
            self.make_fragment('Nog een zin', self.nl, 'zin'),
            label_3).save()

        run_mds(self.scenario)
        # original fragments both have the same label
        self.assertEqual(self.scenario.mds_labels['en'], [('Label:{}'.format(self.label_1.id),)] * 2)
        # translated fragments have two different labels
        self.assertEqual(self.scenario.mds_labels['nl'], [('Label:{}'.format(self.label_2.id),),
                                                          ('Label:{}'.format(label_3.id),)])

        points = [np.array(x) for x in self.scenario.mds_model]
        self.assertAlmostEqual(np.linalg.norm(points[0] - points[1]), 0.5, places=2)

    def test_mds_two_points_multiple_target_labels(self):
        second_key = LabelKey.objects.create(title='Second Label Key')
        second_key.corpora.add(self.c1)
        label_3 = Label.objects.create(title='Label3 (nl)', key=second_key)
        label_4 = Label.objects.create(title='Label4 (nl)', key=second_key)

        self.annotation.labels.add(label_3)
        self.annotation.save()

        annotation = self.make_annotation_with_alignment(
            self.make_fragment('Another sentence', self.en, 'sentence', self.label_1),
            self.make_fragment('Nog een zin', self.nl, 'zin'),
            self.label_2)
        annotation.labels.add(label_4)
        annotation.save()

        run_mds(self.scenario)

        # original fragments both have the same label
        self.assertEqual(self.scenario.mds_labels['en'], [(label_symbol(self.label_1),)] * 2)
        # translated fragments have two different paris of labels
        self.assertEqual(self.scenario.mds_labels['nl'], [(label_symbol(self.label_2), label_symbol(label_3)),
                                                          (label_symbol(self.label_2), label_symbol(label_4))])

        points = [np.array(x) for x in self.scenario.mds_model]
        self.assertAlmostEqual(np.linalg.norm(points[0] - points[1]), 0.5, places=2)

    def test_mds_label_filter(self):
        label_3 = Label.objects.create(title='Label3 (nl)', key=self.label_key)

        self.make_annotation_with_alignment(
            self.make_fragment('Another sentence', self.en, 'sentence', self.label_1),
            self.make_fragment('Nog een zin', self.nl, 'zin'),
            label_3).save()

        self.l2.include_labels.add(label_3)
        self.l2.save()

        run_mds(self.scenario)
        self.assertEqual(self.scenario.mds_labels['en'], [('Label:{}'.format(self.label_1.id),)])
        self.assertEqual(self.scenario.mds_labels['nl'], [('Label:{}'.format(label_3.id),)])

        points = [np.array(x) for x in self.scenario.mds_model]
        # after filtering we expect a single point
        self.assertEqual(len(points), 1)

    def test_mds_scenario_language_include_keys(self):
        second_key = LabelKey.objects.create(title='Second Label Key')
        second_key.corpora.add(self.c1)
        label_3 = Label.objects.create(title='Label3', key=second_key)
        label_4 = Label.objects.create(title='Label4', key=second_key)
        label_5 = Label.objects.create(title='Label5', key=self.label_key)

        self.f_en.labels.add(label_3)
        self.f_en.save()
        self.annotation.labels.add(label_4)
        self.annotation.save()

        # leaving ScenarioLangage.include_keys empty, all label keys should be used
        run_mds(self.scenario)
        # expecting a tuple of two labels
        self.assertEqual(len(self.scenario.mds_labels['nl'][0]), 2)

        # inlcuding only one LabelKey for nl, two for en
        self.l2.include_keys.clear()
        self.l2.include_keys.add(second_key)
        self.l2.save()
        run_mds(self.scenario)
        # expecting a tuple of two labels for en
        self.assertEqual(len(self.scenario.mds_labels['en'][0]), 2)
        # and a tuple of one label for nl
        self.assertEqual(len(self.scenario.mds_labels['nl'][0]), 1)

        # here we will filter by label without including the relevant label key
        annotation = self.make_annotation_with_alignment(
            self.make_fragment('Another sentence', self.en, 'sentence', self.label_1),
            self.make_fragment('Nog een zin', self.nl, 'zin'), label_3)
        annotation.labels.add(label_5)
        annotation.save()

        self.l2.include_keys.clear()
        self.l2.include_keys.add(self.label_key)
        # first run without label filters
        self.l2.include_labels.clear()
        self.l2.save()
        run_mds(self.scenario)

        # nl now includes only one key (self.label_key)
        self.assertEqual(len(self.scenario.mds_labels['nl'][0]), 1)
        self.assertEqual(self.scenario.mds_labels['nl'], [('Label:2',), ('Label:5',)])

        # run again, filtering by label_3 whose key (second_key) is not in include_keys
        self.l2.include_labels.add(label_3)
        run_mds(self.scenario)

        self.assertEqual(len(self.scenario.mds_labels['nl'][0]), 1)
        # and there should be only one annotation, with labels 5 and 3, but only 5 is visible
        self.assertEqual(self.scenario.mds_labels['nl'], [('Label:5',)])
