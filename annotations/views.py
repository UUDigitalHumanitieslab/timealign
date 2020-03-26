import os
from collections import defaultdict
from tempfile import NamedTemporaryFile

from lxml import etree

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Prefetch
from django.urls import reverse
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.views import generic
from django.utils.http import urlquote

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django_filters.views import FilterView

from .exports import export_pos_file
from .filters import AnnotationFilter
from .forms import AnnotationForm, LabelImportForm
from .models import Corpus, SubCorpus, Document, Language, Fragment, Alignment, Annotation, \
    TenseCategory, Tense, Source, Sentence, Word
from .utils import get_random_alignment, get_available_corpora, get_xml_sentences, bind_annotations_to_xml, \
    natural_sort_key

from core.utils import XLSX


class CheckOwnerOrStaff(UserPassesTestMixin):
    """Limits access only to creator of annotation or staff users"""

    def test_func(self):
        return self.get_object().annotated_by == self.request.user or \
            self.request.user.is_staff or self.request.user.is_superuser


##############
# Static views
##############
class IntroductionView(generic.TemplateView):
    """Loads a static introduction view"""
    template_name = 'annotations/introduction.html'


class InstructionsView(generic.TemplateView):
    """Loads the various steps of the instructions"""

    def get_template_names(self):
        return 'annotations/instructions{}.html'.format(self.kwargs['n'])

    def get_context_data(self, **kwargs):
        context = super(InstructionsView, self).get_context_data(**kwargs)

        context['is_no_target_title'] = Annotation._meta.get_field('is_no_target').verbose_name.format('present perfect')
        context['is_translation_title'] = Annotation._meta.get_field('is_translation').verbose_name

        return context


class StatusView(PermissionRequiredMixin, generic.TemplateView):
    """Loads a static home view, with an overview of the annotation progress"""
    template_name = 'annotations/home.html'
    permission_required = 'annotations.change_annotation'

    def get_context_data(self, **kwargs):
        """Creates a list of tuples with information on the annotation progress"""
        context = super(StatusView, self).get_context_data(**kwargs)

        corpus_pk = self.kwargs.get('pk', None)
        if corpus_pk:
            corpora = [get_object_or_404(Corpus, pk=corpus_pk)]
        else:
            corpora = get_available_corpora(self.request.user)

        # Retrieve the totals per language pair
        alignments = Alignment.objects.filter(original_fragment__document__corpus__in=corpora)
        totals = alignments \
            .values('original_fragment__language', 'translated_fragment__language') \
            .order_by('original_fragment__language', 'translated_fragment__language') \
            .annotate(count=Count('pk'))
        completed = {(t.get('original_fragment__language'), t.get('translated_fragment__language')): t.get('count')
                     for t in totals.exclude(annotation=None)}

        # Convert the QuerySets into a list of tuples
        languages = {l.pk: l for l in Language.objects.all()}
        language_totals = []
        for total in totals:
            l1 = languages.get(total['original_fragment__language'])
            l2 = languages.get(total['translated_fragment__language'])
            complete = completed.get((l1.pk, l2.pk), 0)
            available = total['count']

            language_totals.append((l1, l2, complete, available))

        context['languages'] = language_totals
        context['corpus_pk'] = corpus_pk
        context['current_corpora'] = corpora

        return context


