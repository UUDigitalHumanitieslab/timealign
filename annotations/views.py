import os
from collections import defaultdict
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Prefetch, QuerySet
from django.http import HttpResponse, JsonResponse, QueryDict
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import urlquote
from django.views import generic
from django_filters.views import FilterView
from lxml import etree
from reversion.models import Version
from reversion.revisions import add_to_revision, set_comment
from reversion.views import RevisionMixin

from core.mixins import ImportMixin, CheckOwnerOrStaff, FluidMixin, SuperuserRequiredMixin, LimitedPublicAccessMixin
from core.utils import find_in_enum, XLSX
from stats.models import Scenario
from .exports import export_annotations
from .filters import AnnotationFilter
from .forms import AnnotationForm, LabelImportForm, AddFragmentsForm, FragmentForm
from .mixins import PrepareDownloadMixin, SelectSegmentMixin, ImportFragmentsMixin
from .models import Corpus, SubCorpus, Document, Language, Fragment, Alignment, Annotation, \
    TenseCategory, Tense, Source, Sentence, Word, LabelKey
from .utils import get_next_alignment, get_available_corpora, get_xml_sentences, bind_annotations_to_xml, \
    natural_sort_key


##############
# Static views
##############
class IntroductionView(generic.TemplateView):
    """
    Loads a static introduction view.
    """
    template_name = 'annotations/introduction.html'


class InstructionsView(generic.TemplateView):
    """
    Loads the various steps of the instructions.
    """

    def get_template_names(self):
        return 'annotations/instructions{}.html'.format(self.kwargs['n'])

    def get_context_data(self, **kwargs):
        context = super(InstructionsView, self).get_context_data(**kwargs)

        context['is_no_target_title'] = Annotation._meta.get_field('is_no_target').verbose_name.format(
            'present perfect')
        context['is_translation_title'] = Annotation._meta.get_field('is_translation').verbose_name

        return context


