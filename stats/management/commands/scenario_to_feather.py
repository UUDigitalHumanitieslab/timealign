# -*- coding: utf-8 -*-
import pandas as pd
import pyarrow.feather as feather

from django.core.management.base import BaseCommand, CommandError

from annotations.models import TenseCategory
from stats.models import Scenario
from stats.utils import prepare_label_cache, get_label_properties_from_cache


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

        # Write a file with the matrix
        filename = 's{}-matrix.feather'.format(scenario.pk)
        export_matrix(filename, scenario)

        # Write a file with the TenseCategory labels and colors
        filename = 'tensecats.feather'
        export_tensecats(filename)

        # Write a file with the fragments and their labels
        filename = 's{}-labels.feather'.format(scenario.pk)
        export_fragments(filename, scenario)


def export_matrix(filename, scenario):
    mds_matrix = scenario.mds_matrix
    df = pd.DataFrame(data=mds_matrix)
    feather.write_feather(df, filename, compression='uncompressed')


def export_tensecats(filename):
    tc_titles = []
    tc_colors = []
    for title, color in TenseCategory.objects.values_list('title', 'color'):
        tc_titles.append(title)
        tc_colors.append(color)
    df = pd.DataFrame({'title': tc_titles, 'color': tc_colors})
    feather.write_feather(df, filename, compression='uncompressed')


def export_fragments(filename, scenario):
    fragment_pks = scenario.mds_fragments
    scenario_labels = scenario.get_labels()
    df = pd.DataFrame({'fragment_pks': fragment_pks})
    cache = prepare_label_cache(scenario.corpus)
    for sl in scenario.languages().all():
        labels = []
        colors = []
        cats = []
        for scenario_label in scenario_labels[sl.language.iso]:
            label, color, category = get_label_properties_from_cache(scenario_label, cache, len(set(labels)))
            labels.append(label)
            colors.append(color)
            cats.append(category)

        df[sl.language.iso + '-label'] = labels
        df[sl.language.iso + '-color'] = colors
        df[sl.language.iso + '-cat'] = cats
    feather.write_feather(df, filename, compression='uncompressed')
