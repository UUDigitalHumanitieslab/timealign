# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.db import models
from django.forms.widgets import TextInput

from .models import Paper, Conference, Talk, Programme, Thesis


@admin.register(Paper)
class Paper(admin.ModelAdmin):
    list_display = ('title', 'get_authors', 'journal', )

    fieldsets = (
        ('General', {
            'fields': ('date', 'title', 'journal', 'volume', 'issue', 'pages')
        }),
        ('Authors', {
            'fields': ('authors', 'authors_alt', )
        }),
        ('File(s)', {
            'fields': ('url', 'document', 'appendix', )
        })
    )

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '80'})}
    }


@admin.register(Conference)
class Conference(admin.ModelAdmin):
    list_display = ('title', )


@admin.register(Talk)
class Talk(admin.ModelAdmin):
    list_display = ('title', 'get_authors', )

    fieldsets = (
        ('General', {
            'fields': ('date', 'title', 'conference', 'talk_type')
        }),
        ('Authors', {
            'fields': ('authors', 'authors_alt', )
        }),
        ('File(s)', {
            'fields': ('url', 'document', 'appendix', )
        })
    )

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '80'})}
    }


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