class StatusView(PermissionRequiredMixin, generic.TemplateView):
    """
    Loads a static home view, with an overview of the annotation progress.
    """
    template_name = 'annotations/home.html'
    permission_required = 'annotations.change_annotation'

    def get_context_data(self, **kwargs):
        """Creates a list of tuples with information on the annotation progress."""
        context = super(StatusView, self).get_context_data(**kwargs)

        corpus_pk = self.kwargs.get('pk', None)
        if corpus_pk:
            corpora = [get_object_or_404(Corpus, pk=corpus_pk)]
        else:
            corpora = get_available_corpora(self.request.user)

        # Retrieve the totals per language pair
        languages = {language.pk: language for language in Language.objects.all()}
        alignments = Alignment.objects.filter(original_fragment__document__corpus__in=corpora)
        totals = alignments \
            .values('original_fragment__language', 'translated_fragment__language') \
            .order_by('original_fragment__language', 'translated_fragment__language') \
            .annotate(count=Count('pk'))
        completed = {(t.get('original_fragment__language'), t.get('translated_fragment__language')): t.get('count')
                     for t in totals.exclude(annotation=None)}

        # Convert the QuerySets into a list of tuples
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
class AnnotationMixin(SelectSegmentMixin, SuccessMessageMixin, PermissionRequiredMixin):
    model = Annotation
    form_class = AnnotationForm
    permission_required = 'annotations.change_annotation'

    def __init__(self):
        """Creates an attribute to cache the Alignment."""
        super(AnnotationMixin, self).__init__()
        self.alignment = None

    def get_form_kwargs(self):
        """Sets the User and the Alignment as a form kwarg."""
        kwargs = super(AnnotationMixin, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['alignment'] = self.get_alignment()
        kwargs['select_segment'] = self.request.session.get('select_segment', False)
        return kwargs

    def get_context_data(self, **kwargs):
        """Sets the Alignment on the context."""
        context = super(AnnotationMixin, self).get_context_data(**kwargs)
        context['alignment'] = self.get_alignment()
        return context

    def get_alignment(self):
        raise NotImplementedError

    def get_alignments(self):
        """Retrieve related fields on Alignment to prevent extra queries."""
        return Alignment.objects \
            .select_related('original_fragment__document__corpus',
                            'translated_fragment__document__corpus') \
            .prefetch_related('original_fragment__sentence_set__word_set',
                              'translated_fragment__sentence_set__word_set')


class RevisionWithCommentMixin(RevisionMixin):
    revision_manage_manually = True

    def form_valid(self, form):
        result = super().form_valid(form)
        if form.changed_data:
            add_to_revision(self.object)
            set_comment(self.format_change_comment(form.changed_data, form.cleaned_data))

        return result

    def format_change_for_field(self, field, value):
        if isinstance(value, QuerySet):
            value = ', '.join(map(str, value))
        return '{} to "{}"'.format(field, value)

    def format_change_comment(self, changes, values):
        parts = []
        for change in changes:
            parts.append(self.format_change_for_field(change, values[change]))
        return 'Changed {}'.format(', '.join(parts))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['revisions'] = Version.objects.get_for_object(self.object)
        return context


class RevisionCreateMixin(RevisionMixin):
    def form_valid(self, form):
        set_comment('Created annotation')
        return super().form_valid(form)


class AnnotationUpdateMixin(AnnotationMixin, CheckOwnerOrStaff, RevisionWithCommentMixin):
    def get_context_data(self, **kwargs):
        """Sets the annotated Words on the context."""
        context = super(AnnotationUpdateMixin, self).get_context_data(**kwargs)
        context['annotated_words'] = self.object.words.all()
        return context

    def get_success_url(self):
        """Returns to the overview per language."""
        alignment = self.get_alignment()
        l1 = alignment.original_fragment.language.iso
        l2 = alignment.translated_fragment.language.iso
        return reverse('annotations:list', args=(l1, l2,))

    def get_alignment(self):
        """Retrieves the Alignment from the object."""
        if not self.alignment:
            self.alignment = self.get_alignments().get(pk=self.object.alignment.pk)
        return self.alignment


class AnnotationCreate(AnnotationMixin, RevisionCreateMixin, generic.CreateView):
    success_message = 'Annotation created successfully'

    def get_success_url(self):
        """Go to the choose-view to select a new Alignment."""
        alignment = self.object.alignment
        return reverse('annotations:choose', args=(alignment.original_fragment.document.corpus.pk,
                                                   alignment.original_fragment.language.iso,
                                                   alignment.translated_fragment.language.iso))

    def form_valid(self, form):
        """Sets the User and Alignment on the created instance."""
        form.instance.annotated_by = self.request.user
        form.instance.alignment = self.get_alignment()
        return super(AnnotationCreate, self).form_valid(form)

    def get_alignment(self):
        """Retrieves the Alignment by the pk in the kwargs."""
        if not self.alignment:
            self.alignment = get_object_or_404(self.get_alignments(), pk=self.kwargs['pk'])
        return self.alignment


class AnnotationUpdate(AnnotationUpdateMixin, generic.UpdateView):
    success_message = 'Annotation edited successfully'

    def form_valid(self, form):
        """Sets the last modified by on the instance."""
        form.instance.last_modified_by = self.request.user
        return super(AnnotationUpdate, self).form_valid(form)


class AnnotationDelete(AnnotationUpdateMixin, generic.DeleteView):
    success_message = 'Annotation deleted successfully'


class AnnotationChoose(PermissionRequiredMixin, generic.RedirectView):
    permanent = False
    pattern_name = 'annotations:create'
    permission_required = 'annotations.change_annotation'

    def get_redirect_url(self, *args, **kwargs):
        """Redirects to the next open Alignment."""
        l1 = Language.objects.get(iso=self.kwargs['l1'])
        l2 = Language.objects.get(iso=self.kwargs['l2'])
        corpus = Corpus.objects.get(pk=int(self.kwargs['corpus'])) if 'corpus' in self.kwargs else None
        next_alignment = get_next_alignment(self.request.user, l1, l2, corpus)

        # If no next Alignment has been found, redirect to the status overview
        if not next_alignment:
            messages.success(self.request, 'All work is done for this language pair!')
            return reverse('annotations:status')

        corpus_pk = next_alignment.original_fragment.document.corpus.pk
        return super().get_redirect_url(corpus_pk, next_alignment.pk)


############
# CRUD Fragment
############
class FragmentDetailMixin(generic.DetailView):
    model = Fragment

    def get_object(self, queryset=None):
        qs = Fragment.objects \
            .select_related('document__corpus', 'language', 'tense') \
            .prefetch_related('original', 'sentence_set__word_set')
        fragment = super().get_object(qs)
        if fragment.document.corpus not in get_available_corpora(self.request.user):
            raise PermissionDenied

        referer_url = self.request.headers.get('referer', '')
        allowed_referers = referer_url.endswith((reverse('stats:fragment_table'), reverse('stats:fragment_table_mds')))
        if not (self.request.user.is_authenticated or allowed_referers):
            raise PermissionDenied

        return fragment


class FragmentDetail(LimitedPublicAccessMixin, FragmentDetailMixin):

    def get_context_data(self, **kwargs):
        context = super(FragmentDetail, self).get_context_data(**kwargs)

        fragment = self.object
        limit = 5 if self.request.user.is_authenticated else 1  # TODO: magic number
        doc_sentences = get_xml_sentences(fragment, limit)

        context['sentences'] = doc_sentences or fragment.sentence_set.all()
        context['limit'] = limit

        if not self.request.user.is_authenticated:
            scenario_pk = self.request.session.get('scenario_pk', None)
            if scenario_pk is None:
                raise ValueError('Scenario must be known')
            # Don't fetch the PickledObjectFields
            scenario = Scenario.objects \
                .defer('mds_model', 'mds_matrix', 'mds_fragments', 'mds_labels') \
                .get(pk=scenario_pk)
            context['public_languages'] = [lang.iso for lang in scenario.languages()]

        return context


class FragmentDetailPlain(LoginRequiredMixin, FragmentDetailMixin):
    template_name = 'annotations/fragment_detail_plain.html'


class FragmentRevisionWithCommentMixin(RevisionWithCommentMixin):
    def format_change_for_field(self, field, value):
        if field == 'formal_structure':
            return 'formal structure to ' + find_in_enum(value, Fragment.FORMAL_STRUCTURES)
        if field == 'sentence_function':
            return 'sentence function to ' + find_in_enum(value, Fragment.SENTENCE_FUNCTIONS)
        return super().format_change_for_field(field, value)


class FragmentEdit(SelectSegmentMixin, LoginRequiredMixin, FragmentRevisionWithCommentMixin, generic.UpdateView):
    model = Fragment
    form_class = FragmentForm

    def get_context_data(self, **kwargs):
        """Sets the annotated Words on the context."""
        context = super(FragmentEdit, self).get_context_data(**kwargs)
        context['annotated_words'] = self.object.targets()
        return context

    def get_success_url(self):
        return reverse('annotations:show', args=(self.object.pk,))

    def form_valid(self, form):
        """Updates the target words."""
        for word in Word.objects.filter(sentence__fragment=self.object):
            word.is_target = word in form.cleaned_data['words']
            word.save()
        return super(FragmentEdit, self).form_valid(form)


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

            # Additional sanity check:
            # happens if the language is not defined as a Corpus language, but nevertheless Annotations exist.
            if languages.get(language):
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
        qs = Source.objects.select_related('document__corpus', 'language')
        source = super(SourceDetail, self).get_object(qs)
        return source

    def get_context_data(self, **kwargs):
        context = super(SourceDetail, self).get_context_data(**kwargs)

        source = self.object
        tree, failed_lookups = bind_annotations_to_xml(source)
        additional_sources = Source.objects \
            .filter(document=source.document) \
            .exclude(pk=source.pk) \
            .select_related('language')

        transform = etree.XSLT(etree.fromstring(render_to_string('annotations/xml_transform.xslt').encode('utf-8')))
        context['sentences'] = [transform(p) for p in tree.iter('p', 'head')]
        context['failed_lookups'] = failed_lookups
        context['additional_sources'] = additional_sources
        context['rows'] = [(x,) for x in context['sentences']]

        additional_source = self.request.GET.get('additional_source')
        if additional_source:
            source = get_object_or_404(Source, pk=additional_source)
            add_tree, add_failed_lookups = bind_annotations_to_xml(source)

            context['additional_source'] = source
            context['additional_sentences'] = [transform(p) for p in add_tree.iter('p', 'head')]
            context['failed_lookups'] = context['failed_lookups'].extend(add_failed_lookups)
            context['rows'] = zip(context['sentences'], context['additional_sentences'])

        return context


############
# List views
############
class AnnotationList(PermissionRequiredMixin, FluidMixin, FilterView):
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
                              'alignment__original_fragment__labels',
                              'labels',
                              'words') \
            .order_by('-annotated_at')

    def get_filterset(self, filterset_class):
        kwargs = self.get_filterset_kwargs(filterset_class)
        request = kwargs['request']
        l1, l2 = request.resolver_match.kwargs['l1'], request.resolver_match.kwargs['l2']
        session_key = 'annotation_filter_{}_{}'.format(l1, l2)
        if kwargs['data']:
            request.session[session_key] = kwargs['data'].urlencode()
        elif session_key in request.session:
            kwargs['data'] = QueryDict(request.session[session_key])
        return filterset_class(l1, l2, **kwargs)


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
        Sets the current language and other_languages on the context.
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


