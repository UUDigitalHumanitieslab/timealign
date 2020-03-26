from tempfile import NamedTemporaryFile

from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views import generic
from django.utils.http import urlquote

from django.contrib.auth.mixins import PermissionRequiredMixin
from django_filters.views import FilterView

from annotations.models import Language, Corpus, Document
from annotations.utils import get_available_corpora

from .exports import export_selections
from .filters import SelectionFilter
from .forms import SelectionForm
from .models import PreProcessFragment, Selection
from .utils import get_random_fragment, get_selection_order

from core.utils import XLSX


##############
# Static views
##############
class IntroductionView(generic.TemplateView):
    """Loads a static introduction view"""
    template_name = 'selections/introduction.html'


class InstructionsView(generic.TemplateView):
    """Loads the various steps of the instructions"""
    def get_template_names(self):
        return 'selections/instructions{}.html'.format(self.kwargs['n'])


class StatusView(PermissionRequiredMixin, generic.TemplateView):
    """Loads a static home view, with an overview of the selection progress"""
    template_name = 'selections/home.html'
    permission_required = 'selections.change_selection'

    def get_context_data(self, **kwargs):
        """Creates a list of tuples with information on the selection progress"""
        context = super(StatusView, self).get_context_data(**kwargs)

        user = self.request.user
        corpora = get_available_corpora(user)

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
        context['current_corpora'] = corpora

        return context


################
# CRUD Selection
################
class SelectionMixin(PermissionRequiredMixin):
    model = Selection
    form_class = SelectionForm
    permission_required = 'selections.change_selection'

    def __init__(self):
        """Creates an attribute to cache the PreProcessFragment"""
        super(SelectionMixin, self).__init__()
        self.fragment = None

    def get_form_kwargs(self):
        """Sets the PreProcessFragment as a form kwarg"""
        kwargs = super(SelectionMixin, self).get_form_kwargs()
        kwargs['fragment'] = self.get_fragment()
        kwargs['user'] = self.request.user
        kwargs['select_segment'] = self.request.session.get('select_segment', False)
        return kwargs

    def get_context_data(self, **kwargs):
        """Sets the PreProcessFragment on the context"""
        context = super(SelectionMixin, self).get_context_data(**kwargs)
        context['fragment'] = self.get_fragment()
        context['selected_words'] = self.get_fragment().selected_words()
        return context

    def get_fragment(self):
        raise NotImplementedError

    def get_fragments(self):
        """Retrieve related fields on PreProcessFragment to prevent extra queries"""
        return PreProcessFragment.objects. \
            select_related('document__corpus', 'language'). \
            prefetch_related('sentence_set', 'selection_set__words')

    def is_final(self):
        return 'is_final' in self.request.POST

    def form_valid(self, form):
        # save user preferred selection tool on the session
        self.request.session['select_segment'] = form.cleaned_data['select_segment']
        return super().form_valid(form)


class SelectionUpdateMixin(SelectionMixin):
    def get_context_data(self, **kwargs):
        """Sets the selected Words on the context"""
        context = super(SelectionUpdateMixin, self).get_context_data(**kwargs)
        context['annotated_words'] = self.object.words.all()
        return context

    def get_fragment(self):
        """Retrieves the PreProcessFragment from the object"""
        if not self.fragment:
            self.fragment = self.get_fragments().get(pk=self.object.fragment.pk)
        return self.fragment


class SelectionCreate(SelectionMixin, generic.CreateView):
    def get_success_url(self):
        """Go to the choose-view to select a new Alignment"""
        if self.is_final():
            return reverse('selections:choose', args=(self.get_fragment().language.iso, ))
        else:
            return reverse('selections:create', args=(self.get_fragment().pk, ))

    def form_valid(self, form):
        """Sets the User and Fragment on the created instance"""

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

        if form.instance.is_no_target:
            form.instance.tense = ''

        return super(SelectionCreate, self).form_valid(form)

    def get_fragment(self):
        """Retrieves the Fragment by the pk in the kwargs"""
        if not self.fragment:
            self.fragment = get_object_or_404(self.get_fragments(), pk=self.kwargs['pk'])
        return self.fragment


