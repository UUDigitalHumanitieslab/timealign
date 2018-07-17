import json
import numbers
import random
from collections import Counter, defaultdict
from pprint import pprint

from braces.views import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template.loader import get_template
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import six
from django.utils.encoding import iri_to_uri
from django.views import generic
from scipy.spatial import distance

from annotations.models import Fragment, Language, Tense, Document
from annotations.utils import get_available_corpora

from .models import Scenario
from .utils import get_tense_properties


class HttpResponseTemporaryRedirect(HttpResponse):
    status_code = 307

    def __init__(self, redirect_to):
        HttpResponse.__init__(self)
        self['Location'] = iri_to_uri(redirect_to)


class ScenarioList(LoginRequiredMixin, generic.ListView):
    """
    Shows a list of scenarios
    """
    model = Scenario
    context_object_name = 'scenarios'

    def filter_scenarios(self, scenarios, corpus=None, language=None,
                         show_test=False):
        """filter scenarios"""
        if not show_test:
            scenarios = scenarios.exclude(is_test=True)
        if corpus:
            scenarios = scenarios.filter(corpus__id=corpus)
        if language:
            scenarios = scenarios.filter(
                scenariolanguage__language__iso=language)

        # exclude scenarios that belong to corpora that the user is not allowed
        # to annotate
        scenarios = scenarios.filter(
            corpus__in=get_available_corpora(self.request.user))

        return scenarios

    def get_queryset(self):
        """
        Only show Scenarios that have been run,
        and if show_test is False, don't show test Scenarios either.
        Order the Scenarios by Corpus title.
        """
        show_test = self.request.GET.get('test')
        scenarios = Scenario.objects.exclude(last_run__isnull=True)
        corpus = self.request.GET.get('corpus')
        language = self.request.GET.get('language')
        scenarios = self.filter_scenarios(
            scenarios, corpus, language, show_test)

        scenarios = scenarios.exclude(owner=self.request.user)

        return scenarios.order_by('corpus__title')

    def get_context_data(self, **kwargs):
        context = super(ScenarioList, self).get_context_data(**kwargs)

        # get filters if set
        corpus = self.request.GET.get('corpus')
        language = self.request.GET.get('language')
        show_test = self.request.GET.get('test')

        corpora = get_available_corpora(self.request.user)
        # only show languages that are found in the available corpora
        languages = set(sum([list(c.languages.all()) for c in corpora], []))
        # sort by language name
        languages = sorted(languages, key=lambda x: x.title)

        # possible filter values
        context['corpora'] = corpora
        context['languages'] = languages
        context['show_test'] = show_test

        # preserve filter selection
        if corpus:
            context['selected_corpus'] = int(corpus)
        if language:
            context['selected_language'] = language

        # scenarios that belong to the current user are displayed seperately.
        # they need to be queried separately
        # because we should include test scenarios.
        user_scenarios = self.filter_scenarios(
            self.request.user.scenarios,
            corpus, language, show_test=True)
        context['user_scenarios'] = user_scenarios.all()

        return context


class ScenarioDetail(LoginRequiredMixin, generic.DetailView):
    """
    Shows details of a selected scenario
    """
    model = Scenario

    def get_object(self, queryset=None):
        """
        Only show Scenarios that have been run
        """
        scenario = super(ScenarioDetail, self).get_object(queryset)
        if scenario.corpus not in get_available_corpora(self.request.user):
            raise PermissionDenied
        if not scenario.last_run:
            raise Http404('Scenario has not been run')
        return scenario


