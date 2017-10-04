from collections import defaultdict, Counter
import json
import pickle
import random

from django.views import generic

from braces.views import LoginRequiredMixin

from .models import Scenario
from .utils import languages_by_scenario
from annotations.models import Language, Tense, Fragment
from annotations.utils import get_color


class ScenarioList(LoginRequiredMixin, generic.ListView):
    model = Scenario
    context_object_name = 'scenarios'


class ScenarioDetail(LoginRequiredMixin, generic.DetailView):
    model = Scenario


class MDSView(LoginRequiredMixin, generic.DetailView):
    """Loads the matrix plot view"""
    model = Scenario
    template_name = 'stats/mds.html'

    def get_context_data(self, **kwargs):
        context = super(MDSView, self).get_context_data(**kwargs)

        # Retrieve kwargs
        pk = self.object.pk
        language = self.kwargs.get('language', languages_by_scenario(self.object).order_by('language__iso').first().language.iso)
        d1 = int(self.kwargs.get('d1', 1))  # We choose dimensions to be 1-based
        d2 = int(self.kwargs.get('d2', 2))

        # Retrieve lists generated with command python manage.py export_matrix
        pre = 'plots/{}_'.format(pk)
        model = pickle.load(open(pre + 'model.p', 'rb'))
        tenses = pickle.load(open(pre + 'tenses.p', 'rb'))
        fragments = pickle.load(open(pre + 'fragments.p', 'rb'))

        # Turn the pickled model into a scatterplot dictionary
        j = defaultdict(list)
        for n, l in enumerate(model):
            # Retrieve x/y dimensions, add some jitter
            x = l[d1 - 1] + random.uniform(-.5, .5) / 100
            y = l[d2 - 1] + random.uniform(-.5, .5) / 100

            f = fragments[n]
            fragment = Fragment.objects.get(pk=f)
            ts = [tenses[l][n] for l in tenses.keys()]
            t = [Tense.objects.get(pk=t).title if type(t) == int else t for t in ts]
            # Add all values to the dictionary
            j[tenses[language][n]].append({'x': x, 'y': y, 'fragment_id': f, 'fragment': fragment.full(True), 'tenses': t})

        # Transpose the dictionary to the correct format for nvd3.
        # TODO: can this be done in the loop above?
        matrix = []
        for k, v in j.items():
            d = dict()
            d['values'] = v

            if type(k) == int:
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


class DescriptiveStatsView(LoginRequiredMixin, generic.DetailView):
    model = Scenario
    template_name = 'stats/descriptive.html'

    def get_context_data(self, **kwargs):
        context = super(DescriptiveStatsView, self).get_context_data(**kwargs)

        pk = self.object.pk
        pre = 'plots/{}_'.format(pk)
        tenses = pickle.load(open(pre + 'tenses.p', 'rb'))
        languages = Language.objects.filter(iso__in=tenses.keys())

        counters = dict()
        tuples = defaultdict(tuple)

        for l in languages:
            c = Counter()
            n = 0
            for t in tenses[l.iso]:
                tense = Tense.objects.get(pk=t).title if type(t) == int else t
                c.update([tense])
                tuples[n] += (tense,)
                n += 1

            counters[l] = c.most_common()

        context['counters'] = counters
        context['tuples'] = Counter(tuples.values()).most_common()

        return context
