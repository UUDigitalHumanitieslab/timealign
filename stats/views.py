from collections import defaultdict, Counter
import json
import numbers
import random

from django.http import Http404
from django.views import generic

from braces.views import LoginRequiredMixin

from .models import Scenario
from annotations.models import Language, Tense, Fragment
from annotations.utils import get_color


class ScenarioList(LoginRequiredMixin, generic.ListView):
    model = Scenario
    context_object_name = 'scenarios'

    def get_queryset(self):
        """
        Only show Scenarios that have been run
        """
        return Scenario.objects.exclude(last_run__isnull=True).order_by('corpus__title')


class ScenarioDetail(LoginRequiredMixin, generic.DetailView):
    model = Scenario

    def get_object(self, queryset=None):
        """
        Only show Scenarios that have been run
        """
        scenario = super(ScenarioDetail, self).get_object(queryset)
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
        language = self.kwargs.get('language', scenario.languages().order_by('language__iso').first().language.iso)
        d1 = int(self.kwargs.get('d1', 1))  # We choose dimensions to be 1-based
        d2 = int(self.kwargs.get('d2', 2))

        # Retrieve pickled data
        model = scenario.mds_model
        tenses = scenario.mds_labels
        fragments = scenario.mds_fragments

        # Turn the pickled model into a scatterplot dictionary
        j = defaultdict(list)
        for n, l in enumerate(model):
            # Retrieve x/y dimensions, add some jitter
            x = l[d1 - 1] + random.uniform(-.5, .5) / 100
            y = l[d2 - 1] + random.uniform(-.5, .5) / 100

            f = fragments[n]
            fragment = Fragment.objects.get(pk=f)
            ts = [tenses[l][n] for l in tenses.keys()]
            t = [Tense.objects.get(pk=t).title if isinstance(t, numbers.Number) else t for t in ts]
            # Add all values to the dictionary
            j[tenses[language][n]].append({'x': x, 'y': y, 'fragment_id': f, 'fragment': fragment.full(True), 'tenses': t})

        # Transpose the dictionary to the correct format for nvd3.
        # TODO: can this be done in the loop above?
        matrix = []
        for k, v in j.items():
            d = dict()
            d['values'] = v

            if isinstance(k, numbers.Number):
                t = Tense.objects.get(pk=k)
                d['key'] = t.title
                d['color'] = t.category.color
            else:
                d['key'] = k
                d['color'] = get_color(k)

            matrix.append(d)

        # Add all variables to the context
        context['matrix'] = json.dumps(matrix)
        context['language'] = language
        context['languages'] = Language.objects.filter(iso__in=tenses.keys()).order_by('iso')
        context['d1'] = d1
        context['d2'] = d2
        context['max_dimensions'] = range(1, len(model[0]) + 1)  # We choose dimensions to be 1-based

        return context


class DescriptiveStatsView(ScenarioDetail):
    model = Scenario
    template_name = 'stats/descriptive.html'

    def get_context_data(self, **kwargs):
        context = super(DescriptiveStatsView, self).get_context_data(**kwargs)

        tenses = self.object.mds_labels
        languages = Language.objects.filter(iso__in=tenses.keys())

        counters = dict()
        tuples = defaultdict(tuple)

        for l in languages:
            c = Counter()
            n = 0
            for t in tenses[l.iso]:
                tense = Tense.objects.get(pk=t).title if isinstance(t, numbers.Number) else t
                c.update([tense])
                tuples[n] += (tense,)
                n += 1

            counters[l] = c.most_common()

        context['counters'] = counters
        context['tuples'] = Counter(tuples.values()).most_common()

        return context
