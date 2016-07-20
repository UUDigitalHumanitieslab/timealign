from django.contrib import admin

from .models import Sentence, Fragment, Alignment


@admin.register(Sentence)
class SentenceAdmin(admin.ModelAdmin):
    pass


@admin.register(Fragment)
class FragmentAdmin(admin.ModelAdmin):
    list_display = ('language', 'speaker_language', 'document')


@admin.register(Alignment)
class AlignmentAdmin(admin.ModelAdmin):
    list_display = ('original_fragment', 'translated_fragment', 'type')
