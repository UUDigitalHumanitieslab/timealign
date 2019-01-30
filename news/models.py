import datetime

from django.core.validators import validate_slug
from django.db import models

from ckeditor_uploader.fields import RichTextUploadingField


class Post(models.Model):
    date = models.DateField(default=datetime.date.today)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, validators=[validate_slug])
    content = RichTextUploadingField()

    is_published = models.BooleanField(help_text='Untick if you want to keep this as a draft', default=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __unicode__(self):
        return self.title
