from annotations.models import Fragment
from annotations.utils import get_available_corpora


def get_random_fragment(user, language):
    """
    Retrieves a random Alignment from the database.
    :param user: The current User
    :param language: The current language
    :return: A random Fragment object
    """
    fragments = Fragment.objects.filter(language=language, selection=None)

    fragments = fragments.filter(document__corpus__in=get_available_corpora(user))

    return fragments.order_by('?').first()