# -*- coding: utf-8 -*-

from __future__ import division

from collections import defaultdict
import pickle

import numpy as np
from sklearn import manifold
from sklearn.decomposition import PCA

from django.core.management.base import BaseCommand, CommandError

from annotations.models import Annotation, Fragment


class Command(BaseCommand):
    help = 'Exports a distance matrix of all (correct) annotations'

    def add_arguments(self, parser):
        parser.add_argument('corpus', type=str)

    def handle(self, *args, **options):
        # For each Fragment, get the tenses
        fragment_ids = []
        tenses = defaultdict(list)
        for fragment in Fragment.objects.filter(document__corpus__title=options['corpus']):
            # Retrieve the Annotations for this Fragment...
            annotations = Annotation.objects \
                .exclude(tense='other') \
                .filter(is_no_target=False, is_translation=True,
                        alignment__original_fragment=fragment)
            # ... but only allow Fragments that have Alignments in all languages
            if annotations.count() == len(Fragment.LANGUAGES) - 1:
                fragment_ids.append(fragment.id)
                tenses[fragment.language].append(pp_name(fragment.language))
                for annotation in annotations:
                    tenses[annotation.alignment.translated_fragment.language].append(annotation.tense)

        # Create a list of lists with tenses for all languages
        tenses_matrix = defaultdict(list)
        for t in tenses.values():
            for n, tense in enumerate(t):
                tenses_matrix[n].append(tense)

        # Create a distance matrix
        matrix = []
        for t1 in tenses_matrix.values():
            result = []
            for t2 in tenses_matrix.values():
                result.append(get_distance(t1, t2))
            matrix.append(result)

        # Do a Multidimensional Scaling
        matrix = np.array(matrix)
        mds = manifold.MDS(n_components=5, dissimilarity='precomputed')
        pos = mds.fit_transform(matrix)

        # Pickle the created objects
        pickle.dump(pos.tolist(), open('matrix.p', 'wb'))
        pickle.dump(fragment_ids, open('fragments.p', 'wb'))
        pickle.dump(tenses, open('tenses.p', 'wb'))


def pp_name(language):
    if language == Fragment.ENGLISH:
        return u'present perfect'
    elif language == Fragment.GERMAN:
        return u'Perfekt'
    elif language == Fragment.DUTCH:
        return u'vtt'
    elif language == Fragment.SPANISH:
        return u'pretérito perfecto compuesto'
    elif language == Fragment.FRENCH:
        return u'passé composé'


def get_distance(array1, array2):
    result = 0
    total = 0

    for i in range(len(array1)):
        if not array1[i] or not array2[i]:
            continue

        if array1[i] == array2[i]:
            result += 1

        total += 1

    return 1 - round(result / total, 2) if total > 0 else 0
