from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from picklefield.fields import PickledObjectField

from annotations.models import Language, Tense, Corpus, Document, SubCorpus, Fragment


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

    formal_structure = models.PositiveIntegerField('Formal structure', choices=Fragment.FORMAL_STRUCTURES, default=Fragment.FS_NONE)
    formal_structure_strict = models.BooleanField('Require translations to be in the same formal structure', default=True)

    sentence_function = models.PositiveIntegerField('Sentence function', choices=Fragment.SENTENCE_FUNCTIONS, default=Fragment.SF_NONE)

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
        help_text='When enabled, the model will include tuples where one or more of the target languages have no Annotation')

    last_run = models.DateTimeField(blank=True, null=True)

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='scenarios', null=True, on_delete=models.SET_NULL)

    def from_languages(self):
        languages = self.languages_from if hasattr(self, 'languages_from') else self.languages(as_from=True)
        return ', '.join([sl.language.title for sl in languages])

    def to_languages(self):
        languages = self.languages_to if hasattr(self, 'languages_to') else self.languages(as_to=True)
        return ', '.join([sl.language.title for sl in languages])

    def languages(self, **kwargs):
        return self.scenariolanguage_set.filter(**kwargs).select_related('language')

    def __unicode__(self):
        return self.title


class ScenarioLanguage(models.Model):
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)

    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    as_from = models.BooleanField()
    as_to = models.BooleanField()
    tenses = models.ManyToManyField(Tense, blank=True)

    use_other_label = models.BooleanField(default=False)  # if the Tense of a Fragment/Annotation is not used for the language
    other_labels = models.CharField('Allowed labels, comma-separated', max_length=200, blank=True)

    def __unicode__(self):
        return u'Details for language {} in scenario {}'.format(self.language.title, self.scenario.title)
