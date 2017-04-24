# -*- coding: utf-8 -*-

from django.db.models import Count

from .models import Corpus, Alignment, Annotation


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
    if tense in [u'Perfekt', u'present perfect', u'pretérito perfecto compuesto', u'passé composé', u'vtt']:
        return '#1f77b4'
    elif tense in [u'Präsens', u'simple present', u'presente', u'présent', u'ott']:
        return '#ff7f0e'
    elif tense in [u'Präteritum', u'simple past', u'pretérito perfecto simple', u'ovt']:
        return '#2ca02c'
    elif tense in [u'Plusquamperfekt', u'past perfect', u'pretérito pluscuamperfecto', u'plus-que-parfait', u'vvt']:
        return '#d62728'
    elif tense in [u'Futur I', u'futur antérieur']:
        return '#9467bd'
    elif tense in [u'Futur II']:
        return '#8c564b'
    elif tense in [u'present perfect continuous']:
        return '#e377c2'
    elif tense in [u'pasado reciente', u'passé récent']:
        return '#7f7f7f'
    elif tense in [u'pretérito imperfecto', u'imparfait']:
        return '#bcbd22'
    elif tense in [u'present participle', u'participio']:
        return '#17becf'
    elif tense in [u'infinitief']:
        return '#aec7e8'
    else:
        return ''


def get_distinct_tenses(language):
    """
    Returns distinct tenses for a language, sorting them by most frequent.
    :param language: The given Language
    :return: A list of tenses
    """
    return Annotation.objects \
        .filter(alignment__translated_fragment__language=language) \
        .exclude(tense__exact='') \
        .values('tense') \
        .annotate(Count('tense')) \
        .order_by('-tense__count')


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
