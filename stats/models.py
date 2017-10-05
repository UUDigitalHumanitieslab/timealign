from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from annotations.models import Language, Tense, Corpus, Document


class Scenario(models.Model):
    title = models.CharField(max_length=200)
    corpus = models.ForeignKey(Corpus)
    #documents = models.ManyToManyField(Document)
    mds_dimensions = models.PositiveIntegerField(
        'Number of dimensions',
        validators=[MinValueValidator(2), MaxValueValidator(5)],
        help_text='Number of dimensions to use in Multidimensional Scaling. Should be between 2 and 5.'
    )

    last_run = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        return self.title


class ScenarioLanguage(models.Model):
    scenario = models.ForeignKey(Scenario)

    language = models.ForeignKey(Language)
    as_from = models.BooleanField()
    as_to = models.BooleanField()
    tenses = models.ManyToManyField(Tense, blank=True)

    use_other_label = models.BooleanField(default=False)  # if the Tense of a Fragment/Annotation is not used for the language

    def __unicode__(self):
        return u'Details for language {} in scenario {}'.format(self.language.title, self.scenario.title)
