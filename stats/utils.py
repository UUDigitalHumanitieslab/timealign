# -*- coding: utf-8 -*-

from __future__ import division

from collections import defaultdict

import numpy as np
from sklearn import manifold

from django.db.models import Q

from annotations.models import Fragment, Annotation


def run_mds(scenario):
    corpus = scenario.corpus
    languages_from = scenario.languages(as_from=True)
    languages_to = scenario.languages(as_to=True)

    # For each Fragment, get the tenses
    fragment_ids = []

    # per language (as key) stores a list of tenses, using the same order as fragment_ids
    fragment_tenses = defaultdict(list)

    for language_from in languages_from:
        # Filter on Corpus and Language
        fragments = Fragment.objects.filter(document__corpus=corpus, language=language_from.language)

        # Filter on Documents (if selected)
        if scenario.documents.exists():
            fragments = fragments.filter(document__in=scenario.documents.all())

        # Filter on formal structure (if selected)
        if scenario.formal_structure != Fragment.FS_NONE:
            fragments = fragments.filter(formal_structure=scenario.formal_structure)

        # Filter on sentence function (if selected)
        if scenario.sentence_function != Fragment.SF_NONE:
            fragments = fragments.filter(sentence_function=scenario.sentence_function)

        # Filter on Tenses (if selected)
        if language_from.tenses.exists():
            fragments = fragments.filter(tense__in=language_from.tenses.all())

        # For every Fragment, retrieve the Annotations
        for fragment in fragments:
            annotated_tenses = dict()

            for language_to in languages_to:
                annotations = Annotation.objects \
                    .exclude(Q(tense=None) & Q(other_label='')) \
                    .filter(is_no_target=False, is_translation=True,
                            alignment__original_fragment=fragment,
                            alignment__translated_fragment__language=language_to.language)

                # Filter on Tenses
                if language_to.tenses.exists():
                    annotations = annotations.filter(tense__in=language_to.tenses.all())

                # Filter on other_labels
                if language_to.use_other_label and language_to.other_labels:
                    other_labels = language_to.other_labels.split(',')
                    annotations = annotations.filter(other_label__in=other_labels)

                # Filter on formal structure
                if scenario.formal_structure != Fragment.FS_NONE and scenario.formal_structure_strict:
                    annotations = annotations.filter(is_not_same_structure=False)

                # Compile a list of Annotations...
                if annotations:
                    a = annotations[0]  # TODO: For now, we only have one Annotation per Fragment. This might change in the future.
                    a_language = a.alignment.translated_fragment.language.iso
                    a_tense = get_tense(a, language_to)
                    if a_tense:
                        annotated_tenses[a_language] = a_tense

            # ... but only allow Fragments that have Annotations in all languages
            # unless the scenario allows partial tuples.
            if not annotated_tenses:
                # no annotations at all, skip fragment
                continue

            if (scenario.mds_allow_partial or
                    len(annotated_tenses) == len(languages_to)):
                fragment_ids.append(fragment.id)

                # store tense of source language
                fragment_tenses[fragment.language.iso].append(
                    get_tense(fragment, language_from))

                # store tenses of target languages
                for language in languages_to:
                #for l, t in annotated_tenses.items():
                    key = language.language.iso
                    fragment_tenses[key].append(annotated_tenses.get(key))

    # this creates a transposed matrix of fragment_tenses:
    # in fragment_tenses we find a list of tense labels per language,
    # while tenses_matrix stores the a of tense labels per fragment
    # for example:
    # (tenses are objects but for simplicity they are strings here)
    #
    # fragment_tenses['en'] = [simple past, present perfect, future]
    # fragment_tenses['fr'] = [imparfait, passé composé, futur]
    # becomes
    # tenses_matrix[0] = [simple past, imparfait]
    # tenses_matrix[1] = [present perfect, passé composé]
    # tenses_matrix[2] = [future, futur]
    #
    # this then allows to calculate a distance measure for each
    # item of tenses_matrix

    tenses_matrix = defaultdict(list)
    for language_tenses in fragment_tenses.values():
        for n, tense in enumerate(language_tenses):
            tenses_matrix[n].append(tense)

    # Create a distance matrix
    matrix = []
    for tense_set_1 in tenses_matrix.values():
        result = []
        for tense_set_2 in tenses_matrix.values():
            result.append(get_distance(tense_set_1, tense_set_2))
        matrix.append(result)

    # Perform Multidimensional Scaling
    matrix = np.array(matrix)
    mds = manifold.MDS(n_components=scenario.mds_dimensions, dissimilarity='precomputed')
    pos = mds.fit_transform(matrix)

    # Pickle the created objects
    scenario.mds_matrix = matrix
    scenario.mds_model = pos.tolist()
    scenario.mds_fragments = fragment_ids
    scenario.mds_labels = fragment_tenses
    scenario.mds_stress = mds.stress_
    scenario.save()


def get_tense(model, scenario_language):
    result = ''
    if scenario_language.use_other_label:
        if u'le-combine' in scenario_language.scenario.title and model.other_label in [u'le1', u'le12']:
            result = 'le'
        else:
            result = model.other_label
    elif model.tense:
        result = model.tense.pk
    return result


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
