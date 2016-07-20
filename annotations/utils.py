from .models import Alignment


def get_random_alignment(language_from, language_to):
    return Alignment.objects.filter(
        original_fragment__language=language_from,
        translated_fragment__language=language_to,
        annotation=None).order_by('?').first()
