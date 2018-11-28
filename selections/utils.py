from annotations.utils import get_available_corpora

from .models import PreProcessFragment, Selection


def get_random_fragment(user, language):
    """
    Retrieves a random, open PreProcessFragment from the database.
    :param user: The current User
    :param language: The current Language
    :return: A random PreProcessFragment object
    """
    fragments = get_open_fragments(user, language)

    for corpus in get_available_corpora(user):
        if corpus.current_subcorpus:
            fragments = fragments.filter(pk__in=corpus.current_subcorpus.get_fragments())

    return fragments.order_by('?').first()


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
        .exclude(selection__is_final=True)


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
