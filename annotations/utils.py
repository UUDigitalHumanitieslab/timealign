# -*- coding: utf-8 -*-

from django.db.models import Count

from .models import Corpus, Tense, Alignment, Annotation


def get_random_alignment(user, language_from, language_to):
    """
    Retrieves a random Alignment from the database.
    :param user: The current User
    :param language_from: The source language
    :param language_to: The target language
    :return: A random Alignment object
    """
    alignments = Alignment.objects.filter(original_fragment__language=language_from,
                                          translated_fragment__language=language_to,
                                          annotation=None)

    alignments = alignments.filter(original_fragment__document__corpus__in=get_available_corpora(user))

    return alignments.order_by('?').first()


def get_available_corpora(user):
    """
    Returns the available Corpora for a User.
    A staff user can see data from all corpora, other users are limited to corpora where they are an annotator.
    :param user: The current User
    :return: The available Corpora for this User
    """
    if user.is_staff:
        return Corpus.objects.all()
    else:
        return user.corpus_set.all()


def get_color(tense):
    """
    This function maps a tense on a color from the d3 color scale.
    See https://github.com/d3/d3-3.x-api-reference/blob/master/Ordinal-Scales.md#categorical-colors for details.
    TODO: create a Tense model and save this stuff there.
    :param tense: The given tense
    :return: A color from the d3 color scale
    """
    if tense in [u'Perfekt', u'present perfect', u'pretérito perfecto compuesto', u'passé composé', u'vtt',
                 u'passato prossimo', u'PresPerf']:
        return '#1f77b4'
    elif tense in [u'Präsens', u'simple present', u'presente', u'présent', u'ott', u'Present']:
        return '#ff7f0e'
    elif tense in [u'Präteritum', u'simple past', u'pretérito perfecto simple', u'indefinido', u'passé simple', u'ovt', u'Past']:
        return '#2ca02c'
    elif tense in [u'Plusquamperfekt', u'past perfect', u'pretérito pluscuamperfecto', u'plus-que-parfait', u'vvt',
                   u'trapassato prossimo', u'PastPerf']:
        return '#d62728'
    elif tense in [u'Futur I', u'simple future', u'futur', u'futuro', u'ottt']:
        return '#9467bd'
    elif tense in [u'Futur II', u'future perfect', u'futur antérieur', u'futuro perfecto', u'ovtt']:
        return '#8c564b'
    elif tense in [u'present perfect continuous', u'Cont']:
        return '#e377c2'
    elif tense in [u'pasado reciente', u'passé récent', u'RecentPast']:
        return '#7f7f7f'
    elif tense in [u'pretérito imperfecto', u'imparfait', u'Imperfecto']:
        return '#bcbd22'
    elif tense in [u'present participle', u'participio', u'Gerund']:
        return '#17becf'
    elif tense in [u'Infinitiv', u'infinitief', u'infinitif', u'infinitivo']:
        return '#aec7e8'
    elif tense in [u'present continuous', u'PresGer']:
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
        return '#cedb9c'

    elif tense in [u'unmarked']:
        return '#1f77b4'
    elif tense in [u'rvc']:
        return '#ff7f0e'
    elif tense in [u'le1']:
        return '#2ca02c'
    elif tense in [u'le12']:
        return '#d62728'
    elif tense in [u'guo']:
        return '#9467bd'
    elif tense in [u'zhe']:
        return '#8c564b'
    elif tense in [u'zai']:
        return '#e377c2'

    else:
        return ''

def get_distinct_tenses(language):
    """
    Returns distinct tenses for a language, sorting them by most frequent.
    :param language: The given Language
    :return: A list of tenses
    """
    most_frequent_by_language = Annotation.objects \
        .filter(alignment__translated_fragment__language=language) \
        .exclude(tense__exact='') \
        .values('tense') \
        .annotate(Count('tense')) \
        .order_by('-tense__count')
    return Tense.objects.filter(pk__in=[t.get('tense') for t in most_frequent_by_language])


def get_tenses(language):
    """
    Returns tenses for a language.
    TODO: create a Tense model and save this stuff there.
    :param language: The given Language
    :return: A list of tenses
    """
    if language.iso == 'fr':
        return [u'conditionnel',
                u'conditionnel passé',
                u'futur',
                u'futur antérieur',
                u'futur proche',
                u'futur proche du passé',
                u'imparfait',
                u'passé composé',
                u'passé récent',
                u'passé récent du passé',
                u'passé simple',
                u'plus-que-parfait',
                u'présent',
                u'other']
    else:
        return [t.get('tense') for t in get_distinct_tenses(language)]
