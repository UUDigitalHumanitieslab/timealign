# -*- coding: utf-8 -*-
from collections import defaultdict

import rpy2.robjects as robjects
from rpy2.robjects.packages import importr
from rpy2.robjects import numpy2ri
from rpy2.rlike import container

from django.core.management.base import BaseCommand, CommandError

from annotations.models import TenseCategory
from stats.models import Scenario
from stats.utils import prepare_label_cache, get_label_properties_from_cache


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
        tenses = scenario.get_labels()

        # Assign the pickled data to R variables
        robjects.r.assign('scenario_title', scenario.title)
        robjects.r.assign('scenario_description', scenario.description)
        robjects.r.assign('mds_matrix', mds_matrix)
        robjects.r.assign('fragment_ids', robjects.StrVector(fragment_ids))

        cache = prepare_label_cache(scenario.corpus)

        categories = defaultdict(list)
        for sl in scenario.languages().all():
            labels = []
            colors = []
            cats = []
            for tense in tenses[sl.language.iso]:
                label, color, category = get_label_properties_from_cache(tense, cache, len(set(labels)))
                labels.append(label)
                colors.append(color)
                cats.append(category)
                categories[sl.language.iso].append(category)

            robjects.r.assign('labels_{}'.format(sl.language.iso), robjects.StrVector(labels))
            robjects.r.assign('colors_{}'.format(sl.language.iso), robjects.StrVector(colors))
            robjects.r.assign('categories_{}'.format(sl.language.iso), robjects.StrVector(cats))

        language_keys = [language.language.iso for language in scenario.languages().all()]
        df = container.OrdDict(
            [('fragment_id', robjects.StrVector(fragment_ids))] +
            [(language, robjects.StrVector(tenses[language])) for language in language_keys])
        robjects.r.assign('df', robjects.DataFrame(df))
        df_cat = container.OrdDict(
            [('fragment_id', robjects.StrVector(fragment_ids))] +
            [(language, robjects.StrVector(categories[language])) for language in language_keys])
        robjects.r.assign('df_cat', robjects.DataFrame(df_cat))

        tc_titles = []
        tc_colors = []
        for title, color in TenseCategory.objects.values_list('title', 'color'):
            tc_titles.append(title)
            tc_colors.append(color)
        tensecats = container.OrdDict(
            [('category', robjects.StrVector(tc_titles))] +
            [('colors', robjects.StrVector(tc_colors))]
        )
        robjects.r.assign('tensecats', robjects.DataFrame(tensecats))

        # Save the workspace
        filename = 's{}.RData'.format(scenario.pk)
        base = importr('base')
        base.save_image(file=filename)
