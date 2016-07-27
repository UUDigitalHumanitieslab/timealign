from .models import Alignment


def get_random_alignment(language_from, language_to):
    """
    Retrieves a random Alignment from the database.
    :param language_from: The source language
    :param language_to: The target language
    :return: A random Alignment object
    """
    return Alignment.objects.filter(
        original_fragment__language=language_from,
        translated_fragment__language=language_to,
        annotation=None).order_by('?').first()
