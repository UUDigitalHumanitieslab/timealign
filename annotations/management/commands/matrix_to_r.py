# -*- coding: utf-8 -*-
import pickle

import rpy2.robjects as robjects
from rpy2.robjects import numpy2ri
numpy2ri.activate()

from django.core.management.base import BaseCommand, CommandError

from annotations.models import Corpus

class Command(BaseCommand):
    help = 'Exports the matrix in R format'

    def add_arguments(self, parser):
        parser.add_argument('corpus', type=str)

    def handle(self, *args, **options):
        try:
            corpus = Corpus.objects.get(title=options['corpus'])
        except Corpus.DoesNotExist:
            raise CommandError('Corpus with title {} does not exist'.format[options['corpus']])        

        pre = 'plots/{}_'.format(corpus.pk)
        matrix = pickle.load(open(pre + 'matrix.p', 'rb'))
        fragment_ids = pickle.load(open(pre + 'fragments.p', 'rb'))

        r_matrix = robjects.r.matrix(matrix)
        r_matrix.colnames = robjects.StrVector(fragment_ids)
        
        robjects.assign('data', r_matrix)
        robjects.save('data', file='test.R')
