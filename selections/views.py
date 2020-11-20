import os
from tempfile import NamedTemporaryFile

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect, QueryDict, JsonResponse
from django.shortcuts import get_object_or_404
from django.views import generic
from django.utils.http import urlquote

from braces.views import SuperuserRequiredMixin
from django_filters.views import FilterView

from annotations.mixins import PrepareDownloadMixin, SelectSegmentMixin, ImportFragmentsMixin
from annotations.models import Language, Corpus, Document
from annotations.utils import get_available_corpora
from core.mixins import FluidMixin
from core.utils import XLSX

from .exports import export_selections
from .filters import SelectionFilter
from .forms import AddPreProcessFragmentsForm, SelectionForm
from .models import PreProcessFragment, Selection
from .utils import get_next_fragment, get_selection_order


##############
# Static views
##############
class IntroductionView(generic.TemplateView):
    """
    Loads a static introduction view.
    """
    template_name = 'selections/introduction.html'


class InstructionsView(generic.TemplateView):
    """
    Loads the various steps of the instructions.
    """

    def get_template_names(self):
        return 'selections/instructions{}.html'.format(self.kwargs['n'])


class StatusView(PermissionRequiredMixin, generic.TemplateView):
    """
    Loads a static home view, with an overview of the selection progress.
    """
    template_name = 'selections/home.html'
    permission_required = 'selections.change_selection'

    def get_context_data(self, **kwargs):
        """Creates a list of tuples with information on the selection progress."""
        context = super(StatusView, self).get_context_data(**kwargs)

        corpus_pk = self.kwargs.get('pk', None)
        if corpus_pk:
            corpora = [get_object_or_404(Corpus, pk=corpus_pk)]
        else:
            corpora = get_available_corpora(self.request.user)

        languages = set()
        for corpus in corpora:
            for language in corpus.languages.all():
                languages.add(language)

        language_totals = []
        for language in languages:
            # Only select PreProcessFragments from the available corpora for the current User
            fragments = PreProcessFragment.objects \
                .filter(language=language) \
                .filter(document__corpus__in=corpora)

            total = fragments.count()
            completed = fragments.exclude(selection=None).count()
            language_totals.append((language, completed, total))

        context['languages'] = language_totals
        context['corpus_pk'] = corpus_pk
        context['current_corpora'] = corpora

        return context


