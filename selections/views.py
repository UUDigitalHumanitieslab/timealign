from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, redirect
from django.views import generic

from braces.views import PermissionRequiredMixin
from django_filters.views import FilterView

from annotations.models import Language
from annotations.utils import get_available_corpora

from .filters import SelectionFilter
from .forms import SelectionForm
from .models import PreProcessFragment, Selection
from .utils import get_random_fragment, get_selection_order


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
            completed = fragments.filter(selection__selected_by=user, selection__is_final=True).count()
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

    def get_form_kwargs(self):
        """Sets the PreProcessFragment as a form kwarg"""
        kwargs = super(SelectionMixin, self).get_form_kwargs()
        kwargs['fragment'] = self.get_fragment()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Sets the PreProcessFragment on the context"""
        context = super(SelectionMixin, self).get_context_data(**kwargs)
        context['fragment'] = self.get_fragment()
        context['selected_words'] = self.get_fragment().selected_words(self.request.user)
        return context

    def get_fragment(self):
        raise NotImplementedError

    def is_final(self):
        return 'is_final' in self.request.POST


class SelectionUpdateMixin(SelectionMixin):
    def get_context_data(self, **kwargs):
        """Sets the selected Words on the context"""
        context = super(SelectionUpdateMixin, self).get_context_data(**kwargs)
        context['annotated_words'] = self.object.words.all()
        return context

    def get_fragment(self):
        """Retrieves the PreProcessFragment from the object"""
        return self.object.fragment


class SelectionCreate(SelectionMixin, generic.CreateView):
    def get_success_url(self):
        """Go to the choose-view to select a new Alignment"""
        if self.is_final():
            return reverse('selections:choose', args=(self.get_fragment().language.iso, ))
        else:
            return reverse('selections:create', args=(self.get_fragment().pk, ))

    def form_valid(self, form):
        """Sets the User and Fragment on the created instance"""
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
        return get_object_or_404(PreProcessFragment, pk=self.kwargs['pk'])


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