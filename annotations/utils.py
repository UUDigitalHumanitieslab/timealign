# -*- coding: utf-8 -*-

from collections import OrderedDict
import re

from lxml import etree

from django.db.models import Count, Prefetch

from selections.models import PreProcessFragment
from stats.utils import get_tense_properties_from_cache

from .models import Corpus, Tense, Alignment, Source, Annotation, Fragment, Sentence, Word


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
            result = list(map(int, xml_id[1:].split('.')))

    return result


def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    """
    Allows natural sorting, e.g. 2.xml is before 16.xml
    """
    return [int(text) if text.isdigit() else text.lower()
            for text in _nsre.split(s)]


def get_xml_sentences(fragment, limit):
    """
    Retrieves sentences in the XML in the vicinity of the given xml_id
    """
    try:
        source = Source.objects.get(document=fragment.document, language=fragment.language)
    except Source.DoesNotExist:
        source = None

    results = []

    if source and source.xml_file:
        xml_id = fragment.xml_ids()  # TODO: this works, as source Fragments have only one Sentence
        # TODO: limit to Fragments that are the source of an Alignment
        related_fragments = Fragment.objects.filter(
            document=fragment.document,
            language=fragment.language,
            preprocessfragment=None,
        )
        related_fragments = related_fragments.exclude(original=None)

        # Loop over p/s elements
        prev_el = []
        found = False
        added = 0
        for _, el in etree.iterparse(source.xml_file.path, tag=['p', 's']):
            if el.get('id') == xml_id:
                found = True

            if found:
                if added <= limit:
                    position = 'current' if added == 0 else 'after'
                    results.append(add_element(el, fragment, related_fragments, position))
                    if el.tag == 's':
                        added += 1
                else:
                    break
            else:
                prev_el.append(el)

        # Inserts previous elements before the results
        added = 0
        for el in list(reversed(prev_el)):
            results.insert(0, add_element(el, fragment, related_fragments, 'before'))
            if el.tag == 's':
                added += 1
            if added == limit:
                break

    return results


def add_element(el, current_fragment, related_fragments, position):
    sentence = None
    sentence_content_xml = None
    if el.tag == 's':
        # For s elements, look up the Sentence in the same Corpus as the current Fragment
        sentences = Sentence.objects.filter(
            xml_id=el.get('id'),
            fragment__in=related_fragments
        ).select_related('fragment').prefetch_related('word_set')

        if sentences:
            xml_id = None
            fragment_pks = []
            words = OrderedDict()
            for s in sentences:
                xml_id = s.xml_id
                fragment_pks.append(s.fragment.pk)
                is_current = current_fragment == s.fragment

                for w in s.word_set.all():
                    if w.xml_id in words:
                        words[w.xml_id]['is_target'] |= w.is_target and is_current
                        words[w.xml_id]['is_other_target'] |= w.is_target and not is_current
                    else:
                        word = {
                            'word': w.word,
                            'xml_id': w.xml_id,
                            'pos': w.pos,
                            'lemma': w.lemma,
                            'is_in_dialogue': w.is_in_dialogue,
                            'is_target': w.is_target and is_current,
                            'is_other_target': w.is_target and not is_current,
                        }
                        words[w.xml_id] = word

            fragment_pks.sort(reverse=True)
            sentence = {
                'xml_id': xml_id,
                'fragment_pks': fragment_pks,
                'words': list(words.values()),
            }

        # If the Sentence is not there, create a mock Sentence from the XML
        else:
            words = []
            for w in el.xpath('.//w'):
                word = {
                    'word': w.text,
                    'xml_id': w.get('id'),
                    'pos': w.get('tree') or w.get('pos') or w.get('hun') or '?',
                    'lemma': w.get('lem'),
                    'is_in_dialogue': float(w.get('dialog', 0)) > 0,
                }
                words.append(word)

            sentence_content_xml = {
                'xml_id': el.get('id'),
                'words': words
            }

    return {'tag': el.tag,
            'id': el.get('id'),
            'position': position,
            'content': sentence,
            'content_xml': sentence_content_xml,
            }


def bind_annotations_to_xml(source):
    # Retrieve the Annotations
    annotations = Annotation.objects. \
        filter(alignment__translated_fragment__language=source.language,
               alignment__translated_fragment__document=source.document). \
        select_related('alignment__original_fragment', 'tense'). \
        prefetch_related('words')
    # Only include correct Annotations
    annotations = annotations.filter(is_no_target=False, is_translation=True)
    tree = etree.parse(source.xml_file)

    tense_cache = {t.pk: (t.title, t.category.color, t.category.title)
                   for t in Tense.objects.select_related('category')}
    labels = set()
    failed_lookups = []

    words_by_xml_id = dict()

    if annotations:
        # Attach Annotations to the XML tree
        for annotation in annotations:
            tense_label, tense_color, _ = get_tense_properties_from_cache(
                annotation.label(as_pk=True), tense_cache, len(labels))
            labels.add(tense_label)

            words = annotation.words.all()
            for w in words:
                words_by_xml_id[w.xml_id] = dict(annotation=annotation, tense=tense_label, color=tense_color, found=False)

        for xml_w in tree.xpath('//w'):
            word = words_by_xml_id.get(xml_w.get('id'))
            if word:
                word['found'] = True
                annotation = word['annotation']
                tense_label = word['tense']
                tense_color = word['color']
                xml_w.set('annotation-pk', str(annotation.pk))
                xml_w.set('fragment-pk', str(annotation.alignment.original_fragment.pk))
                xml_w.set('tense', tense_label)
                xml_w.set('color', tense_color)
    else:
        # Assume we are dealing with a source language here
        # Retrieve the fragments
        target_words = Sentence.objects. \
            prefetch_related(Prefetch('word_set', queryset=Word.objects.filter(is_target=True)))
        pp_fragments = PreProcessFragment.objects.filter(language=source.language, document=source.document)
        fragments = Fragment.objects.filter(language=source.language, document=source.document). \
            exclude(pk__in=pp_fragments). \
            select_related('tense'). \
            prefetch_related(Prefetch('sentence_set', queryset=target_words, to_attr='targets_prefetched'))

        # Attach Fragments to the XML tree
        for fragment in fragments:
            tense_label, tense_color, _ = get_tense_properties_from_cache(
                fragment.label(as_pk=True), tense_cache, len(labels))
            labels.add(tense_label)

            sentences = fragment.targets_prefetched
            for s in sentences:
                for w in s.word_set.all():
                    words_by_xml_id[w.xml_id] = dict(fragment=fragment, tense=tense_label, color=tense_color, found=False)


        for xml_w in tree.xpath('//w'):
            word = words_by_xml_id.get(xml_w.get('id'))
            if word:
                word['found'] = True
                fragment = word['fragment']
                tense_label = word['tense']
                tense_color = word['color']
                xml_w.set('fragment-pk', str(fragment.pk))
                xml_w.set('tense', tense_label)
                xml_w.set('color', tense_color)

    for word in words_by_xml_id.values():
        if not word['found']:
            failed_lookups.append(word.get('fragment', word.get('annotation')))

    return tree, failed_lookups
