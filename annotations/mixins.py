from django.views import generic

from core.mixins import ImportMixin

from .models import Corpus, Language
from .utils import get_available_corpora


class PrepareDownloadMixin(generic.base.ContextMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

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


class SelectSegmentMixin:
    def get_form_kwargs(self):
        """Sets select_segment as a form kwarg."""
        kwargs = super().get_form_kwargs()
        kwargs['select_segment'] = self.request.session.get('select_segment', False)
        return kwargs

    def form_valid(self, form):
        """Save User-preferred selection tool on the session."""
        self.request.session['select_segment'] = form.cleaned_data['select_segment']
        return super(SelectSegmentMixin, self).form_valid(form)


class ImportFragmentsMixin(ImportMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['corpus'] = self.request.GET.get('corpus')
        return context

    def get_form_kwargs(self):
        """Sets the Corpus as a form kwarg."""
        kwargs = super().get_form_kwargs()
        kwargs['corpus'] = self.request.GET.get('corpus')
        return kwargs
