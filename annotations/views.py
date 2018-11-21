from collections import defaultdict
from tempfile import NamedTemporaryFile

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count
from django.urls import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views import generic
from django.utils.http import urlquote

from braces.views import LoginRequiredMixin, PermissionRequiredMixin, SuperuserRequiredMixin
from django_filters.views import FilterView

from .exports import export_pos_file
from .filters import AnnotationFilter
from .forms import AnnotationForm, LabelImportForm
from .models import Corpus, Document, Language, Fragment, Alignment, Annotation, TenseCategory, Tense
from .utils import get_random_alignment, get_available_corpora

from core.utils import XLSX


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
        completed = totals.exclude(annotation=None)

        # Convert the QuerySets into a list of tuples
        language_totals = []
        for total in totals:
            l1 = Language.objects.get(pk=total['original_fragment__language'])
            l2 = Language.objects.get(pk=total['translated_fragment__language'])
            available = total['count']

            # TODO: can we do this more elegantly, e.g. without a database call?
            complete = completed.filter(original_fragment__language=l1, translated_fragment__language=l2)
            if complete:
                complete = complete[0]['count']
            else:
                complete = 0

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

    def get_form_kwargs(self):
        """Sets the User and the Alignment as a form kwarg"""
        kwargs = super(AnnotationMixin, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['alignment'] = self.get_alignment()
        return kwargs

    def get_context_data(self, **kwargs):
        """Sets the Alignment on the context"""
        context = super(AnnotationMixin, self).get_context_data(**kwargs)
        context['alignment'] = self.get_alignment()
        return context

    def get_alignment(self):
        raise NotImplementedError


class AnnotationUpdateMixin(AnnotationMixin):
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
        return reverse('annotations:list', args=(l1, l2, ))

    def get_alignment(self):
        """Retrieves the Alignment from the object"""
        return self.object.alignment


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
        """Retrieves the Alignment by the pk in the kwargs, and also some related fields to speed up processing"""
        alignments = Alignment.objects.select_related('original_fragment',
                                                      'original_fragment__tense',
                                                      'original_fragment__language',
                                                      'original_fragment__document__corpus',
                                                      'translated_fragment',
                                                      'translated_fragment__language',
                                                      'translated_fragment__document')
        return get_object_or_404(alignments, pk=self.kwargs['pk'])


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
            messages.success(self.request, 'All work is done for this language pair!')
            return reverse('annotations:status')

        corpus_pk = new_alignment.original_fragment.document.corpus.pk
        return super(AnnotationChoose, self).get_redirect_url(corpus_pk, new_alignment.pk)


############
# CRUD Fragment
############
class FragmentDetail(LoginRequiredMixin, generic.DetailView):
    model = Fragment


############
# List views
############
class AnnotationList(PermissionRequiredMixin, FilterView):
    context_object_name = 'annotations'
    filterset_class = AnnotationFilter
    paginate_by = 25
    permission_required = 'annotations.change_annotation'

    def get_queryset(self):
        """
        Retrieves all Annotations for the given source (l1) and target (l2) language.
        :return: A QuerySet of Annotations.
        """
        return Annotation.objects \
            .filter(alignment__original_fragment__language__iso=self.kwargs['l1']) \
            .filter(alignment__translated_fragment__language__iso=self.kwargs['l2']) \
            .filter(alignment__original_fragment__document__corpus__in=get_available_corpora(self.request.user)) \
            .select_related('annotated_by',
                            'tense',
                            'alignment__original_fragment',
                            'alignment__original_fragment__document',
                            'alignment__translated_fragment') \
            .order_by('-annotated_at')


class FragmentList(PermissionRequiredMixin, generic.ListView):
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
        Sets all current languages on the context
        :return: The context variables.
        """
        context = super(TenseCategoryList, self).get_context_data(**kwargs)

        tenses = defaultdict(list)
        languages = []

        for language in Language.objects.all().order_by('iso'):
            if not Tense.objects.filter(language=language):
                continue

            languages.append(language)

            for tc in TenseCategory.objects.all():
                ts = Tense.objects.filter(category=tc, language=language).values_list('title', flat=True)
                tenses[tc.title].append(', '.join(ts))

        context['tenses'] = sorted(tenses.items())
        context['languages'] = languages

        return context


class PrepareDownload(generic.TemplateView):
    template_name = 'annotations/download.html'

    def get_context_data(self, **kwargs):
        context = super(PrepareDownload, self).get_context_data(**kwargs)

        language = kwargs['language']
        corpora = get_available_corpora(self.request.user)
        selected_corpus = corpora[0]
        if kwargs.get('corpus'):
            selected_corpus = Corpus.objects.get(id=int(kwargs['corpus']))

        context['language_to'] = Language.objects.get(iso=language)
        context['corpora'] = corpora
        context['selected_corpus'] = selected_corpus
        return context


class ExportPOSDownload(PermissionRequiredMixin, generic.View):
    permission_required = 'annotations.change_annotation'

    def get(self, request, *args, **kwargs):
        language = self.request.GET['language']
        corpus_id = self.request.GET['corpus']
        document_id = self.request.GET['document']
        include_non_targets = 'include_non_targets' in self.request.GET

        with NamedTemporaryFile() as file_:
            corpus = Corpus.objects.get(id=int(corpus_id))
            if document_id == 'all':
                export_pos_file(file_.name, XLSX, corpus, language, include_non_targets=include_non_targets)
                title = 'all'
            else:
                document = Document.objects.get(id=int(document_id))
                export_pos_file(file_.name, XLSX, corpus, language, include_non_targets=include_non_targets,
                                document=document)
                title = document.title

            response = HttpResponse(file_, content_type='application/xlsx')
            filename = '{}-{}-{}.xlsx'.format(urlquote(corpus.title),
                                              urlquote(title),
                                              language)
            response['Content-Disposition'] = \
                'attachment; filename={}'.format(filename)
            return response


class ImportLabelsView(LoginRequiredMixin, SuperuserRequiredMixin, generic.View):
    """
    Allows superusers to import labels to Annotations and Fragments
    """
    form_class = LabelImportForm
    template_name = 'annotations/label_form.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            try:
                form.save()
                messages.success(self.request, u'Successfully imported the labels!')
            except ValueError as e:
                messages.error(self.request, u'Error during import: {}'.format(e.message))
            return redirect(reverse('annotations:import-labels'))
        else:
            return render(request, self.template_name, {'form': form})
