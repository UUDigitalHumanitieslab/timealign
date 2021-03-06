from annotations.utils import get_available_corpora

from .models import PreProcessFragment, Selection


def get_next_fragment(user, language, corpus=None):
    """
    Retrieves the next open PreProcessFragment from the database.
    :param user: The current User
    :param language: The current Language
    :param corpus: (if supplied) The Corpus where to draw an PreProcessFragment from
                   (otherwise: select from the available Corpora for a user)
    :return: A random PreProcessFragment object
    """
    fragments = get_open_fragments(user, language)

    corpora = [corpus] if corpus else get_available_corpora(user)
    fragments = fragments.filter(document__corpus__in=corpora)

    for corpus in corpora:
        if corpus.current_subcorpus:
            fragments = fragments.filter(pk__in=corpus.current_subcorpus.get_fragments())

    if not fragments:
        return None
    elif corpora[0].random_next_item:
        return fragments.order_by('?').first()
    else:
        # Sort by Document and Sentence.xml_id
        return sorted(fragments, key=lambda f: (f.document.title, f.sort_key()))[0]


def get_open_fragments(user, language):
    """
    Retrieves the open PreProcessFragments for this User and Language from the database.
    :param user: The current User
    :param language: The current Language
    :return: A random PreProcessFragment object
    """
    return PreProcessFragment.objects \
        .filter(language=language) \
        .filter(document__corpus__in=get_available_corpora(user)) \
        .exclude(selection__is_final=True) \
        .select_related('document') \
        .prefetch_related('sentence_set')


def get_selection_order(fragment, user):
    """
    Retrieves the next order for the current PreProcessFragment and User
    :param fragment: The current PreProcessFragment
    :param user: The current User
    :return: The next order
    """
    selections = Selection.objects.filter(fragment=fragment, selected_by=user)

    result = 1
    if selections:
        result = selections.latest().order + 1

    return result
