# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.db import models
from django.forms.widgets import TextInput

from .models import Programme, Thesis


@admin.register(Programme)
class Programme(admin.ModelAdmin):
    list_display = ('title', )


@admin.register(Thesis)
class Thesis(admin.ModelAdmin):
    list_display = ('title', 'get_authors', 'date', 'programme', 'level', )
    list_filter = ('programme', 'level', )
    date_hierarchy = 'date'

    fieldsets = (
        ('General', {
            'fields': ('date', 'title', 'description', )
        }),
        ('Authors', {
            'fields': ('authors', 'authors_alt', )
        }),
        ('Programme', {
            'fields': ('programme', 'level', )
        }),
        ('Thesis', {
            'fields': ('url', 'document', 'appendix', )
        })
    )

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '80'})}
    }
