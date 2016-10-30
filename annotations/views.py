from collections import defaultdict
from itertools import permutations
import json
import pickle
import random

from django.conf import settings
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.views import generic

from braces.views import LoginRequiredMixin, PermissionRequiredMixin
from django_filters.views import FilterView

from .filters import AnnotationFilter
from .forms import AnnotationForm
from .models import Annotation, Alignment, Fragment, Corpus
from .utils import get_random_alignment, get_color


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

        languages = []
        for l1, l2 in permutations(Fragment.LANGUAGES, 2):
            alignments = Alignment.objects.filter(original_fragment__language=l1[0],
                                                  translated_fragment__language=l2[0])

            if settings.CURRENT_DOCUMENTS:
                alignments = alignments.filter(original_fragment__document__title__in=settings.CURRENT_DOCUMENTS)

            total = alignments.count()
            annotated = alignments.exclude(annotation=None).count()
            languages.append((l1, l2, annotated, total))
        context['languages'] = languages
        context['current_documents'] = settings.CURRENT_DOCUMENTS

        return context


class PlotMatrixView(LoginRequiredMixin, generic.DetailView):
    """Loads the matrix plot view"""
    model = Corpus
    template_name = 'annotations/plot_matrix.html'

    def get_context_data(self, **kwargs):
        context = super(PlotMatrixView, self).get_context_data(**kwargs)

        # Retrieve kwargs
        pk = self.object.pk
        language = self.kwargs.get('language', Fragment.ENGLISH)
        d1 = int(self.kwargs.get('d1', 1))  # We choose dimensions to be 1-based
        d2 = int(self.kwargs.get('d2', 2))

        # Retrieve lists generated with command python manage.py export_matrix
        pre = 'plots/{}_'.format(pk)
        model = pickle.load(open(pre + 'matrix.p', 'rb'))
        tenses = pickle.load(open(pre + 'tenses.p', 'rb'))
        fragments = pickle.load(open(pre + 'fragments.p', 'rb'))

        # Turn the pickled model into a scatterplot dictionary
        j = defaultdict(list)
        for n, l in enumerate(model):
            # Retrieve x/y dimensions, add some jitter
            x = l[d1 - 1] + random.uniform(-.5, .5) / 100
            y = l[d2 - 1] + random.uniform(-.5, .5) / 100

            f = fragments[n]
            t = [tenses[l][n] for l in tenses.keys()]
            # Add all values to the dictionary
            j[tenses[language][n]].append({'x': x, 'y': y, 'fragment_id': f, 'tenses': t})

        # Transpose the dictionary to the correct format for nvd3.
        # TODO: can this be done in the loop above?
        matrix = []
        for k, v in j.items():
            d = dict()
            d['key'] = k
            d['color'] = get_color(k)
            d['values'] = v
            matrix.append(d)

        # Add all variables to the context
        context['matrix'] = json.dumps(matrix)
        context['language'] = language
        context['languages'] = Fragment.LANGUAGES
        context['d1'] = d1
        context['d2'] = d2
        context['max_dimensions'] = range(1, len(model[0]) + 1)  # We choose dimensions to be 1-based

        return context


#################
# CRUD Annotation
#################
class AnnotationMixin(SuccessMessageMixin, PermissionRequiredMixin):
    model = Annotation
    form_class = AnnotationForm
    permission_required = 'annotations.change_annotation'

    def get_form_kwargs(self):
        """Sets the Alignment as a form kwarg"""
        kwargs = super(AnnotationMixin, self).get_form_kwargs()
        kwargs['alignment'] = self.get_alignment()
        return kwargs

    def get_context_data(self, **kwargs):
        """Sets the Alignment on the context"""
        context = super(AnnotationMixin, self).get_context_data(**kwargs)
        context['alignment'] = self.get_alignment()
        return context

    def get_alignment(self):
        raise NotImplementedError


class AnnotationCreate(AnnotationMixin, generic.CreateView):
    success_message = 'Annotation created successfully'

    def get_success_url(self):
        """Go to the choose-view to select a new Alignment"""
        alignment = self.object.alignment
        return reverse('annotations:choose', args=(alignment.original_fragment.language,
                                                   alignment.translated_fragment.language))

    def form_valid(self, form):
        """Sets the User and Alignment on the created instance"""
        form.instance.annotated_by = self.request.user
        form.instance.alignment = self.get_alignment()
        return super(AnnotationCreate, self).form_valid(form)

    def get_alignment(self):
        """Retrieves the Alignment by the pk in the kwargs"""
        return get_object_or_404(Alignment, pk=self.kwargs['pk'])


class AnnotationUpdate(AnnotationMixin, generic.UpdateView):
    success_message = 'Annotation edited successfully'

    def get_context_data(self, **kwargs):
        """Sets the annotated Words on the context"""
        context = super(AnnotationUpdate, self).get_context_data(**kwargs)
        context['annotated_words'] = self.object.words.all()
        return context

    def get_success_url(self):
        """Returns to the overview per language"""
        alignment = self.get_alignment()
        l1 = alignment.original_fragment.language
        l2 = alignment.translated_fragment.language
        return reverse('annotations:list', args=(l1, l2,))

    def form_valid(self, form):
        """Sets the last modified by on the instance"""
        form.instance.last_modified_by = self.request.user
        return super(AnnotationUpdate, self).form_valid(form)

    def get_alignment(self):
        """Retrieves the Alignment from the object"""
        return self.object.alignment


class AnnotationChoose(PermissionRequiredMixin, generic.RedirectView):
    permanent = False
    pattern_name = 'annotations:create'
    permission_required = 'annotations.change_annotation'

    def get_redirect_url(self, *args, **kwargs):
        """Redirects to a random Alignment"""
        new_alignment = get_random_alignment(self.kwargs['l1'], self.kwargs['l2'])

        # If no new alignment has been found, redirect to the status overview
        if not new_alignment:
            messages.success(self.request, 'All work is done for this language pair!')
            return reverse('annotations:status')

        return super(AnnotationChoose, self).get_redirect_url(new_alignment.pk)


############
# CRUD Fragment
############
class FragmentDetail(LoginRequiredMixin, generic.DetailView):
    model = Fragment


############
# List views
############
class CorporaList(PermissionRequiredMixin, generic.ListView):
    model = Corpus
    context_object_name = 'corpora'
    permission_required = 'annotations.change_annotation'


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
        annotations = Annotation.objects.filter(alignment__original_fragment__language=self.kwargs['l1'],
                                                alignment__translated_fragment__language=self.kwargs['l2'])

        if settings.CURRENT_DOCUMENTS:
            annotations = annotations.filter(alignment__original_fragment__document__title__in=settings.CURRENT_DOCUMENTS)

        return annotations


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
        fragments = Fragment.objects.filter(language=self.kwargs['language'])

        if settings.CURRENT_DOCUMENTS:
            fragments = fragments.filter(document__title__in=settings.CURRENT_DOCUMENTS)

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
        context['language'] = [f for l, f in Fragment.LANGUAGES if l == language][0]
        context['other_languages'] = [f for l, f in Fragment.LANGUAGES if l != language]

        context['show_tenses'] = self.kwargs.get('showtenses', False)

        return context