################
# CRUD Selection
################
class SelectionMixin(SelectSegmentMixin, PermissionRequiredMixin):
    model = Selection
    form_class = SelectionForm
    permission_required = 'selections.change_selection'

    def __init__(self):
        """Creates an attribute to cache the PreProcessFragment."""
        super(SelectionMixin, self).__init__()
        self.fragment = None

    def get_form_kwargs(self):
        """Sets the PreProcessFragment as a form kwarg."""
        kwargs = super(SelectionMixin, self).get_form_kwargs()
        kwargs['fragment'] = self.get_fragment()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Sets the PreProcessFragment on the context."""
        context = super(SelectionMixin, self).get_context_data(**kwargs)
        context['fragment'] = self.get_fragment()
        context['selected_words'] = self.get_fragment().selected_words()
        return context

    def get_fragment(self):
        raise NotImplementedError

    def get_fragments(self):
        """Retrieve related fields on PreProcessFragment to prevent extra queries."""
        return PreProcessFragment.objects. \
            select_related('document__corpus', 'language'). \
            prefetch_related('sentence_set', 'selection_set__words')

    def is_final(self):
        return 'is_final' in self.request.POST


class SelectionUpdateMixin(SelectionMixin):
    def get_context_data(self, **kwargs):
        """Sets the selected Words on the context."""
        context = super(SelectionUpdateMixin, self).get_context_data(**kwargs)
        context['annotated_words'] = self.object.words.all()
        return context

    def get_fragment(self):
        """Retrieves the PreProcessFragment from the object."""
        if not self.fragment:
            self.fragment = self.get_fragments().get(pk=self.object.fragment.pk)
        return self.fragment


class SelectionCreate(SelectionMixin, generic.CreateView):
    def get_success_url(self):
        """Go to the choose-view to select a new Alignment."""
        if self.is_final():
            return reverse('selections:choose', args=(self.get_fragment().document.corpus.pk,
                                                      self.get_fragment().language.iso,))
        else:
            return reverse('selections:create', args=(self.get_fragment().pk,))

    def form_valid(self, form):
        """Sets the User and Fragment on the created instance."""
        # Set the previous Selection to is_final when the User signals the annotation has already been completed
        if 'already_complete' in self.request.POST:
            last_selection = self.get_fragment().selection_set.order_by('-order')[0]
            last_selection.is_final = True
            last_selection.save()

            return HttpResponseRedirect(self.get_success_url())

        fragment = self.get_fragment()
        user = self.request.user

        form.instance.selected_by = user
        form.instance.fragment = fragment
        form.instance.order = get_selection_order(fragment, user)
        form.instance.is_final = self.is_final()

        return super().form_valid(form)

    def get_fragment(self):
        """Retrieves the Fragment by the pk in the kwargs."""
        if not self.fragment:
            self.fragment = get_object_or_404(self.get_fragments(), pk=self.kwargs['pk'])
        return self.fragment


class SelectionUpdate(SelectionUpdateMixin, generic.UpdateView):
    def get_success_url(self):
        """
        Returns to the overview per language on final Selection,
        otherwise, show a new Selection for the current PreProcessFragment.
        """
        if self.is_final():
            return reverse('selections:list', args=(self.get_fragment().language.iso,))
        else:
            return reverse('selections:create', args=(self.get_fragment().pk,))

    def form_valid(self, form):
        """Sets the last modified by on the instance."""
        form.instance.is_final = self.is_final()
        form.instance.last_modified_by = self.request.user

        return super().form_valid(form)


class SelectionDelete(SelectionUpdateMixin, generic.DeleteView):
    def get_success_url(self):
        """Returns to the overview per Language."""
        return reverse('selections:list', args=(self.get_fragment().language.iso,))


class SelectionChoose(PermissionRequiredMixin, generic.RedirectView):
    permanent = False
    pattern_name = 'selections:create'
    permission_required = 'selections.change_selection'

    def get_redirect_url(self, *args, **kwargs):
        """Redirects to the next open PreProcessFragment."""
        language = Language.objects.get(iso=self.kwargs['language'])
        corpus = Corpus.objects.get(pk=int(self.kwargs['corpus'])) if 'corpus' in self.kwargs else None
        next_fragment = get_next_fragment(self.request.user, language, corpus)

        # If no next PreProcessFragment has been found, redirect to the status overview
        if not next_fragment:
            messages.success(self.request, 'All work is done for this language!')
            return reverse('selections:status')

        return super().get_redirect_url(next_fragment.pk)


############
# List views
############
class SelectionList(PermissionRequiredMixin, FluidMixin, FilterView):
    context_object_name = 'selections'
    filterset_class = SelectionFilter
    paginate_by = 25
    permission_required = 'selections.change_selection'

    def get_queryset(self):
        """
        Retrieves all Selections for the given language.
        :return: A QuerySet of Selections.
        """
        if 'corpus' in self.kwargs:
            corpora = [Corpus.objects.get(pk=int(self.kwargs['corpus']))]
        else:
            corpora = get_available_corpora(self.request.user)
        queryset = Selection.objects \
            .filter(fragment__language__iso=self.kwargs['language']) \
            .filter(fragment__document__corpus__in=corpora)

        queryset = queryset.select_related('fragment',
                                           'fragment__document',
                                           'fragment__document__corpus',
                                           'tense',
                                           'selected_by') \
            .prefetch_related('fragment__sentence_set__word_set',
                              'words')
        return queryset

    def get_filterset(self, filterset_class):
        kwargs = self.get_filterset_kwargs(filterset_class)
        request = kwargs['request']
        language = request.resolver_match.kwargs['language']
        session_key = 'selection_filter_{}'.format(language)
        if kwargs['data']:
            request.session[session_key] = kwargs['data'].urlencode()
        elif session_key in request.session:
            kwargs['data'] = QueryDict(request.session[session_key])
        return filterset_class(language, **kwargs)


##############
# Export views
##############
class PrepareDownload(PrepareDownloadMixin, generic.TemplateView):
    template_name = 'selections/download.html'


class SelectionsPrepare(PermissionRequiredMixin, generic.View):
    permission_required = 'selections.change_selection'

    def get(self, request, *args, **kwargs):
        language = request.GET['language']
        corpus_id = request.GET['corpus']
        document_id = request.GET['document']
        add_lemmata = 'add_lemmata' in self.request.GET

        pos_file = NamedTemporaryFile(delete=False)
        self.request.session['pos_file'] = pos_file.name

        corpus = Corpus.objects.get(pk=int(corpus_id))
        document = Document.objects.get(pk=int(document_id)) if document_id != 'all' else None
        document_title = document.title if document_id != 'all' else 'all'

        filename = '{}-{}-{}.xlsx'.format(urlquote(corpus.title), urlquote(document_title), language)
        self.request.session['pos_filename'] = filename
        export_selections(pos_file.name, XLSX, corpus, language,
                          document=document, add_lemmata=add_lemmata)

        return JsonResponse(dict(done=True))


class SelectionsDownload(PermissionRequiredMixin, generic.View):
    permission_required = 'selections.change_selection'

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
class AddPreProcessFragmentsView(SuperuserRequiredMixin, ImportFragmentsMixin):
    """
    Allows superusers to import PreProcessFragments.
    """
    form_class = AddPreProcessFragmentsForm
    template_name = 'selections/add_fragments_form.html'
    success_message = 'Successfully added the fragments!'

    def get_success_url(self):
        return reverse('selections:add-fragments')
