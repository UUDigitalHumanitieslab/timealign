from itertools import permutations

from django.contrib.messages.views import SuccessMessageMixin
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.views import generic

from django_filters.views import FilterView

from .filters import AnnotationFilter
from .forms import AnnotationForm
from .models import Annotation, Alignment, Fragment


class StartView(generic.TemplateView):
    template_name = 'annotations/start.html'


class InstructionsView(generic.TemplateView):
    def get_template_names(self):
        return 'annotations/instructions{}.html'.format(self.kwargs['n'])


class ContactView(generic.TemplateView):
    template_name = 'annotations/contact.html'


class HomeView(generic.TemplateView):
    template_name = 'annotations/home.html'

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)

        languages = []
        for l1, l2 in permutations(Fragment.LANGUAGES, 2):
            alignments = Alignment.objects.filter(original_fragment__language=l1[0], translated_fragment__language=l2[0])
            total = alignments.count()
            annotated = alignments.exclude(annotation=None).count()
            languages.append((l1, l2, annotated, total))
        context['languages'] = languages

        return context


class AnnotationList(FilterView):
    context_object_name = 'annotations'
    filterset_class = AnnotationFilter

    def get_queryset(self):
        return Annotation.objects.filter(alignment__original_fragment__language=self.kwargs['l1'],
                                         alignment__translated_fragment__language=self.kwargs['l2'])


class AnnotationCreate(generic.CreateView, SuccessMessageMixin):
    model = Annotation
    form_class = AnnotationForm
    success_message = 'Annotation added'

    def get_form_kwargs(self):
        """Sets the Alignment as a form kwarg"""
        kwargs = super(AnnotationCreate, self).get_form_kwargs()
        kwargs['alignment'] = self.get_alignment()
        return kwargs

    def get_success_url(self):
        """Find a new Alignment to annotate in the same original and translated language"""
        alignment = self.object.alignment
        new_alignment = get_random_alignment(alignment.original_fragment.language,
                                             alignment.translated_fragment.language)
        return reverse('annotations:annotate', args=(new_alignment.pk,))

    def get_context_data(self, **kwargs):
        """Sets the Alignment on the context"""
        context = super(AnnotationCreate, self).get_context_data(**kwargs)
        context['alignment'] = self.get_alignment()
        return context

    def form_valid(self, form):
        """Sets the User and Alignment on the created instance"""
        form.instance.annotated_by = self.request.user
        form.instance.alignment = self.get_alignment()
        return super(AnnotationCreate, self).form_valid(form)

    def get_alignment(self):
        """Retrieves the Alignment by the pk in the kwargs"""
        return get_object_or_404(Alignment, pk=self.kwargs['pk'])


class AnnotationChoose(generic.RedirectView):
    permanent = False
    pattern_name = 'annotations:annotate'

    def get_redirect_url(self, *args, **kwargs):
        new_alignment = get_random_alignment(self.kwargs['l1'], self.kwargs['l2'])
        return super(AnnotationChoose, self).get_redirect_url(new_alignment.pk)


def get_random_alignment(language_from, language_to):
    return Alignment.objects.filter(
        original_fragment__language=language_from,
        translated_fragment__language=language_to,
        annotation=None).order_by('?').first()
