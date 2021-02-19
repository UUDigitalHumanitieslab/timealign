# -*- coding: utf-8 -*-


import numbers
from collections import defaultdict

import numpy as np
from sklearn import manifold

from django.db.models import Q, Prefetch

from annotations.models import Fragment, Annotation, Tense, Label
from core.utils import COLOR_LIST


class EmptyScenario(Exception):
    pass


class ImproperScenario(Exception):
    pass


def run_mds(scenario):
    languages_from = scenario.languages(as_from=True).prefetch_related('tenses', 'include_keys', 'include_labels')
    languages_to = scenario.languages(as_to=True).prefetch_related('tenses', 'include_keys', 'include_labels')

    # For each Fragment, retrieve the labels per language (as key), using the same order as fragment_pks
    fragment_pks = []
    fragment_labels = defaultdict(list)

    for language_from in languages_from:
        # Retrieve the Fragments
        fragments = retrieve_fragments(scenario, language_from)

        # Retrieve the Annotations from all ScenarioLanguages (except when they are also used as from-language)
        languages_to_filtered = languages_to.exclude(language=language_from.language)
        annotations = retrieve_annotations(scenario, languages_to_filtered, fragments)

        # Retrieve the labels
        retrieve_labels(scenario, fragments, annotations, languages_to_filtered,
                        fragment_labels, fragment_pks, language_from)

    # If no from-languages are provided, call the same methods without this parameter
    if not languages_from:
        # Retrieve the Fragments
        fragments = retrieve_fragments(scenario)

        # Retrieve the Annotations from all ScenarioLanguages
        annotations = retrieve_annotations(scenario, languages_to, fragments)

        # Retrieve the labels
        retrieve_labels(scenario, fragments, annotations, languages_to,
                        fragment_labels, fragment_pks)

    # the following creates a transposed matrix of fragment_labels:
    # in fragment_labels we find a list of labels per language,
    # while labels_matrix stores the labels per fragment
    # for example:
    #
    # fragment_labels['en'] = [simple past, present perfect, future]
    # fragment_labels['fr'] = [imparfait, passé composé, futur]
    # becomes
    # labels_matrix[0] = [simple past, imparfait]
    # labels_matrix[1] = [present perfect, passé composé]
    # labels_matrix[2] = [future, futur]
    #
    # this then allows to calculate a distance measure for each item of labels_matrix

    labels_matrix = defaultdict(list)
    for language_labels in list(fragment_labels.values()):
        for n, label in enumerate(language_labels):
            labels_matrix[n].append(label)

    # Create a distance matrix
    matrix = []
    for labels_1 in list(labels_matrix.values()):
        result = []
        for labels_2 in list(labels_matrix.values()):
            result.append(get_distance(labels_1, labels_2))
        matrix.append(result)

    if len(matrix) == 0:
        raise EmptyScenario()

    # Perform Multidimensional Scaling, keep the settings as close to the SMACOF implementation in R
    mds = manifold.MDS(n_components=scenario.mds_dimensions,
                       dissimilarity='precomputed',
                       n_init=1, max_iter=1000, eps=1e-6)
    matrix = np.array(matrix)
    pos = mds.fit_transform(matrix)

    # Pickle the created objects
    scenario.mds_matrix = matrix
    scenario.mds_fragments = fragment_pks
    scenario.mds_labels = fragment_labels

    # Normalize stress as per https://stackoverflow.com/a/47501135
    scenario.mds_stress = np.nan_to_num(np.sqrt(mds.stress_ / ((matrix.ravel() ** 2).sum() / 2)))

    # Pickle the model. Rounding here helps cluster points which are very close,
    # and also prevents loss of accuracy from serialization and deserialization of numpy arrays
    scenario.mds_model = pos.round(3).tolist()

    scenario.save()


