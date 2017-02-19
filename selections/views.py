from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.views import generic

from braces.views import PermissionRequiredMixin
from django_filters.views import FilterView

from annotations.utils import get_available_corpora

from .filters import SelectionFilter
from .forms import SelectionForm
from .models import PreProcessFragment, Selection
from .utils import get_random_fragment


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

        corpora = get_available_corpora(self.request.user)

        languages = []
        for language in PreProcessFragment.LANGUAGES:
            fragments = PreProcessFragment.objects.filter(language=language[0], needs_selection=True)

            # Only select PreProcessFragments from the available corpora for the current User
            fragments = fragments.filter(document__corpus__in=corpora)

            total = fragments.count()
            completed = fragments.exclude(selection=None).count()
            languages.append((language, completed, total))
        context['languages'] = languages
        context['current_corpora'] = corpora

        return context


################
# CRUD Selection
################
class SelectionMixin(SuccessMessageMixin, PermissionRequiredMixin):
    model = Selection
    form_class = SelectionForm
    permission_required = 'selections.change_selection'

    def get_form_kwargs(self):
        """Sets the PreProcessFragment as a form kwarg"""
        kwargs = super(SelectionMixin, self).get_form_kwargs()
        kwargs['fragment'] = self.get_fragment()
        return kwargs

    def get_context_data(self, **kwargs):
        """Sets the PreProcessFragment on the context"""
        context = super(SelectionMixin, self).get_context_data(**kwargs)
        context['fragment'] = self.get_fragment()
        return context

    def get_fragment(self):
        raise NotImplementedError


class SelectionCreate(SelectionMixin, generic.CreateView):
    success_message = 'Verb phrase selection successfully created'

    def get_success_url(self):
        """Go to the choose-view to select a new Alignment"""
        return reverse('selections:choose', args=(self.get_fragment().language, ))

    def form_valid(self, form):
        """Sets the User and Fragment on the created instance"""
        form.instance.selected_by = self.request.user
        form.instance.fragment = self.get_fragment()
        return super(SelectionCreate, self).form_valid(form)

    def get_fragment(self):
        """Retrieves the Fragment by the pk in the kwargs"""
        return get_object_or_404(PreProcessFragment, pk=self.kwargs['pk'])


class SelectionUpdate(SelectionMixin, generic.UpdateView):
    success_message = 'Verb phrase selection successfully edited'

    def get_context_data(self, **kwargs):
        """Sets the selected Words on the context"""
        context = super(SelectionUpdate, self).get_context_data(**kwargs)
        context['annotated_words'] = self.object.words.all()
        return context

    def get_success_url(self):
        """Returns to the overview per language"""
        return reverse('selections:list', args=(self.get_fragment().language,))

    def form_valid(self, form):
        """Sets the last modified by on the instance"""
        form.instance.last_modified_by = self.request.user
        return super(SelectionUpdate, self).form_valid(form)

    def get_fragment(self):
        """Retrieves the PreProcessFragment from the object"""
        return self.object.fragment


class SelectionChoose(PermissionRequiredMixin, generic.RedirectView):
    permanent = False
    pattern_name = 'selections:create'
    permission_required = 'selections.change_selection'

    def get_redirect_url(self, *args, **kwargs):
        """Redirects to a random Alignment"""
        new_alignment = get_random_fragment(self.request.user, self.kwargs['language'])

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
        selections = Selection.objects.filter(fragment__language=self.kwargs['language'])

        selections = selections.filter(fragment__document__corpus__in=get_available_corpora(self.request.user))

        return selections
