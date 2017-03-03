from django.contrib import admin

from .models import Language, Corpus, Document, Fragment, Sentence, Alignment


@admin.register(Language)
class Language(admin.ModelAdmin):
    list_display = ('iso', 'title', )


@admin.register(Corpus)
class CorpusAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_languages', 'get_annotators', )


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    pass


@admin.register(Fragment)
class FragmentAdmin(admin.ModelAdmin):
    list_display = ('target_words', )
    list_filter = ('document', 'language', )


@admin.register(Sentence)
class SentenceAdmin(admin.ModelAdmin):
    pass


@admin.register(Alignment)
class AlignmentAdmin(admin.ModelAdmin):
    list_display = ('original_fragment', 'translated_fragment', 'type')