def retrieve_fragments(scenario, language_from=None):
    # Fetch all Fragments, filter on Corpus and Language, prefetch Language, Tense, and Labels
    if language_from and language_from.include_keys.all():
        filtered_labels = Label.objects.filter(key__in=language_from.include_keys.all())
    else:
        filtered_labels = Label.objects.all()
    fragments = Fragment.objects \
        .filter(document__corpus=scenario.corpus) \
        .select_related('language', 'tense') \
        .prefetch_related(Prefetch('labels', queryset=filtered_labels, to_attr='labels_prefetched'))

    # Filter on the from-language (if set)
    if language_from:
        fragments = fragments.filter(language=language_from.language)

    # Filter on Documents (if selected)
    if scenario.documents.exists():
        fragments = fragments.filter(document__in=scenario.documents.all())

    # Filter on SubCorpora (if selected)
    if scenario.subcorpora.exists():
        for subcorpus in scenario.subcorpora.all():
            fragments = fragments.filter(pk__in=subcorpus.get_fragments())

    # Filter on formal structure (if selected)
    if scenario.formal_structure != Fragment.FS_NONE:
        fragments = fragments.filter(formal_structure=scenario.formal_structure)

    # Filter on sentence function (if selected)
    if scenario.sentence_function != Fragment.SF_NONE:
        fragments = fragments.filter(sentence_function=scenario.sentence_function)

    # Filter on Tenses (if selected)
    if language_from and language_from.use_tenses and language_from.tenses.exists():
        fragments = fragments.filter(tense__in=language_from.tenses.all())

    # Filter on Labels (if selected)
    if language_from and language_from.use_labels and language_from.include_labels.exists():
        fragments = fragments.filter(labels__in=language_from.include_labels.all())

    return fragments


def retrieve_annotations(scenario, languages_to, fragments):
    result = Annotation.objects.none()
    for language_to in languages_to:
        # Fetch the correct Annotations per Language, prefetch Fragment, Language, Tense, and Labels
        if language_to.include_keys.all():
            filtered_labels = Label.objects.filter(key__in=language_to.include_keys.all())
        else:
            filtered_labels = Label.objects.all()
        annotations = Annotation.objects \
            .exclude(Q(tense=None) & Q(labels=None)) \
            .filter(is_no_target=False, is_translation=True) \
            .filter(alignment__original_fragment__in=fragments) \
            .filter(alignment__translated_fragment__language=language_to.language) \
            .select_related('alignment__original_fragment',
                            'alignment__translated_fragment__language',
                            'tense') \
            .prefetch_related(Prefetch('labels', queryset=filtered_labels, to_attr='labels_prefetched'))

        # Filter on formal structure (if selected)
        if scenario.formal_structure != Fragment.FS_NONE and scenario.formal_structure_strict:
            annotations = annotations.filter(is_not_same_structure=False)

        # Filter on Tenses (if selected)
        if language_to.use_tenses and language_to.tenses.exists():
            annotations = annotations.filter(~Q(alignment__translated_fragment__language=language_to.language) |
                                             Q(tense__in=language_to.tenses.all()))

        # Filter on labels (if selected)
        if language_to.use_labels and language_to.include_labels.exists():
            annotations = annotations.filter(~Q(alignment__translated_fragment__language=language_to.language) |
                                             Q(labels__in=language_to.include_labels.all()))

        result |= annotations

    return result


