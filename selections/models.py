from django.conf import settings
from django.db import models

from annotations.models import Fragment, Word


class PreProcessFragment(Fragment):
    def selected_words(self, user=None):
        result = dict()

        selections = self.selection_set.all()
        if user:
            selections = selections.filter(selected_by=user)

        for selection in selections:
            result[selection.order] = [word.xml_id for word in selection.words.all()]

        return result

    def has_final(self):
        return self.selection_set.filter(is_final=True).exists()


class Selection(models.Model):
    is_no_target = models.BooleanField(
        'This fragment does not contain a target',
        default=False)

    order = models.PositiveIntegerField(default=1)
    is_final = models.BooleanField(default=True)

    words = models.ManyToManyField(Word, blank=True)
    comments = models.TextField(blank=True)
    fragment = models.ForeignKey(PreProcessFragment, on_delete=models.CASCADE)

    selected_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, related_name='selected_by', on_delete=models.SET_NULL)
    selected_at = models.DateTimeField(auto_now_add=True)

    last_modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, related_name='selection_last_modified_by', on_delete=models.SET_NULL)
    last_modified_at = models.DateTimeField(auto_now=True)

    tense = models.CharField('Tense', max_length=200, blank=True)
    other_label = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ('fragment', 'selected_by', 'order')
        get_latest_by = 'order'
        ordering = ('-selected_at', )

    def annotated_words(self):
        """
        Retrieves the selected Words for this Selection.
        Order is based on the xml_id, e.g. w18.1.10 should be after w18.1.9.
        :return: A space-separated string with the selected words.
        """
        from annotations.utils import sort_key

        ordered_words = sorted(self.words.all(), key=lambda w: sort_key(w.xml_id, w.XML_TAG))
        return ' '.join([word.word for word in ordered_words])
