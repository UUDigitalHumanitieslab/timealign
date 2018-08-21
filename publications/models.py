# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models


class Publication(models.Model):
    date = models.DateField(default=datetime.date.today)
    title = models.CharField(max_length=200)

    authors = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)
    authors_alt = models.CharField(
        'Author(s) display name',
        max_length=200,
        blank=True,
        help_text='If the author is not a registered User, please supply an author name here')

    class Meta:
        abstract = True
        ordering = ['-date']

    def get_authors(self):
        if not self.authors:
            return self.authors_alt
        else:
            return ' and '.join([author.get_full_name() for author in self.authors.order_by('last_name')])
    get_authors.short_description = 'Authors'


class Programme(models.Model):
    title = models.CharField(max_length=200)

    def __unicode__(self):
        return self.title


class Thesis(Publication):
    TL_BA = 'BA'
    TL_MA = 'MA'
    TL_INTERN = 'IN'
    THESIS_LEVELS = (
        (TL_BA, 'Bachelor'),
        (TL_MA, 'Master'),
        (TL_INTERN, 'Internship report'),
    )

    description = models.CharField(
        max_length=200,
        help_text='Short description, e.g. "investigated the semantics and pragmatics of the Greek perfect"')

    programme = models.ForeignKey(Programme)
    level = models.CharField(
        max_length=2,
        choices=THESIS_LEVELS,
        default=TL_BA)

    url = models.URLField(
        'Link to thesis in thesis archive',
        blank=True)
    document = models.FileField(
        blank=True,
        validators=[FileExtensionValidator(['pdf'])],
        help_text='Use this only if there is no archived version available')
    appendix = models.FileField(
        blank=True,
        validators=[FileExtensionValidator(['pdf'])],
        help_text='Use this only if there is no archived version available')

    class Meta(Publication.Meta):
        verbose_name_plural = 'Theses'

    def get_url(self):
        return self.url or self.document.url

    def __unicode__(self):
        return self.title
