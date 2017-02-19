from django.conf import settings
from django.db import models

from annotations.models import Fragment, Word


class PreProcessFragment(Fragment):
    # Whether the Fragment has to be pre-processed in VPSelect
    needs_selection = models.BooleanField(default=False)


class Selection(models.Model):
    is_no_target = models.BooleanField(
        'This fragment does not contain a verb phrase',
        default=False)

    words = models.ManyToManyField(Word, blank=True)
    fragment = models.ForeignKey(PreProcessFragment)

    selected_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='selected_by')
    selected_at = models.DateTimeField(auto_now_add=True)

    last_modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, related_name='selection_last_modified_by')
    last_modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('fragment', 'selected_by', )

    def selected_words(self):
        # TODO: is there a way to order on part of the id?! Or add an extra field...
        return ' '.join([word.word for word in self.words.all().order_by('xml_id')])