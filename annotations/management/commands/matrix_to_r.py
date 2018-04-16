# -*- coding: utf-8 -*-
import rpy2.robjects as robjects
from rpy2.robjects.packages import importr
from rpy2.robjects import numpy2ri
from rpy2.rlike import container

from django.core.management.base import BaseCommand, CommandError

from stats.models import Scenario

numpy2ri.activate()


class Command(BaseCommand):
    help = 'Exports the distance matrix in R format'

    def add_arguments(self, parser):
        parser.add_argument('scenario', type=str)

    def handle(self, *args, **options):
        # Retrieve the Scenario from the database
        try:
            scenario = Scenario.objects.get(title=options['scenario'])
        except Scenario.DoesNotExist:
            raise CommandError('Scenario with title {} does not exist'.format(
                options['scenario']))

        # Retrieve the pickled data
        matrix = scenario.mds_matrix
        fragment_ids = scenario.mds_fragments
        tenses = scenario.mds_labels

        # Assign the pickled data to R variables
        robjects.r.assign('matrix', matrix)
        robjects.r.assign('fragment_ids', robjects.StrVector(fragment_ids))

        language_keys = [language.language.iso
                         for language in scenario.languages().all()]

        df = container.OrdDict(
            [('fragment_id', robjects.StrVector(fragment_ids))] +

            [(language, robjects.StrVector(tenses[language]))
             for language in language_keys])

        robjects.r.assign('df', robjects.DataFrame(df))

        # Save the workspace
        filename = '{}.RData'.format(scenario.title)
        base = importr('base')
        base.save_image(file=filename)
