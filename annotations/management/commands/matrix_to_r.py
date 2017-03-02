# -*- coding: utf-8 -*-
import pickle

import rpy2.robjects as robjects
from rpy2.robjects.packages import importr
from rpy2.robjects import numpy2ri

from django.core.management.base import BaseCommand, CommandError

from annotations.models import Corpus, Fragment

numpy2ri.activate()


class Command(BaseCommand):
    help = 'Exports the distance matrix in R format'

    def add_arguments(self, parser):
        parser.add_argument('corpus', type=str)

    def handle(self, *args, **options):
        # Retrieve the Corpus from the database
        try:
            corpus = Corpus.objects.get(title=options['corpus'])
        except Corpus.DoesNotExist:
            raise CommandError('Corpus with title {} does not exist'.format[options['corpus']])        

        # Retrieve the pickled data
        pre = 'plots/{}_'.format(corpus.pk)
        matrix = pickle.load(open(pre + 'matrix.p', 'rb'))
        fragment_ids = pickle.load(open(pre + 'fragments.p', 'rb'))
        tenses = pickle.load(open(pre + 'tenses.p', 'rb'))

        # Assign the pickled data to R variables
        robjects.r.assign('matrix', matrix)
        robjects.r.assign('fragment_ids', robjects.StrVector(fragment_ids))

        for language in corpus.languages:
            robjects.r.assign('tenses_{}'.format(language.iso), robjects.StrVector(tenses[language]))

        # Save the workspace
        filename = '{}.RData'.format(corpus.title)
        base = importr('base')
        base.save_image(file=filename)