def retrieve_labels(scenario, fragments, annotations, languages_to, fragment_labels, fragment_pks, language_from=None):
    # Create a dict of Fragment -> Annotations for lookup in the for-loop below
    annotations_dict = defaultdict(list)
    for annotation in annotations:
        annotations_dict[annotation.alignment.original_fragment.pk].append(annotation)

    # For every Fragment, retrieve the Annotations and its labels
    for fragment in fragments:
        fragment_annotations = annotations_dict.get(fragment.pk)
        if not fragment_annotations:
            # No Annotations at all, skip Fragment
            continue

        # Compile a list of Annotations...
        annotated_labels = dict()
        for language_to in languages_to:
            language_annotations = []
            for fa in fragment_annotations:
                if fa.alignment.translated_fragment.language == language_to.language:
                    language_annotations.append(fa)

            if language_annotations:
                # TODO: For now, we only have one Annotation per Fragment. This might change in the future.
                a = language_annotations[0]
                a_language = language_to.language.iso
                a_label = get_labels(a, language_to)
                if a_label:
                    annotated_labels[a_language] = a_label

        # ... but only allow Fragments that have Annotations in all languages
        # unless the scenario allows partial tuples.
        if scenario.mds_allow_partial or len(annotated_labels) == len(languages_to):
            fragment_pks.append(fragment.pk)

            # store label of source language
            if language_from:
                from_labels = get_labels(fragment, language_from)
                fragment_labels[fragment.language.iso].append(from_labels)

            # store label(s) of target language(s)
            for language in languages_to:
                key = language.language.iso
                fragment_labels[key].append(annotated_labels.get(key))


def get_labels(model, scenario_language):
    return model.get_labels(as_pk=True,
                            include_tense=scenario_language.use_tenses,
                            include_labels=scenario_language.use_labels,
                            include_keys=scenario_language.include_keys.all())


def get_distance(array1, array2):
    result = 0
    total = 0

    if len(array1) != len(array2):
        raise ImproperScenario()

    for i in range(len(array1)):
        if not array1[i] or not array2[i]:
            continue

        if array1[i] == array2[i]:
            result += 1

        total += 1

    return 1 - round(result / total, 2) if total > 0 else 0


def copy_scenario(request, scenario):
    # Save relationships
    corpus = scenario.corpus
    documents = scenario.documents.all()
    subcorpora = scenario.subcorpora.all()
    scenario_languages = scenario.scenariolanguage_set.all()

    # Create a copy
    copy_scenario = scenario
    copy_scenario.pk = None

    # Amend title and owner
    copy_scenario.title = scenario.title + '-copy'
    copy_scenario.owner = request.user

    # Empty MDS fields
    copy_scenario.mds_model = None
    copy_scenario.mds_matrix = None
    copy_scenario.mds_fragments = None
    copy_scenario.mds_labels = None
    copy_scenario.mds_stress = None
    copy_scenario.last_run = None
    copy_scenario.save()

    # Add references
    copy_scenario.corpus = corpus
    copy_scenario.documents.set(documents)
    copy_scenario.subcorpora.set(subcorpora)
    copy_scenario.save()

    # Copy linked models
    for scenario_language in scenario_languages:
        copy_scenario_language(copy_scenario, scenario_language)

    return copy_scenario


def copy_scenario_language(scenario, scenario_language):
    # Save relationships
    language = scenario_language.language
    tenses = scenario_language.tenses.all()

    # Create a copy
    copy_sl = scenario_language
    copy_sl.pk = None
    copy_sl.scenario = scenario
    copy_sl.save()

    # Add references
    copy_sl.language = language
    copy_sl.tenses.set(tenses)
    copy_sl.save()


def get_label_properties(identifier, seq=0, allow_empty=False):
    """
    Fetches properties for a Tense identifier.
    For integers, this method finds the label, color and TenseCategory label.
    For strings, this method generates a color based on a sequence number.
    NOTE: Usually, one should not call this method directly, rather use get_tense_properties_from_cache below.
    :param identifier: identifier of the Tense/Label, int or string
    :param seq: current sequence number of assigned colors (for strings)
    :param allow_empty: allow #000000 (black) as color instead of an assigned color
    :return: label, color, and category for the given tense identifier
    """
    if not identifier:
        label = '-'
        color = '#000000'
        category = None
    elif isinstance(identifier, numbers.Number):
        tense = Tense.objects.select_related('category').get(pk=identifier)
        label = tense.title
        color = tense.category.color
        category = tense.category.title
    else:
        label = identifier
        color = '#000000' if allow_empty else get_color(identifier, seq)
        category = None
    return label, color, category