#################
# CRUD Annotation
#################
class AnnotationMixin(SuccessMessageMixin, PermissionRequiredMixin):
    model = Annotation
    form_class = AnnotationForm
    permission_required = 'annotations.change_annotation'

    def __init__(self):
        """Creates an attribute to cache the Alignment"""
        super(AnnotationMixin, self).__init__()
        self.alignment = None

    def get_form_kwargs(self):
        """Sets the User and the Alignment as a form kwarg"""
        kwargs = super(AnnotationMixin, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['alignment'] = self.get_alignment()
        kwargs['select_segment'] = self.request.session.get('select_segment', False)
        return kwargs

    def get_context_data(self, **kwargs):
        """Sets the Alignment on the context"""
        context = super(AnnotationMixin, self).get_context_data(**kwargs)
        context['alignment'] = self.get_alignment()
        return context

    def get_alignment(self):
        raise NotImplementedError

    def get_alignments(self):
        """Retrieve related fields on Alignment to prevent extra queries"""
        return Alignment.objects.select_related('original_fragment', 'translated_fragment')

    def form_valid(self, form):
        # save user preferred selection tool on the session
        self.request.session['select_segment'] = form.cleaned_data['select_segment']
        return super().form_valid(form)


class AnnotationUpdateMixin(AnnotationMixin, CheckOwnerOrStaff):
    def get_context_data(self, **kwargs):
        """Sets the annotated Words on the context"""
        context = super(AnnotationUpdateMixin, self).get_context_data(**kwargs)
        context['annotated_words'] = self.object.words.all()
        return context

    def get_success_url(self):
        """Returns to the overview per language"""
        alignment = self.get_alignment()
        l1 = alignment.original_fragment.language.iso
        l2 = alignment.translated_fragment.language.iso
        return reverse('annotations:list', args=(l1, l2,))

    def get_alignment(self):
        """Retrieves the Alignment from the object"""
        if not self.alignment:
            self.alignment = self.get_alignments().get(pk=self.object.alignment.pk)
        return self.alignment


class AnnotationCreate(AnnotationMixin, generic.CreateView):
    success_message = 'Annotation created successfully'

    def get_success_url(self):
        """Go to the choose-view to select a new Alignment"""
        alignment = self.object.alignment
        return reverse('annotations:choose', args=(alignment.original_fragment.document.corpus.pk,
                                                   alignment.original_fragment.language.iso,
                                                   alignment.translated_fragment.language.iso))

    def form_valid(self, form):
        """Sets the User and Alignment on the created instance"""
        form.instance.annotated_by = self.request.user
        form.instance.alignment = self.get_alignment()
        return super(AnnotationCreate, self).form_valid(form)

    def get_alignment(self):
        """Retrieves the Alignment by the pk in the kwargs"""
        if not self.alignment:
            self.alignment = get_object_or_404(self.get_alignments(), pk=self.kwargs['pk'])
        return self.alignment


class AnnotationUpdate(AnnotationUpdateMixin, generic.UpdateView):
    success_message = 'Annotation edited successfully'

    def form_valid(self, form):
        """Sets the last modified by on the instance"""
        form.instance.last_modified_by = self.request.user
        return super(AnnotationUpdate, self).form_valid(form)


class AnnotationDelete(AnnotationUpdateMixin, generic.DeleteView):
    success_message = 'Annotation deleted successfully'


class AnnotationChoose(PermissionRequiredMixin, generic.RedirectView):
    permanent = False
    pattern_name = 'annotations:create'
    permission_required = 'annotations.change_annotation'

    def get_redirect_url(self, *args, **kwargs):
        """Redirects to a random Alignment"""
        l1 = Language.objects.get(iso=self.kwargs['l1'])
        l2 = Language.objects.get(iso=self.kwargs['l2'])
        corpus = Corpus.objects.get(pk=int(self.kwargs['corpus'])) if 'corpus' in self.kwargs else None
        new_alignment = get_random_alignment(self.request.user, l1, l2, corpus)

        # If no new alignment has been found, redirect to the status overview
        if not new_alignment:
            messages.success(
                self.request, 'All work is done for this language pair!')
            return reverse('annotations:status')

        corpus_pk = new_alignment.original_fragment.document.corpus.pk
        return super(AnnotationChoose, self).get_redirect_url(corpus_pk, new_alignment.pk)


############
# CRUD Fragment
############
class FragmentDetail(LoginRequiredMixin, generic.DetailView):
    model = Fragment

    def get_object(self, queryset=None):
        qs = Fragment.objects \
            .select_related('document__corpus', 'language', 'tense') \
            .prefetch_related('original', 'sentence_set__word_set')
        fragment = super(FragmentDetail, self).get_object(qs)
        return fragment

    def get_context_data(self, **kwargs):
        context = super(FragmentDetail, self).get_context_data(**kwargs)

        fragment = self.object
        limit = 5  # TODO: magic number
        doc_sentences = get_xml_sentences(fragment, limit)

        context['sentences'] = doc_sentences or fragment.sentence_set.all()
        context['limit'] = limit

        return context


class FragmentDetailPlain(LoginRequiredMixin, generic.DetailView):
    model = Fragment
    template_name = 'annotations/fragment_detail_plain.html'

    def get_object(self, queryset=None):
        qs = Fragment.objects \
            .select_related('document__corpus', 'language', 'tense') \
            .prefetch_related('original', 'sentence_set__word_set')
        fragment = super(FragmentDetailPlain, self).get_object(qs)
        return fragment


############
# CRUD Corpus
############
class CorpusList(LoginRequiredMixin, generic.ListView):
    model = Corpus
    context_object_name = 'corpora'
    ordering = 'title'


class CorpusDetail(LoginRequiredMixin, generic.DetailView):
    model = Corpus

    def get_context_data(self, **kwargs):
        context = super(CorpusDetail, self).get_context_data(**kwargs)

        # Retrieve all Documents and order them by title
        corpus = self.object
        documents = {d.pk: d.title for d in corpus.documents.all()}
        documents_sorted = sorted(list(documents.items()), key=lambda x: natural_sort_key(x[1]))
        document_pks = [d[0] for d in documents_sorted]

        # Create a list of Languages
        languages = defaultdict(list)
        for language in corpus.languages.all():
            languages[language.title] = [None] * len(document_pks)

        # Retrieve the number of Annotations per document
        by_document = Annotation.objects. \
            filter(alignment__translated_fragment__document__corpus=corpus). \
            values('alignment__translated_fragment__language__title',
                   'alignment__translated_fragment__document__pk'). \
            annotate(Count('pk'))

        # Wrap the number of Annotations into the list of Languages
        for d in by_document:
            language = d.get('alignment__translated_fragment__language__title')
            document_pk = d.get('alignment__translated_fragment__document__pk')

            index = document_pks.index(document_pk)
            languages[language][index] = d.get('pk__count')

        # And finally, append the list of Document and Languages to the context
        context['documents'] = documents_sorted
        context['languages'] = dict(languages)

        return context

############
# CRUD Document
############


class DocumentDetail(LoginRequiredMixin, generic.DetailView):
    model = Document


############
# CRUD Source
############
class SourceDetail(LoginRequiredMixin, generic.DetailView):
    model = Source

    def get_object(self, queryset=None):
        qs = Source.objects \
            .select_related('document__corpus', 'language')
        source = super(SourceDetail, self).get_object(qs)
        return source

    def get_context_data(self, **kwargs):
        context = super(SourceDetail, self).get_context_data(**kwargs)

        source = self.object
        tree, failed_lookups = bind_annotations_to_xml(source)
        additional_sources = Source.objects.filter(document=source.document) \
            .exclude(pk=source.pk) \
            .select_related('language')

        transform = etree.XSLT(etree.fromstring(render_to_string('annotations/xml_transform.xslt').encode('utf-8')))
        context['sentences'] = [transform(p) for p in tree.iter('p')]
        context['failed_lookups'] = failed_lookups
        context['additional_sources'] = additional_sources
        context['rows'] = [(x,) for x in context['sentences']]

        additional_source = self.request.GET.get('additional_source')
        if additional_source:
            source = get_object_or_404(Source, pk=additional_source)
            add_tree, add_failed_lookups = bind_annotations_to_xml(source)

            context['additional_source'] = source
            context['additional_sentences'] = [transform(p) for p in add_tree.iter('p')]
            context['failed_lookups'] = context['failed_lookups'].extend(add_failed_lookups)
            context['rows'] = zip(context['sentences'], context['additional_sentences'])

        return context


############
# List views
############
class AnnotationList(PermissionRequiredMixin, FilterView):
    context_object_name = 'annotations'
    filterset_class = AnnotationFilter
    paginate_by = 15
    permission_required = 'annotations.change_annotation'

    def get_queryset(self):
        """
        Retrieves all Annotations for the given source (l1) and target (l2) language.
        :return: A QuerySet of Annotations.
        """
        target_words = Sentence.objects. \
            prefetch_related(Prefetch('word_set', queryset=Word.objects.filter(is_target=True)))
        return Annotation.objects \
            .filter(alignment__original_fragment__language__iso=self.kwargs['l1']) \
            .filter(alignment__translated_fragment__language__iso=self.kwargs['l2']) \
            .filter(alignment__original_fragment__document__corpus__in=get_available_corpora(self.request.user)) \
            .select_related('annotated_by',
                            'tense',
                            'alignment__original_fragment',
                            'alignment__original_fragment__document',
                            'alignment__original_fragment__tense',
                            'alignment__translated_fragment') \
            .prefetch_related('alignment__original_fragment__sentence_set__word_set',
                              Prefetch('alignment__original_fragment__sentence_set', queryset=target_words,
                                       to_attr='targets_prefetched'),
                              'alignment__translated_fragment__sentence_set__word_set',
                              'words') \
            .order_by('-annotated_at')


class FragmentList(PermissionRequiredMixin, generic.ListView):
    """
    TODO: consider refactoring, too many queries.
    """
    context_object_name = 'fragments'
    template_name = 'annotations/fragment_list.html'
    paginate_by = 25
    permission_required = 'annotations.change_annotation'

    def get_queryset(self):
        """
        Retrieves all Fragments for the given language that have an Annotation that contains a target expression.
        :return: A list of Fragments.
        """
        results = []
        fragments = Fragment.objects.filter(language__iso=self.kwargs['language']) \
            .filter(document__corpus__in=get_available_corpora(self.request.user))

        for fragment in fragments:
            if Annotation.objects.filter(alignment__original_fragment=fragment, is_no_target=False).exists():
                results.append(fragment)
            if len(results) == 50:  # TODO: Capping this for now with a magic number.
                break
        return results

    def get_context_data(self, **kwargs):
        """
        Sets the current language and other_languages on the context
        :param kwargs: Contains the current language.
        :return: The context variables.
        """
        context = super(FragmentList, self).get_context_data(**kwargs)
        language = self.kwargs['language']
        corpus = context['fragments'][0].document.corpus
        context['language'] = Language.objects.filter(iso=language)
        context['other_languages'] = corpus.languages.exclude(iso=language)

        context['show_tenses'] = self.kwargs.get('showtenses', False)

        return context


class TenseCategoryList(PermissionRequiredMixin, generic.ListView):
    model = TenseCategory
    context_object_name = 'tensecategories'
    template_name = 'annotations/tenses.html'
    permission_required = 'annotations.change_annotation'

    def get_context_data(self, **kwargs):
        """
        Sets the tenses and languages on the context
        :return: The context variables.
        """
        context = super(TenseCategoryList, self).get_context_data(**kwargs)

        tense_cache = {(t.category.title, t.language.iso): t.title for t in
                       Tense.objects.select_related('category', 'language')}
        tense_categories = TenseCategory.objects.all()

        tenses = defaultdict(list)
        languages = []

        for language in Language.objects.order_by('iso'):
            if not Tense.objects.filter(language=language):
                continue

            languages.append(language)

            for tc in tense_categories:
                tense = tense_cache.get((tc.title, language.iso), '')
                tenses[tc].append(tense)

        context['tenses'] = sorted(list(tenses.items()), key=lambda item: item[0].pk)
        context['languages'] = languages

        return context


class PrepareDownload(generic.TemplateView):
    template_name = 'annotations/download.html'

    def get_context_data(self, **kwargs):
        context = super(PrepareDownload, self).get_context_data(**kwargs)

        corpora = get_available_corpora(self.request.user)
        language = Language.objects.get(iso=kwargs['language'])
        corpora = corpora.filter(languages=language)
        selected_corpus = corpora.first()
        if kwargs.get('corpus'):
            selected_corpus = Corpus.objects.get(pk=int(kwargs['corpus']))

        context['language_to'] = language
        context['corpora'] = corpora
        context['selected_corpus'] = selected_corpus
        return context


class ExportPOSPrepare(PermissionRequiredMixin, generic.View):
    permission_required = 'annotations.change_annotation'

    def get(self, request, *args, **kwargs):
        language = self.request.GET['language']
        corpus_id = self.request.GET['corpus']
        subcorpus_id = self.request.GET['subcorpus']
        document_id = self.request.GET['document']
        include_non_targets = 'include_non_targets' in self.request.GET

        pos_file = NamedTemporaryFile(delete=False)
        self.request.session['pos_file'] = pos_file.name

        corpus = Corpus.objects.get(pk=int(corpus_id))
        subcorpus = SubCorpus.objects.get(pk=int(subcorpus_id)) if subcorpus_id != 'all' else None
        document = Document.objects.get(pk=int(document_id)) if document_id != 'all' else None
        document_title = document.title if document_id != 'all' else 'all'

        filename = '{}-{}-{}.xlsx'.format(urlquote(corpus.title), urlquote(document_title), language)
        self.request.session['pos_filename'] = filename
        export_pos_file(pos_file.name, XLSX, corpus, language, include_non_targets=include_non_targets,
                        subcorpus=subcorpus, document=document)

        return JsonResponse(dict(done=True))


class ExportPOSDownload(PermissionRequiredMixin, generic.View):
    permission_required = 'annotations.change_annotation'

    def get(self, request, *args, **kwargs):
        pos_file = self.request.session['pos_file']
        pos_filename = self.request.session['pos_filename']

        with open(pos_file, 'rb') as f:
            contents = f.read()
        os.unlink(pos_file)
        response = HttpResponse(contents, content_type='application/xlsx')
        response['Content-Disposition'] = 'attachment; filename={}'.format(pos_filename)
        return response


class ImportLabelsView(LoginRequiredMixin, UserPassesTestMixin, generic.View):
    """
    Allows superusers to import labels to Annotations and Fragments
    """
    form_class = LabelImportForm
    template_name = 'annotations/label_form.html'

    def test_func(self):
        # limit access to superusers
        return self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            try:
                form.save()
                messages.success(
                    self.request, 'Successfully imported the labels!')
            except ValueError as e:
                messages.error(
                    self.request, 'Error during import: {}'.format(e.message))
            return redirect(reverse('annotations:import-labels'))
        else:
            return render(request, self.template_name, {'form': form})
