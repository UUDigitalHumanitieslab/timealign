from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from annotations.models import Language, Corpus


class Scenario(models.Model):
    title = models.CharField(max_length=200)
    corpus = models.ForeignKey(Corpus)
    mds_dimensions = models.PositiveIntegerField(
        'Number of dimensions to use in Multidimensional Scaling',
        validators=[MinValueValidator(2), MaxValueValidator(5)])


class ScenarioLanguage(models.Model):
    scenario = models.ForeignKey(Scenario)
    language = models.ForeignKey(Language)
    as_from = models.BooleanField()
    as_to = models.BooleanField()
