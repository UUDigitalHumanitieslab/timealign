from annotations.utils import get_available_corpora

from .models import PreProcessFragment


def get_random_fragment(user, language):
    """
    Retrieves a random PreProcessFragment from the database.
    :param user: The current User
    :param language: The current language
    :return: A random PreProcessFragment object
    """
    fragments = PreProcessFragment.objects.filter(language=language, needs_selection=True, selection=None)

    fragments = fragments.filter(document__corpus__in=get_available_corpora(user))

    return fragments.order_by('?').first()