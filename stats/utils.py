# -*- coding: utf-8 -*-

from __future__ import division

from collections import defaultdict
import os
import pickle

import numpy as np
from sklearn import manifold

from .models import ScenarioLanguage
from annotations.models import Tense, Fragment, Annotation


def languages_by_scenario(scenario, **kwargs):
    return ScenarioLanguage.objects.filter(scenario=scenario, **kwargs)


def run_mds(scenario):
    corpus = scenario.corpus
    languages_from = languages_by_scenario(scenario, as_from=True)
    languages_to = languages_by_scenario(scenario, as_to=True)

    # For each Fragment, get the tenses
    fragment_ids = []
    tenses = defaultdict(list)
    for language_from in languages_from:

        fragments = Fragment.objects.filter(document__corpus=corpus, language=language_from.language)
        if language_from.tenses.exists():
            fragments = fragments.filter(tense__in=language_from.tenses.all())

        for fragment in fragments:
            annotations = Annotation.objects.none()

            # Retrieve the Annotations for this Fragment...
            for language_to in languages_to:
                a = Annotation.objects \
                    .exclude(tense=None) \
                    .filter(is_no_target=False, is_translation=True,
                            alignment__original_fragment=fragment,
                            alignment__translated_fragment__language=language_to.language)

                if language_to.tenses.exists():
                    a = a.filter(tense__in=language_to.tenses.all())

                annotations |= a

            # ... but only allow Fragments that have Alignments in all languages
            if annotations.count() == len(languages_to):
                fragment_ids.append(fragment.id)
                tenses[fragment.language.iso].append(get_tense(fragment))
                for annotation in annotations:
                    tenses[annotation.alignment.translated_fragment.language.iso].append(annotation.tense.pk)

    print tenses.values()

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

    # Perform Multidimensional Scaling
    matrix = np.array(matrix)
    mds = manifold.MDS(n_components=scenario.mds_dimensions, dissimilarity='precomputed')
    pos = mds.fit_transform(matrix)

    # Pickle the created objects
    plots_dir = 'plots'
    if not os.path.exists(plots_dir):
        os.makedirs(plots_dir)

    pre = '{}/{}_'.format(plots_dir, scenario.pk)
    pickle.dump(matrix, open(pre + 'matrix.p', 'wb'))
    pickle.dump(pos.tolist(), open(pre + 'model.p', 'wb'))
    pickle.dump(fragment_ids, open(pre + 'fragments.p', 'wb'))
    pickle.dump(tenses, open(pre + 'tenses.p', 'wb'))


def get_tense(fragment):
    if fragment.tense:
        return fragment.tense.pk
    elif fragment.language.iso == 'en':
        return Tense.objects.get(title=u'present perfect').pk
    elif fragment.language.iso == 'fr':
        return Tense.objects.get(title=u'passé composé').pk
    else:
        return None


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
