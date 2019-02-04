from django.contrib import admin

from .forms import SubSentenceFormSet, SubSentenceForm
from .models import Language, TenseCategory, Tense, Corpus, Document, Fragment, \
    Sentence, Alignment, Annotation, SubCorpus, SubSentence


@admin.register(Language)
class Language(admin.ModelAdmin):
    list_display = ('iso', 'title', )


@admin.register(TenseCategory)
class TenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'color', )


@admin.register(Tense)
class TenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'language', )
    list_filter = ('language', 'category', )


@admin.register(Corpus)
class CorpusAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_languages', 'get_annotators', 'tense_based', 'check_structure', )


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', )
    list_filter = ('corpus', )


@admin.register(Fragment)
class FragmentAdmin(admin.ModelAdmin):
    list_display = ('language', 'xml_ids', 'full', 'target_words', 'label', )
    list_filter = ('document__corpus', 'language', )
    search_fields = ['sentence__word__word']


@admin.register(Sentence)
class SentenceAdmin(admin.ModelAdmin):
    pass


@admin.register(Alignment)
class AlignmentAdmin(admin.ModelAdmin):
    list_display = ('original_fragment', 'translated_fragment', 'type')


@admin.register(Annotation)
class AnnotationAdmin(admin.ModelAdmin):
    list_display = ('pk', 'selected_words', 'label',  'annotated_by', 'annotated_at', )
    list_filter = ('is_no_target', 'is_translation', 'annotated_by', )


class SubSentenceInline(admin.TabularInline):
    model = SubSentence
    form = SubSentenceForm
    formset = SubSentenceFormSet
    max_num = 3


@admin.register(SubCorpus)
class SubCorpusAdmin(admin.ModelAdmin):
    list_display = ('title', 'language', 'corpus', )
    list_filter = ('corpus', )

    inlines = [
        SubSentenceInline,
    ]


@admin.register(SubSentence)
class SubSentenceAdmin(admin.ModelAdmin):
    list_display = ('subcorpus', 'document', 'xml_id', )
    list_filter = ('subcorpus__corpus', )
