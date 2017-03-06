from annotations.utils import get_available_corpora

from .models import PreProcessFragment


def get_random_fragment(user, language):
    """
    Retrieves a random, open PreProcessFragment from the database.
    :param user: The current User
    :param language: The current Language
    :return: A random PreProcessFragment object
    """
    return get_open_fragments(user, language).order_by('?').first()


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
        .exclude(selection__selected_by=user)
