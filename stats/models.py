from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from picklefield.fields import PickledObjectField

from annotations.models import Language, Tense, Corpus, Document, SubCorpus, Fragment, Label, LabelKey
import constants


class Scenario(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    is_test = models.BooleanField(
        'Test scenario',
        default=False,
        help_text='Checking this box signals that the scenario should not be displayed in the standard overview.')

    corpus = models.ForeignKey(Corpus, on_delete=models.CASCADE)
    documents = models.ManyToManyField(Document, blank=True)
    subcorpora = models.ManyToManyField(SubCorpus, blank=True)

    formal_structure = models.PositiveIntegerField(
        'Formal structure', choices=Fragment.FORMAL_STRUCTURES, default=Fragment.FS_NONE)
    formal_structure_strict = models.BooleanField(
        'Require translations to be in the same formal structure', default=True)

    sentence_function = models.PositiveIntegerField(
        'Sentence function', choices=Fragment.SENTENCE_FUNCTIONS, default=Fragment.SF_NONE)

    mds_dimensions = models.PositiveIntegerField(
        'Number of dimensions',
        default=5,
        validators=[MinValueValidator(2), MaxValueValidator(5)],
        help_text='Number of dimensions to use in Multidimensional Scaling. Should be between 2 and 5.'
    )
    mds_model = PickledObjectField('MDS model', null=True)
    mds_matrix = PickledObjectField('MDS matrix', null=True)
    mds_fragments = PickledObjectField('MDS fragments', null=True)
    mds_labels = PickledObjectField('MDS labels', null=True)
    mds_stress = models.FloatField('MDS stress', null=True)
    mds_allow_partial = models.BooleanField(
        'Allow partial tuples in model', default=False,
        help_text='When enabled, the model will include tuples '
                  'where one or more of the target languages have no Annotation')

    last_run = models.DateTimeField(blank=True, null=True)

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='scenarios', null=True, on_delete=models.SET_NULL)

    def from_languages(self):
        languages = self.languages_from if hasattr(self, 'languages_from') else self.languages(as_from=True)
        return ', '.join([sl.language.title for sl in languages])

    def to_languages(self):
        languages = self.languages_to if hasattr(self, 'languages_to') else self.languages(as_to=True)
        return ', '.join([sl.language.title for sl in languages])

    def languages(self, **kwargs):
        # TODO bram: It is insufficient to solve the language limiting by only applying the following filter. When the languages is empty, the view might throw exception because it always expects at least one language. E.g. AttributeError at /stats/sankey/280/ 'NoneType' object has no attribute 'language'

        extended_kwargs = dict(**kwargs, language__in=constants.PUBLIC_LANGUAGES)
        return self.scenariolanguage_set.filter(**extended_kwargs).select_related('language')
        # return self.scenariolanguage_set.filter(**kwargs).select_related('language')

    def __str__(self):
        return self.title

    def get_labels(self):
        # format mds_labels in a way that works with the recent changes.
        # this prevents us from having to rerun all existing scenarios.
        result = dict()
        for language, values in self.mds_labels.items():
            if isinstance(values[0], int):
                result[language] = [('Tense:{}'.format(v),) for v in values]
            if isinstance(values[0], str):
                labels = []
                for v in values:
                    try:
                        # TODO: This generates a lot of queries! (only for old scenarios though)
                        keys = LabelKey.objects.filter(corpora=self.corpus)
                        label = Label.objects.get(key__in=keys, title=v)
                        labels.append(label)
                    except:  # If all else fails, just continue...
                        continue
                result[language] = [('Label:{}'.format(label.pk),) for label in labels]
            else:
                result[language] = values
        return result


class ScenarioLanguage(models.Model):
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)

    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    as_from = models.BooleanField()
    as_to = models.BooleanField()
    tenses = models.ManyToManyField(Tense, blank=True)

    use_tenses = models.BooleanField(default=True)

    use_labels = models.BooleanField(default=False)
    include_keys = models.ManyToManyField(
        LabelKey, blank=True, related_name='+',
        help_text='Keys selected here will be used as components of the fragment tuples.')
    include_labels = models.ManyToManyField(
        Label, blank=True, related_name='+',
        verbose_name='Filter by labels',
        help_text='Fragments will be included in the scenario only '
                  'when they are assigned one of the selected labels. Leave emtpy to include all fragments.')

    # backward compatibility
    @property
    def use_other_label(self):
        return self.use_labels

    def __str__(self):
        return 'Details for language {} in scenario {}'.format(self.language.title, self.scenario.title)