def get_label_properties_from_cache(identifier, label_cache, seq=0, allow_empty=False):
    """
    Fetches properties for a Tense identifier from a cache.
    For integers, this method finds the label, color and TenseCategory label.
    For strings, this method generates a color based on a sequence number.
    :param identifier: identifier of the Tense/Label, int or string
    :param label_cache: the current Tense/Label cache
    :param seq: current sequence number of assigned colors (for strings)
    :param allow_empty: allow #000000 (black) as color instead of an assigned color
    :return: label, color, and category for the given tense identifier
    """
    if isinstance(identifier, tuple) and len(identifier) == 1:
        identifier = identifier[0]

    if identifier in label_cache:
        label, color, category = label_cache[identifier]
    else:
        label, color, category = get_label_properties(identifier, seq, allow_empty)
        if isinstance(identifier, tuple):
            label = '<{}>'.format(','.join(label_cache[t][0] for t in identifier))
        label_cache[identifier] = (label, color, category)
    return label, color, category


def prepare_label_cache(corpus):
    """
    Prepares the Tense/Label cache for a Corpus that is used in get_label_properties_from_cache.
    :param corpus: The given Corpus.
    :return: A dictionary with label, colors and categories per label identifier.
    """
    cache = {'Tense:{}'.format(t.pk): (t.title, t.category.color, t.category.title)
             for t in Tense.objects.select_related('category')}
    for i, label in enumerate(Label.objects.filter(key__corpora=corpus)):
        color = label.color if label.color is not None else COLOR_LIST[i % len(COLOR_LIST)]
        cache['Label:{}'.format(label.pk)] = label.title, color, None
    return cache


