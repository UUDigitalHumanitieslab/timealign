from django.conf import settings
from django.db import models

from annotations.models import Fragment, Word


class PreProcessFragment(Fragment):
    def selected_words(self):
        """
        Retrieves the selected Words for this PreProcessFragment.
        :return: A list of Strings with the selected Words.
        """
        return ' '.join([word.word for word in self.selection_set.first().words.all()])


class Selection(models.Model):
    is_no_target = models.BooleanField(
        'This fragment does not contain a verb phrase',
        default=False)

    order = models.PositiveIntegerField(default=1)
    is_final = models.BooleanField(default=True)

    words = models.ManyToManyField(Word, blank=True)
    fragment = models.ForeignKey(PreProcessFragment)

    selected_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='selected_by')
    selected_at = models.DateTimeField(auto_now_add=True)

    last_modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, related_name='selection_last_modified_by')
    last_modified_at = models.DateTimeField(auto_now=True)

    tense = models.CharField('Tense', max_length=200, blank=True)

    class Meta:
        unique_together = ('fragment', 'selected_by', 'order')
        get_latest_by = 'order'

    def selected_words(self):
        # TODO: is there a way to order on part of the id?! Or add an extra field...
        return ' '.join([word.word for word in self.words.all().order_by('xml_id')])