class SelectionUpdate(SelectionUpdateMixin, generic.UpdateView):
    def get_success_url(self):
        """
        Returns to the overview per language on final Selection,
        otherwise, show a new Selection for the current PreProcessFragment
        """
        if self.is_final():
            return reverse('selections:list', args=(self.get_fragment().language.iso,))
        else:
            return reverse('selections:create', args=(self.get_fragment().pk, ))

    def form_valid(self, form):
        """Sets the last modified by on the instance"""
        form.instance.is_final = self.is_final()
        form.instance.last_modified_by = self.request.user

        if form.instance.is_no_target:
            form.instance.tense = ''

        return super(SelectionUpdate, self).form_valid(form)


class SelectionDelete(SelectionUpdateMixin, generic.DeleteView):
    def get_success_url(self):
        """Returns to the overview per Language"""
        return reverse('selections:list', args=(self.get_fragment().language.iso,))


class SelectionChoose(PermissionRequiredMixin, generic.RedirectView):
    permanent = False
    pattern_name = 'selections:create'
    permission_required = 'selections.change_selection'

    def get_redirect_url(self, *args, **kwargs):
        """Redirects to a random Alignment"""
        l = Language.objects.get(iso=self.kwargs['language'])
        new_alignment = get_random_fragment(self.request.user, l)

        # If no new alignment has been found, redirect to the status overview
        if not new_alignment:
            messages.success(self.request, 'All work is done for this language!')
            return reverse('selections:status')

        return super(SelectionChoose, self).get_redirect_url(new_alignment.pk)


############
# List views
############
class SelectionList(PermissionRequiredMixin, FilterView):
    context_object_name = 'selections'
    filterset_class = SelectionFilter
    paginate_by = 25
    permission_required = 'selections.change_selection'

    def get_queryset(self):
        """
        Retrieves all Selections for the given language.
        :return: A QuerySet of Selections.
        """
        corpora = get_available_corpora(self.request.user)
        return Selection.objects \
            .filter(fragment__language__iso=self.kwargs['language']) \
            .filter(fragment__document__corpus__in=corpora)


############
# Download views
############
class PrepareDownload(generic.TemplateView):
    template_name = 'selections/download.html'

    def get_context_data(self, **kwargs):
        context = super(PrepareDownload, self).get_context_data(**kwargs)

        corpora = get_available_corpora(self.request.user)
        language = Language.objects.get(iso=kwargs['language'])
        corpora = corpora.filter(languages=language)
        selected_corpus = corpora.first()
        if kwargs.get('corpus'):
            selected_corpus = Corpus.objects.get(id=int(kwargs['corpus']))

        context['language'] = language
        context['corpora'] = corpora
        context['selected_corpus'] = selected_corpus
        return context


class SelectionsDownload(PermissionRequiredMixin, generic.View):
    permission_required = 'selections.change_selection'

    def get(self, request, *args, **kwargs):
        language = request.GET['language']
        corpus_id = request.GET['corpus']
        document_id = request.GET['document']

        with NamedTemporaryFile() as file_:
            corpus = Corpus.objects.get(id=int(corpus_id))
            if document_id == 'all':
                export_selections(file_.name, XLSX, corpus, language)
                title = 'all'
            else:
                document = Document.objects.get(id=int(document_id))
                export_selections(file_.name, XLSX, corpus, language, document=document)
                title = document.title

            response = HttpResponse(file_, content_type='application/xlsx')
            filename = '{}-{}-{}.xlsx'.format(urlquote(corpus.title),
                                              urlquote(title),
                                              language)
            response['Content-Disposition'] = \
                'attachment; filename={}'.format(filename)
            return response
