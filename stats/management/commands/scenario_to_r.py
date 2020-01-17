# -*- coding: utf-8 -*-
from collections import defaultdict

import rpy2.robjects as robjects
from rpy2.robjects.packages import importr
from rpy2.robjects import numpy2ri
from rpy2.rlike import container

from django.core.management.base import BaseCommand, CommandError

from stats.models import Scenario
from stats.utils import get_tense_properties


numpy2ri.activate()


class Command(BaseCommand):
    help = 'Exports a Scenario in R format'

    def add_arguments(self, parser):
        parser.add_argument('scenario', type=int)

    def handle(self, *args, **options):
        # Retrieve the Scenario from the database
        try:
            scenario = Scenario.objects.get(pk=options['scenario'])
        except Scenario.DoesNotExist:
            raise CommandError('Scenario with title {} does not exist'.format(options['scenario']))

        # Retrieve the pickled data
        mds_matrix = scenario.mds_matrix
        fragment_ids = scenario.mds_fragments
        tenses = scenario.mds_labels

        # Assign the pickled data to R variables
        robjects.r.assign('scenario_title', scenario.title)
        robjects.r.assign('scenario_description', scenario.description)
        robjects.r.assign('mds_matrix', mds_matrix)
        robjects.r.assign('fragment_ids', robjects.StrVector(fragment_ids))

        categories = defaultdict(list)
        for sl in scenario.languages().all():
            labels = []
            colors = []
            for tense in tenses[sl.language.iso]:
                label, color, category = get_tense_properties(tense, len(set(labels)))
                labels.append(label)
                colors.append(color)
                print(tense)
                categories[sl.language.iso].append(category)

            robjects.r.assign('labels_{}'.format(sl.language.iso), robjects.StrVector(labels))
            robjects.r.assign('colors_{}'.format(sl.language.iso), robjects.StrVector(colors))

        language_keys = [language.language.iso for language in scenario.languages().all()]
        df = container.OrdDict(
            [('fragment_id', robjects.StrVector(fragment_ids))] +
            [(language, robjects.StrVector(tenses[language])) for language in language_keys])
        robjects.r.assign('df', robjects.DataFrame(df))
        df_cat = container.OrdDict(
            [('fragment_id', robjects.StrVector(fragment_ids))] +
            [(language, robjects.StrVector(categories[language])) for language in language_keys])
        robjects.r.assign('df_cat', robjects.DataFrame(df_cat))

        # Save the workspace
        filename = 's{}.RData'.format(scenario.pk)
        base = importr('base')
        base.save_image(file=filename)
