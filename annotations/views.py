from itertools import permutations

from django.contrib.messages.views import SuccessMessageMixin
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.views import generic

from django_filters.views import FilterView

from .filters import AnnotationFilter
from .forms import AnnotationForm
from .models import Annotation, Alignment, Fragment
from .utils import get_random_alignment


##############
# Static views
##############
class StartView(generic.TemplateView):
    """Loads a static start view"""
    template_name = 'annotations/start.html'


class InstructionsView(generic.TemplateView):
    """Loads the various steps of the instructions"""
    def get_template_names(self):
        return 'annotations/instructions{}.html'.format(self.kwargs['n'])


class ContactView(generic.TemplateView):
    """Loads a static contact view"""
    template_name = 'annotations/contact.html'


class HomeView(generic.TemplateView):
    template_name = 'annotations/home.html'

    def get_context_data(self, **kwargs):
        """Creates a list of tuples with information on the annotation progress"""
        context = super(HomeView, self).get_context_data(**kwargs)

        languages = []
        for l1, l2 in permutations(Fragment.LANGUAGES, 2):
            alignments = Alignment.objects.filter(original_fragment__language=l1[0],
                                                  translated_fragment__language=l2[0])
            total = alignments.count()
            annotated = alignments.exclude(annotation=None).count()
            languages.append((l1, l2, annotated, total))
        context['languages'] = languages

        return context


#################
# CRUD Annotation
#################
class AnnotationMixin(object):
    model = Annotation
    form_class = AnnotationForm

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


class AnnotationCreate(AnnotationMixin, SuccessMessageMixin, generic.CreateView):
    success_message = 'Annotation created successfully'

    def get_success_url(self):
        """Find a new Alignment to annotate in the same original and translated language"""
        alignment = self.object.alignment
        new_alignment = get_random_alignment(alignment.original_fragment.language,
                                             alignment.translated_fragment.language)
        return reverse('annotations:create', args=(new_alignment.pk,))

    def form_valid(self, form):
        """Sets the User and Alignment on the created instance"""
        form.instance.annotated_by = self.request.user
        form.instance.alignment = self.get_alignment()
        return super(AnnotationCreate, self).form_valid(form)

    def get_alignment(self):
        """Retrieves the Alignment by the pk in the kwargs"""
        return get_object_or_404(Alignment, pk=self.kwargs['pk'])


class AnnotationUpdate(AnnotationMixin, SuccessMessageMixin, generic.UpdateView):
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
        """Sets the last modified by on the instance (TODO: actually save this!)"""
        form.instance.last_modified_by = self.request.user
        return super(AnnotationUpdate, self).form_valid(form)

    def get_alignment(self):
        """Retrieves the Alignment from the object"""
        return self.object.alignment


class AnnotationChoose(generic.RedirectView):
    permanent = False
    pattern_name = 'annotations:create'

    def get_redirect_url(self, *args, **kwargs):
        """Redirects to a random Alignment"""
        new_alignment = get_random_alignment(self.kwargs['l1'], self.kwargs['l2'])
        return super(AnnotationChoose, self).get_redirect_url(new_alignment.pk)


############
# List views
############
class AnnotationList(FilterView):
    context_object_name = 'annotations'
    filterset_class = AnnotationFilter
    paginate_by = 25

    def get_queryset(self):
        """
        Retrieves all Annotations for the given source (l1) and target (l2) language.
        :return: A QuerySet of Annotations.
        """
        return Annotation.objects.filter(alignment__original_fragment__language=self.kwargs['l1'],
                                         alignment__translated_fragment__language=self.kwargs['l2'])


class FragmentList(generic.ListView):
    context_object_name = 'fragments'
    template_name = 'annotations/fragment_list.html'
    paginate_by = 25

    def get_queryset(self):
        """
        Retrieves all Fragments for the given language that have an Annotation that contains a target expression.
        :return: A QuerySet of Fragments.
        """
        return Fragment.objects.filter(language=self.kwargs['language'], original__annotation__is_no_target=False)

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
        return context
