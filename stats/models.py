from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from picklefield.fields import PickledObjectField

from annotations.models import Language, Tense, Corpus, Document


class Scenario(models.Model):
    title = models.CharField(max_length=200)
    corpus = models.ForeignKey(Corpus)
    documents = models.ManyToManyField(Document, blank=True)

    mds_dimensions = models.PositiveIntegerField(
        'Number of dimensions',
        default=5,
        validators=[MinValueValidator(2), MaxValueValidator(5)],
        help_text='Number of dimensions to use in Multidimensional Scaling. Should be between 2 and 5.'
    )
    mds_model = PickledObjectField('MDS model', blank=True)
    mds_matrix = PickledObjectField('MDS matrix', blank=True)
    mds_fragments = PickledObjectField('MDS fragments', blank=True)
    mds_labels = PickledObjectField('MDS labels', blank=True)

    last_run = models.DateTimeField(blank=True, null=True)

    def from_languages(self):
        return ', '.join([sl.language.title for sl in self.languages(as_from=True)])

    def to_languages(self):
        return ', '.join([sl.language.title for sl in self.languages(as_to=True)])

    def languages(self, **kwargs):
        return ScenarioLanguage.objects.filter(scenario=self, **kwargs)

    def __unicode__(self):
        return self.title


class ScenarioLanguage(models.Model):
    scenario = models.ForeignKey(Scenario)

    language = models.ForeignKey(Language)
    as_from = models.BooleanField()
    as_to = models.BooleanField()
    tenses = models.ManyToManyField(Tense, blank=True)

    use_other_label = models.BooleanField(default=False)  # if the Tense of a Fragment/Annotation is not used for the language
    other_labels = models.CharField('Allowed labels, comma-separated', max_length=200, blank=True)

    def __unicode__(self):
        return u'Details for language {} in scenario {}'.format(self.language.title, self.scenario.title)