def get_color(tense, seq=0):
    """
    This function maps a tense on a color from the d3 color scale.
    See https://github.com/d3/d3-3.x-api-reference/blob/master/Ordinal-Scales.md#categorical-colors for details.
    TODO: the string lookup has become obsolete now we have the Tense and LabelKey in place. Consider removing.
    :param tense: The given tense
    :param seq: The current sequence number
    :return: A color from the d3 color scale
    """
    if tense in ['Perfekt', 'present perfect', 'pretérito perfecto compuesto', 'passé composé', 'vtt',
                 'passato prossimo', 'PresPerf']:
        return '#1f77b4'
    elif tense in ['Präsens', 'simple present', 'presente', 'présent', 'ott', 'Present', 'present imperfective', 'present']:
        return '#ff7f0e'
    elif tense in ['Präteritum', 'simple past', 'pretérito perfecto simple', 'indefinido', 'passé simple', 'ovt', 'Past', 'past perfective', 'past']:
        return '#2ca02c'
    elif tense in ['Plusquamperfekt', 'past perfect', 'pretérito pluscuamperfecto', 'plus-que-parfait', 'vvt',
                   'trapassato prossimo', 'PastPerf', 'past+infinitive']:
        return '#d62728'
    elif tense in ['Futur I', 'simple future', 'futur', 'futuro', 'ottt', 'future']:
        return '#9467bd'
    elif tense in ['Futur II', 'future perfect', 'futur antérieur', 'futuro perfecto', 'ovtt', 'future past']:
        return '#8c564b'
    elif tense in ['present perfect continuous', 'Cont', 'present/adjective']:
        return '#e377c2'
    elif tense in ['pasado reciente', 'passé récent', 'RecentPast', 'copular']:
        return '#7f7f7f'
    elif tense in ['pretérito imperfecto', 'imparfait', 'Imperfecto', 'past imperfective', 'past+present']:
        return '#bcbd22'
    elif tense in ['present participle', 'participio', 'Gerund', 'gerund', 'gerund perfective']:
        return '#17becf'
    elif tense in ['Infinitiv', 'infinitief', 'infinitif', 'infinitivo', 'infinitive']:
        return '#aec7e8'
    elif tense in ['present continuous', 'PresGer', 'existential']:
        return '#ffbb78'
    elif tense in ['condicional', 'conditionnel', 'Rep']:
        return '#98df8a'
    elif tense in ['past continuous']:
        return '#ff9896'
    elif tense in ['past perfect continuous']:
        return '#c5b0d5'
    elif tense in ['future continuous']:
        return '#c49c94'
    elif tense in ['future in the past', 'futuro perfecto']:
        return '#f7b6d2'
    elif tense in ['future in the past continuous']:
        return '#c7c7c7'
    elif tense in ['infinitivo perfecto']:
        return '#dbdb8d'
    elif tense in ['futur proche', 'futuro próximo']:
        return '#9edae5'
    elif tense in ['futur proche du passé', 'futuro próximo en imperfecto']:
        return '#393b79'
    elif tense in ['conditionnel passé']:
        return '#5254a3'
    elif tense in ['subjuntivo presente']:
        return '#e7cb94'
    elif tense in ['subjuntivo pretérito imperfecto']:
        return '#8c6d31'
    elif tense in ['participle past perfective active']:
        return '#843c39'
    elif tense in ['gerund imperfective']:
        return '#393b79'

    # Mandarin
    elif tense in ['unmarked']:
        return '#1f77b4'
    elif tense in ['rvc']:
        return '#ff7f0e'
    elif tense in ['le1', 'le']:
        return '#2ca02c'
    elif tense in ['le12']:
        return '#d62728'
    elif tense in ['guo']:
        return '#9467bd'
    elif tense in ['zhe']:
        return '#8c564b'
    elif tense in ['zai']:
        return '#e377c2'
    elif tense in ['unmarked duplication']:
        return '#7f7f7f'
    elif tense in ['adv']:
        return '#bcbd22'
    elif tense in ['adj']:
        return '#17becf'
    elif tense in ['conj']:
        return '#aec7e8'
    elif tense in ['mood']:
        return '#ffbb78'
    elif tense in ['noun']:
        return '#98df8a'
    elif tense in ['non-verb', 'other']:
        return '#ff9896'

    # ViB
    elif tense in ['adjectif']:
        return '#e6194b'
    elif tense in ['adverbe']:
        return '#3cb44b'
    elif tense in ['article défini']:
        return '#ff0000'
    elif tense in ['article défini pluriel']:
        return '#bf0000'
    elif tense in ['article défini singulier']:
        return '#ff0051'
    elif tense in ['article indéfini']:
        return '#ff8400'
    elif tense in ['article indéfini pluriel']:
        return '#8c4800'
    elif tense in ['article indéfini singulier']:
        return '#4c2800'
    elif tense in ['déterminant défini pluriel']:
        return '#adb300'
    elif tense in ['déterminant démonstratif']:
        return '#56bf00'
    elif tense in ['déterminant indéfini']:
        return '#285900'
    elif tense in ['déterminant possessif']:
        return '#00e686'
    elif tense in ['expression']:
        return '#e377c2'
    elif tense in ['nom commun']:
        return '#7f7f7f'
    elif tense in ['nom propre']:
        return '#bcbd22'
    elif tense in ['nom propre gén']:
        return '#dbdb8d'
    elif tense in ['numéral']:
        return '#17becf'
    elif tense in ['pronom démonstratif']:
        return '#5b008c'
    elif tense in ['pronom indéfini']:
        return '#2200ff'
    elif tense in ['pronom interrogatif']:
        return '#0058e6'
    elif tense in ['pronom personnel']:
        return '#006773'
    elif tense in ['pronom personnel adverbial']:
        return '#00331e'
    elif tense in ['pronom relatif']:
        return '#285900'
    elif tense in ['pronom réfléchi']:
        return '#00e686'

    # Contraction
    elif tense in ['contracted', 'bare noun']:
        return '#2f5597'
    elif tense in ['uncontracted', 'demonstrative']:
        return '#fd8f8e'

    else:
        return COLOR_LIST[seq % len(COLOR_LIST)]