class TenseCategoryList(PermissionRequiredMixin, FluidMixin, generic.ListView):
    model = TenseCategory
    context_object_name = 'tensecategories'
    template_name = 'annotations/tenses.html'
    permission_required = 'annotations.change_annotation'

    def get_context_data(self, **kwargs):
        """
        Sets the tenses and languages on the context.
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


class LabelList(PermissionRequiredMixin, FluidMixin, generic.ListView):
    model = LabelKey
    context_object_name = 'labelkeys'
    template_name = 'annotations/labels.html'
    permission_required = 'annotations.change_annotation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        corpus = self.kwargs.get('corpus')
        if corpus:
            corpus = Corpus.objects.get(pk=corpus)
        else:
            corpus = get_available_corpora(self.request.user)[0]
        self.object_list = self.object_list.filter(corpora=corpus)

        context['label_keys'] = self.object_list
        labels = [key.labels.all() for key in self.object_list]

        # transpose the 2d array stored in labels so that we could have each label key
        # show in a column on the html table
        transposed = []
        max_len = max([len(x) for x in labels]) if labels else 0
        for i in range(max_len):
            transposed.append([])
            for group in labels:
                if len(group) > i:
                    transposed[-1].append(group[i])
                else:
                    # add empty table cells
                    transposed[-1].append('')
        context['labels'] = transposed
        context['corpus'] = corpus
        context['corpora'] = get_available_corpora(self.request.user)
        return context


##############
# Export views
##############
class PrepareDownload(PrepareDownloadMixin, generic.TemplateView):
    template_name = 'annotations/download.html'


class ExportPOSPrepare(PermissionRequiredMixin, generic.View):
    permission_required = 'annotations.change_annotation'

    def get(self, request, *args, **kwargs):
        language = self.request.GET['language']
        corpus_id = self.request.GET['corpus']
        subcorpus_id = self.request.GET['subcorpus']
        document_id = self.request.GET['document']
        include_non_targets = 'include_non_targets' in self.request.GET
        add_lemmata = 'add_lemmata' in self.request.GET

        pos_file = NamedTemporaryFile(delete=False)
        self.request.session['pos_file'] = pos_file.name

        corpus = Corpus.objects.get(pk=int(corpus_id))
        subcorpus = SubCorpus.objects.get(pk=int(subcorpus_id)) if subcorpus_id != 'all' else None
        document = Document.objects.get(pk=int(document_id)) if document_id != 'all' else None
        document_title = document.title if document_id != 'all' else 'all'

        filename = '{}-{}-{}.xlsx'.format(urlquote(corpus.title), urlquote(document_title), language)
        self.request.session['pos_filename'] = filename
        export_annotations(pos_file.name, XLSX, corpus, language,
                           subcorpus=subcorpus, document=document,
                           include_non_targets=include_non_targets, add_lemmata=add_lemmata)

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


##############
# Import views
##############
class ImportLabelsView(SuperuserRequiredMixin, ImportMixin):
    """
    Allows superusers to import labels to Annotations and Fragments.
    """
    form_class = LabelImportForm
    template_name = 'annotations/label_form.html'
    success_message = 'Successfully imported the labels!'

    def get_success_url(self):
        return reverse('annotations:import-labels')


class AddFragmentsView(SuperuserRequiredMixin, ImportFragmentsMixin):
    """
    Allows superusers to import Fragments.
    """
    form_class = AddFragmentsForm
    template_name = 'annotations/add_fragments_form.html'
    success_message = 'Successfully added the fragments!'

    def get_success_url(self):
        return reverse('annotations:add-fragments')
