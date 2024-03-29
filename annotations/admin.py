from django.contrib import admin
from django.urls import reverse
from django.http import HttpResponseRedirect

from django_object_actions import DjangoObjectActions
from reversion.admin import VersionAdmin
from nested_admin.nested import NestedModelAdmin, NestedTabularInline

from .forms import SubSentenceForm, SubSentenceFormSet, LabelForm
from .models import Language, TenseCategory, Tense, Corpus, Document, Source, Fragment, \
    Sentence, Word, Alignment, Annotation, SubCorpus, SubSentence, Label, LabelKey


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


class SourceInline(admin.TabularInline):
    model = Source


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', )
    list_filter = ('corpus', )

    inlines = [
        SourceInline,
    ]


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ('pk', 'language', 'document', )
    list_filter = ('document__corpus', 'language', )


class WordInline(NestedTabularInline):
    model = Word
    extra = 0


class SentenceInline(NestedTabularInline):
    model = Sentence
    extra = 0
    inlines = [WordInline]


@admin.register(Fragment)
class FragmentAdmin(DjangoObjectActions, NestedModelAdmin, VersionAdmin):
    list_display = ('pk', 'language', 'xml_ids', 'full', 'target_words', 'label', )
    list_filter = ('document__corpus', 'language', )
    list_per_page = 20
    search_fields = ['pk', 'sentence__word__word']

    fieldsets = (
        ('General', {
            'fields': ('language', 'document', )
        }),
        ('Annotation', {
            'fields': ('tense', 'labels', 'formal_structure', 'sentence_function', )
        }),
    )

    inlines = [SentenceInline]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'document':
            kwargs['queryset'] = Document.objects.select_related('corpus')
        return super(FragmentAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def show_fragment(self, request, obj):
        return HttpResponseRedirect(reverse('annotations:show', args=(obj.pk, )))
    show_fragment.label = 'Show Fragment'
    show_fragment.short_description = 'Show Fragment in front-end'

    change_actions = ['show_fragment']


@admin.register(Alignment)
class AlignmentAdmin(admin.ModelAdmin):
    list_display = ('original_fragment', 'translated_fragment', 'type')


@admin.register(Annotation)
class AnnotationAdmin(VersionAdmin):
    list_display = ('pk', 'selected_words', 'label',
                    'annotated_by', 'annotated_at', )
    list_filter = ('is_no_target', 'is_translation', 'annotated_by', )

    readonly_fields = ('words', 'alignment')


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


class LabelKeyInline(admin.TabularInline):
    model = LabelKey
    show_change_link = True
    extra = 0


@admin.register(Corpus)
class CorpusAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_languages', 'get_annotators',
                    'tense_based', 'check_structure', 'is_public', )


class LabelInline(admin.TabularInline):
    model = Label
    form = LabelForm
    extra = 0


@admin.register(LabelKey)
class LabelKeyAdmin(admin.ModelAdmin):
    list_display = ('title',)
    list_filter = ('corpora',)
    inlines = [LabelInline]
