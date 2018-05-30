# -*- coding: utf-8 -*-

from __future__ import division

import numbers
from collections import defaultdict

import numpy as np
from sklearn import manifold

from django.db.models import Q

from annotations.models import Fragment, Annotation, Tense


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


def get_tense_properties(tense_identifier, seq=0):
    if isinstance(tense_identifier, numbers.Number):
        tense = Tense.objects.get(pk=tense_identifier)
        tense_label = tense.title
        tense_color = tense.category.color
    else:
        tense_label = tense_identifier
        tense_color = get_color(tense_identifier, seq)
    return tense_label, tense_color


def get_color(tense, seq=0):
    """
    This function maps a tense on a color from the d3 color scale.
    See https://github.com/d3/d3-3.x-api-reference/blob/master/Ordinal-Scales.md#categorical-colors for details.
    TODO: create a Tense model and save this stuff there.
    :param tense: The given tense
    :param seq: The current sequence number
    :return: A color from the d3 color scale
    """
    if tense in [u'Perfekt', u'present perfect', u'pretérito perfecto compuesto', u'passé composé', u'vtt',
                 u'passato prossimo', u'PresPerf']:
        return '#1f77b4'
    elif tense in [u'Präsens', u'simple present', u'presente', u'présent', u'ott', u'Present', u'present imperfective', u'present']:
        return '#ff7f0e'
    elif tense in [u'Präteritum', u'simple past', u'pretérito perfecto simple', u'indefinido', u'passé simple', u'ovt', u'Past', u'past perfective', u'past']:
        return '#2ca02c'
    elif tense in [u'Plusquamperfekt', u'past perfect', u'pretérito pluscuamperfecto', u'plus-que-parfait', u'vvt',
                   u'trapassato prossimo', u'PastPerf', u'past+infinitive']:
        return '#d62728'
    elif tense in [u'Futur I', u'simple future', u'futur', u'futuro', u'ottt', u'future']:
        return '#9467bd'
    elif tense in [u'Futur II', u'future perfect', u'futur antérieur', u'futuro perfecto', u'ovtt', u'future past']:
        return '#8c564b'
    elif tense in [u'present perfect continuous', u'Cont', u'present/adjective']:
        return '#e377c2'
    elif tense in [u'pasado reciente', u'passé récent', u'RecentPast', u'copular']:
        return '#7f7f7f'
    elif tense in [u'pretérito imperfecto', u'imparfait', u'Imperfecto', u'past imperfective', u'past+present']:
        return '#bcbd22'
    elif tense in [u'present participle', u'participio', u'Gerund', u'gerund', u'gerund perfective']:
        return '#17becf'
    elif tense in [u'Infinitiv', u'infinitief', u'infinitif', u'infinitivo', u'infinitive']:
        return '#aec7e8'
    elif tense in [u'present continuous', u'PresGer', u'existential']:
        return '#ffbb78'
    elif tense in [u'condicional', u'conditionnel', u'Rep']:
        return '#98df8a'
    elif tense in [u'past continuous']:
        return '#ff9896'
    elif tense in [u'past perfect continuous']:
        return '#c5b0d5'
    elif tense in [u'future continuous']:
        return '#c49c94'
    elif tense in [u'future in the past', u'futuro perfecto']:
        return '#f7b6d2'
    elif tense in [u'future in the past continuous']:
        return '#c7c7c7'
    elif tense in [u'infinitivo perfecto']:
        return '#dbdb8d'
    elif tense in [u'futur proche', u'futuro próximo']:
        return '#9edae5'
    elif tense in [u'futur proche du passé', u'futuro próximo en imperfecto']:
        return '#393b79'
    elif tense in [u'conditionnel passé']:
        return '#5254a3'
    elif tense in [u'subjuntivo presente']:
        return '#e7cb94'
    elif tense in [u'subjuntivo pretérito imperfecto']:
        return '#8c6d31'
    elif tense in [u'participle past perfective active']:
        return '#843c39'
    elif tense in [u'gerund imperfective']:
        return '#393b79'

    # Mandarin
    elif tense in [u'unmarked']:
        return '#1f77b4'
    elif tense in [u'rvc']:
        return '#ff7f0e'
    elif tense in [u'le1', u'le']:
        return '#2ca02c'
    elif tense in [u'le12']:
        return '#d62728'
    elif tense in [u'guo']:
        return '#9467bd'
    elif tense in [u'zhe']:
        return '#8c564b'
    elif tense in [u'zai']:
        return '#e377c2'
    elif tense in [u'unmarked duplication']:
        return '#7f7f7f'
    elif tense in [u'adv']:
        return '#bcbd22'
    elif tense in [u'adj']:
        return '#17becf'
    elif tense in [u'conj']:
        return '#aec7e8'
    elif tense in [u'mood']:
        return '#ffbb78'
    elif tense in [u'noun']:
        return '#98df8a'
    elif tense in [u'non-verb', u'other']:
        return '#ff9896'

    # ViB
    elif tense in [u'adjectif']:
        return '#e6194b'
    elif tense in [u'adverbe']:
        return '#3cb44b'
    elif tense in [u'article défini']:
        return '#ff0000'
    elif tense in [u'article défini pluriel']:
        return '#bf0000'
    elif tense in [u'article défini singulier']:
        return '#ff0051'
    elif tense in [u'article indéfini']:
        return '#ff8400'
    elif tense in [u'article indéfini pluriel']:
        return '#8c4800'
    elif tense in [u'article indéfini singulier']:
        return '#4c2800'
    elif tense in [u'déterminant défini pluriel']:
        return '#adb300'
    elif tense in [u'déterminant démonstratif']:
        return '#56bf00'
    elif tense in [u'déterminant indéfini']:
        return '#285900'
    elif tense in [u'déterminant possessif']:
        return '#00e686'
    elif tense in [u'expression']:
        return '#e377c2'
    elif tense in [u'nom commun']:
        return '#7f7f7f'
    elif tense in [u'nom propre']:
        return '#bcbd22'
    elif tense in [u'nom propre gén']:
        return '#dbdb8d'
    elif tense in [u'numéral']:
        return '#17becf'
    elif tense in [u'pronom démonstratif']:
        return '#5b008c'
    elif tense in [u'pronom indéfini']:
        return '#2200ff'
    elif tense in [u'pronom interrogatif']:
        return '#0058e6'
    elif tense in [u'pronom personnel']:
        return '#006773'
    elif tense in [u'pronom personnel adverbial']:
        return '#00331e'
    elif tense in [u'pronom relatif']:
        return '#285900'
    elif tense in [u'pronom réfléchi']:
        return '#00e686'

    else:
        color_list = [
            '#1f77b4',
            '#ff7f0e',
            '#2ca02c',
            '#d62728',
            '#9467bd',
            '#8c564b',
            '#e377c2',
            '#7f7f7f',
            '#bcbd22',
            '#17becf',
            '#aec7e8',
            '#ffbb78',
            '#98df8a',
            '#ff9896',
            '#c5b0d5',
            '#c49c94',
            '#f7b6d2',
            '#f7b6d2',
            '#dbdb8d',
            '#9edae5',
        ]
        return color_list[seq % len(color_list)]
