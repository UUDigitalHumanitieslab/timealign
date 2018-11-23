# -*- coding: utf-8 -*-

import re

from django.db.models import Count

from .models import Corpus, Tense, Alignment, Annotation, Word


def get_random_alignment(user, language_from, language_to, corpus=None):
    """
    Retrieves a random Alignment from the database.
    :param user: The current User
    :param language_from: The source language
    :param language_to: The target language
    :param corpus: (if supplied) The Corpus where to draw an Alignment from
                   (otherwise: select from the available Corpora for a user)
    :return: A random Alignment object
    """
    alignments = Alignment.objects \
        .filter(original_fragment__language=language_from) \
        .filter(translated_fragment__language=language_to) \
        .filter(annotation=None)

    corpora = [corpus] if corpus else get_available_corpora(user)
    alignments = alignments.filter(original_fragment__document__corpus__in=corpora)

    for corpus in corpora:
        if corpus.current_subcorpus:
            alignments = alignments.filter(original_fragment__in=corpus.current_subcorpus.get_fragments())

    return alignments.order_by('?').first()


def get_available_corpora(user):
    """
    Returns the available Corpora for a User.
    A superuser can see data from all corpora, other users are limited to corpora where they are an annotator.
    :param user: The current User
    :return: The available Corpora for this User
    """
    if user.is_superuser:
        return Corpus.objects.all()
    else:
        return user.corpus_set.all()


def get_most_frequent_tenses(language):
    """
    Returns the most frequently annotated tenses for a language.
    :param language: The given Language
    :return: A list of tenses
    """
    most_frequent_by_language = Annotation.objects \
        .filter(alignment__translated_fragment__language=language) \
        .values('tense') \
        .annotate(Count('tense')) \
        .order_by('-tense__count')
    return Tense.objects.filter(pk__in=[t.get('tense') for t in most_frequent_by_language])


def get_tenses(language):
    """
    Returns tenses for a language.
    :param language: The given Language
    :return: A list of tenses
    """
    return [t.title for t in Tense.objects.filter(language=language).order_by('title')]


def update_dialogue(in_dialogue, fragment=None, sentence=None, word_range=None):
    """
    Updates the dialogue marking for Words and Fragments.
    :param in_dialogue: whether the Words should be in_dialogue
    :param fragment: a Fragment for which to change the dialogue marking
    :param sentence: a Sentence for which to change the dialogue marking
    :param word_range: a Word range for which to change the dialogue marking
    """
    words = Word.objects.none()

    if not any([fragment, sentence, word_range]):
        raise ValueError('No words selected')

    if fragment:
        words |= Word.objects.filter(sentence__fragment=fragment)
    if sentence:
        words |= Word.objects.filter(sentence=sentence)
    if word_range:
        words |= Word.objects.filter(pk__in=word_range)

    fragments = set()
    for word in words:
        word.is_in_dialogue = in_dialogue
        word.is_in_dialogue_prob = 1.0 if in_dialogue else 0.0
        word.save()

        fragments.add(word.sentence.fragment)

    for fragment in fragments:
        fragment.save()


XML_ID_REGEX = re.compile(r'w?(\d[\.\d]*)')


def is_before(xml_id1, xml_id2):
    result = False

    match1 = re.match(XML_ID_REGEX, xml_id1)
    match2 = re.match(XML_ID_REGEX, xml_id2)
    if match1 and match2:
        parts1 = [int(i) for i in match1.group(1).split('.')]
        parts2 = [int(i) for i in match2.group(1).split('.')]

        for p1, p2 in zip(parts1, parts2):
            if p1 < p2:
                result = True
                break

    return result


def sort_key(xml_id, xml_tag):
    result = [xml_id]
    if xml_id.isdigit():
        result = int(xml_id)
    else:
        if xml_id[0] == xml_tag and xml_id[1:].split('.'):
            result = map(int, xml_id[1:].split('.'))

    return result
