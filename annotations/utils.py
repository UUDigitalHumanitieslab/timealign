# -*- coding: utf-8 -*-

from django.conf import settings

from .models import Alignment


def get_random_alignment(language_from, language_to):
    """
    Retrieves a random Alignment from the database.
    :param language_from: The source language
    :param language_to: The target language
    :return: A random Alignment object
    """
    alignments = Alignment.objects.filter(original_fragment__language=language_from,
                                          translated_fragment__language=language_to,
                                          annotation=None)

    if settings.CURRENT_DOCUMENTS:
        alignments = alignments.filter(original_fragment__document__title__in=settings.CURRENT_DOCUMENTS)

    return alignments.order_by('?').first()


def get_color(tense):
    """
    This function maps a tense on a color from the d3 color scale.
    See https://github.com/d3/d3-3.x-api-reference/blob/master/Ordinal-Scales.md#categorical-colors for details.
    :param tense: The given tense
    :return: A color from the d3 color scale.
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
    elif tense in [u'participio']:
        return '#17becf'
    else:
        print tense