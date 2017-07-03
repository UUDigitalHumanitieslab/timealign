from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from annotations.models import Language, Tense, Corpus, Document


class Scenario(models.Model):
    title = models.CharField(max_length=200)
    corpus = models.ForeignKey(Corpus)
    #documents = models.ManyToManyField(Document)
    mds_dimensions = models.PositiveIntegerField(
        'Number of dimensions to use in Multidimensional Scaling',
        validators=[MinValueValidator(2), MaxValueValidator(5)])

    def __unicode__(self):
        return self.title


class ScenarioLanguage(models.Model):
    scenario = models.ForeignKey(Scenario)

    language = models.ForeignKey(Language)
    as_from = models.BooleanField()
    as_to = models.BooleanField()
    tenses = models.ManyToManyField(Tense, blank=True)

    def __unicode__(self):
        return u'Details for language {} in scenario {}'.format(self.language.iso, self.scenario.title)
