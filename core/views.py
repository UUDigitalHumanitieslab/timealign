from django.db.models import Prefetch
from django.shortcuts import redirect
from django.utils import translation
from django.views import generic
from django.views.generic.base import View

from annotations.utils import get_available_corpora
from core.mixins import LimitedPublicAccessMixin
from stats.models import Scenario, ScenarioLanguage


class ActivateLanguageView(View):
    language_code = ''
    redirect_to = ''

    def get(self, request, *args, **kwargs):
        self.redirect_to = request.META.get('HTTP_REFERER')
        self.language_code = kwargs.get('language_code')
        translation.activate(self.language_code)
        request.session[translation.LANGUAGE_SESSION_KEY] = self.language_code
        return redirect(self.redirect_to)


class PublicScenarioList(LimitedPublicAccessMixin, generic.TemplateView):
    """Shows a list of Scenarios for different target groups"""
    model = Scenario
    template_name = 'stats/public_scenario_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        scenario_list_kwargs = {'corpus__in': get_available_corpora(self.request.user), 'is_public': True}
        # TODO Bram: Is it necessary to add extra filter for teachers vs students?
        languages_from = ScenarioLanguage.objects.filter(as_from=True).select_related('language')
        languages_to = ScenarioLanguage.objects.filter(as_to=True).select_related('language')
        scenarios = Scenario.objects \
            .filter(**scenario_list_kwargs) \
            .exclude(last_run__isnull=True) \
            .select_related('corpus') \
            .prefetch_related(Prefetch('scenariolanguage_set', queryset=languages_from, to_attr='languages_from'),
                              Prefetch('scenariolanguage_set', queryset=languages_to, to_attr='languages_to')) \
            .order_by('corpus__title') \
            .defer('mds_model', 'mds_matrix', 'mds_fragments', 'mds_labels')  # Don't fetch the PickledObjectFields

        context['scenarios'] = scenarios
        return context