class MDSView(ScenarioDetail):
    """Loads the matrix plot view"""
    model = Scenario
    template_name = 'stats/mds.html'

    def get_context_data(self, **kwargs):
        context = super(MDSView, self).get_context_data(**kwargs)

        # Retrieve kwargs
        scenario = self.object
        language = self.kwargs.get('language', scenario.languages().order_by(
            'language__iso').first().language.iso)
        # We choose dimensions to be 1-based
        d1 = int(self.kwargs.get('d1', 1))
        d2 = int(self.kwargs.get('d2', 2))

        language_object = get_object_or_404(Language, iso=language)
        if language_object not in [sl.language for sl in scenario.languages()]:
            raise Http404('Language {} does not exist in Scenario {}'.format(
                language_object, scenario.pk))

        # Retrieve pickled data
        model = scenario.mds_model
        tenses = scenario.mds_labels
        fragments = scenario.mds_fragments

        # Turn the pickled model into a scatterplot dictionary
        random.seed(scenario.pk)  # Fixed seed for random jitter
        j = defaultdict(list)
        for n, l in enumerate(model):
            # Retrieve x/y dimensions, add some jitter
            x = l[d1 - 1] + random.uniform(-.5, .5) / 100
            y = random.uniform(-.5, .5) / 100
            if d2 > 0:
                y += l[d2 - 1]

            f = fragments[n]
            fragment = Fragment.objects.get(pk=f)
            ts = [tenses[l][n] for l in tenses.keys()]
            t = [Tense.objects.get(pk=t).title if isinstance(
                t, numbers.Number) else t for t in ts]
            # Add all values to the dictionary
            j[tenses[language][n]].append(
                {'x': x, 'y': y, 'fragment_id': f,
                 'fragment': fragment.full(True), 'tenses': t})

        # Transpose the dictionary to the correct format for nvd3.
        # TODO: can this be done in the loop above?
        matrix = []
        labels = set()
        for tense, values in j.items():
            tense_label, tense_color = get_tense_properties(tense, len(labels))
            labels.add(tense_label)

            d = dict()
            d['key'] = tense_label
            d['color'] = tense_color
            d['values'] = values
            matrix.append(d)

        # Add all variables to the context
        context['matrix'] = json.dumps(matrix)
        context['language'] = language
        context['languages'] = Language.objects.filter(
            iso__in=tenses.keys()).order_by('iso')
        context['d1'] = d1
        context['d2'] = d2
        # We choose dimensions to be 1-based
        context['max_dimensions'] = range(1, len(model[0]) + 1)
        context['stress'] = scenario.mds_stress

        return context

    def post(self, request, pk):
        request.session['fragment_ids'] = json.loads(
            request.POST['fragment_ids'])
        url = reverse('stats:fragment_table', kwargs={'pk': pk})
        return HttpResponseRedirect(url)


class DescriptiveStatsView(ScenarioDetail):
    model = Scenario
    template_name = 'stats/descriptive.html'

    def get_context_data(self, **kwargs):
        context = super(DescriptiveStatsView, self).get_context_data(**kwargs)

        tenses = self.object.mds_labels
        languages = Language.objects.filter(iso__in=tenses.keys())

        counters = dict()
        tuples = defaultdict(tuple)
        colors = dict()

        for l in languages:
            c = Counter()
            n = 0
            labels = set()
            for t in tenses[l.iso]:
                tense_label, tense_color = get_tense_properties(t, len(labels))
                labels.add(tense_label)

                c.update([tense_label])
                tuples[n] += (tense_label,)
                n += 1

                if tense_label not in colors:
                    colors[tense_label] = tense_color

            counters[l] = c.most_common()

        context['counters'] = counters
        context['counters_json'] = json.dumps(
            {language.iso: values for language, values in counters.items()})
        context['tuples'] = Counter(tuples.values()).most_common()
        context['colors'] = json.dumps(colors)
        context['languages'] = json.dumps({l.iso: l.title for l in languages})

        return context


class FragmentTableView(MDSView, ScenarioDetail):
    model = Scenario
    template_name = 'stats/fragment_table.html'

    def get_context_data(self, **kwargs):
        context = super(FragmentTableView, self).get_context_data(**kwargs)
        fragment_ids = self.request.session['fragment_ids']
        # print(fragment_ids)
        # fragments_to_show = Fragment.objects.filter(id__in=fragment_ids)
        # print(len(fragments_to_show))
        # print(fragments_to_show)

        fragments = Fragment.objects.filter(id__in=fragment_ids)
        context['out'] = []
        for f in fragments:
            # print(f.id)
            # print(f.document.title)
            # print(f.xml_ids())
            # print(f.full(marked=True))
            # print('---------')
            context['out'].append(
                {
                    'fragment_id': f.id,
                    'doc_title': f.document.title,
                    'xml_ids': f.xml_ids(),
                    'target_words': f.target_words(),
                    'full': f.full(marked=True),
                }
            )

        return context
