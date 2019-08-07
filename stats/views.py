import json
import numbers
import random
from collections import Counter, OrderedDict, defaultdict
from itertools import chain

from braces.views import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views import generic

from django_filters.views import FilterView

from annotations.models import Fragment, Language, Tense, TenseCategory, Annotation
from annotations.utils import get_available_corpora
from core.utils import HTML

from .filters import ScenarioFilter
from .models import Scenario
from .utils import get_tense_properties


class ScenarioList(LoginRequiredMixin, FilterView):
    """
    Shows a list of scenarios
    """
    model = Scenario
    context_object_name = 'scenarios'
    filterset_class = ScenarioFilter
    paginate_by = 10

    def get_queryset(self):
        """
        Only show Scenarios that have been run,
        and if show_test is False, don't show test Scenarios either.
        Order the Scenarios by Corpus title.
        """
        return Scenario.objects \
            .filter(corpus__in=get_available_corpora(self.request.user)) \
            .exclude(last_run__isnull=True) \
            .prefetch_related('scenariolanguage_set') \
            .order_by('corpus__title')


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
        language = self.kwargs.get('language', scenario.languages().order_by('language__iso').first().language.iso)
        # We choose dimensions to be 1-based
        d1 = int(self.kwargs.get('d1', 1))
        d2 = int(self.kwargs.get('d2', 2))

        # Check whether the languages provided are correct, and included in this Scenario
        language_object = get_object_or_404(Language, iso=language)
        if language_object not in [sl.language for sl in scenario.languages()]:
            raise Http404('Language {} does not exist in Scenario {}'.format(language_object, scenario.pk))

        # Retrieve pickled data
        model = scenario.mds_model
        tenses = scenario.mds_labels
        fragments = scenario.mds_fragments

        # Turn the pickled model into a scatterplot dictionary
        random.seed(scenario.pk)  # Fixed seed for random jitter
        j = defaultdict(list)
        tense_cache = dict()
        for n, l in enumerate(model):
            # Retrieve x/y dimensions, add some jitter
            x = l[d1 - 1] + random.uniform(-.5, .5) / 100
            y = random.uniform(-.5, .5) / 100
            if d2 > 0:
                y += l[d2 - 1]

            f = fragments[n]
            fragment = Fragment.objects.get(pk=f)
            ts = [tenses[l][n] for l in tenses.keys()]

            labels = []
            for t in ts:
                label = t
                if isinstance(t, numbers.Number):
                    if t in tense_cache:
                        label = tense_cache[t]
                    else:
                        label = Tense.objects.get(pk=t).title
                        tense_cache[t] = label
                labels.append(label)

            # Add all values to the dictionary
            j[tenses[language][n]].append({'x': x, 'y': y, 'fragment_id': f, 'fragment': fragment.full(HTML), 'tenses': labels})

        # Transpose the dictionary to the correct format for nvd3.
        # TODO: can this be done in the loop above?
        matrix = []
        labels = set()
        for tense, values in j.items():
            tense_label, tense_color, _ = get_tense_properties(tense, len(labels))
            labels.add(tense_label)

            d = dict()
            d['key'] = tense_label
            d['color'] = tense_color
            d['values'] = values
            matrix.append(d)

        # Add all variables to the context
        context['matrix'] = json.dumps(matrix)
        context['language'] = language
        context['languages'] = Language.objects.filter(iso__in=tenses.keys()).order_by('iso')
        context['d1'] = d1
        context['d2'] = d2
        context['max_dimensions'] = range(1, len(model[0]) + 1)  # We choose dimensions to be 1-based
        context['stress'] = scenario.mds_stress

        # flat data representation for d3
        flat_data = []
        series_list = []
        for series in matrix:
            series_list.append(
                {'key': series['key'], 'color': series['color']}
            )
            for fragment in series['values']:
                s = {'key': series['key'], 'color': series['color']}
                flat_data.append(
                    dict(chain(
                        s.iteritems(),
                        fragment.iteritems()
                    ))
                )
        context['flat_data'] = json.dumps(flat_data)
        context['series_list'] = json.dumps(series_list)

        return context

    def post(self, request, pk, *args, **kwargs):
        request.session['fragment_ids'] = json.loads(request.POST['fragment_ids'])
        request.session['tenses'] = json.loads(request.POST['tenses'])
        return HttpResponseRedirect(reverse('stats:fragment_table', kwargs={'pk': pk}))


class MDSViewOld(MDSView):
    """Loads the matrix plot view, previous version (for the sake of comparison and nostalgia)"""
    template_name = 'stats/mds_old.html'


class DescriptiveStatsView(ScenarioDetail):
    """
    Shows descriptive statistics of a selected scenario
    """
    model = Scenario
    template_name = 'stats/descriptive.html'

    def get_context_data(self, **kwargs):
        context = super(DescriptiveStatsView, self).get_context_data(**kwargs)

        tenses = self.object.mds_labels
        languages = Language.objects.filter(iso__in=tenses.keys())

        counters_tenses = dict()
        counters_tensecats = dict()
        tuples = defaultdict(tuple)
        colors = dict()
        distinct_tensecats = set()

        for l in languages:
            c_tenses = Counter()
            c_tensecats = Counter()
            n = 0
            labels = set()
            for t in tenses[l.iso]:
                tense_label, tense_color, tense_category = get_tense_properties(
                    t, len(labels))
                labels.add(tense_label)
                distinct_tensecats.add(tense_category)

                c_tenses.update([tense_label])
                c_tensecats.update([tense_category])
                tuples[n] += (tense_label,)
                n += 1

                if tense_label not in colors:
                    colors[tense_label] = tense_color

            counters_tenses[l] = c_tenses.most_common()
            counters_tensecats[l] = c_tensecats

        tensecat_table = defaultdict(list)
        for l in languages:
            tensecat_counts = counters_tensecats[l]
            for tensecat in distinct_tensecats:
                if tensecat in tensecat_counts.keys():
                    tensecat_table[tensecat].append(tensecat_counts[tensecat])
                else:
                    tensecat_table[tensecat].append(0)

        tensecat_table_ordered = OrderedDict(sorted(tensecat_table.items(),
                                                    key=lambda item: sum(
                                                        item[1]) if item[0] else 0,
                                                    reverse=True))

        context['counters'] = counters_tenses
        context['counters_json'] = json.dumps(
            {language.iso: values for language, values in counters_tenses.items()})
        context['tensecat_table'] = tensecat_table_ordered
        context['tuples'] = Counter(tuples.values()).most_common()
        context['colors_json'] = json.dumps(colors)
        context['languages'] = languages
        context['languages_json'] = json.dumps(
            {l.iso: l.title for l in languages})

        return context


class FragmentTableView(ScenarioDetail):
    model = Scenario
    template_name = 'stats/fragment_table.html'

    def get_context_data(self, **kwargs):
        context = super(FragmentTableView, self).get_context_data(**kwargs)

        fragments = Fragment.objects.filter(pk__in=self.request.session.get('fragment_ids', []))
        tenses = self.request.session.get('tenses', [])

        context['fragments'] = fragments
        context['tenses'] = tenses

        return context


class UpsetView(ScenarioDetail):
    model = Scenario
    template_name = 'stats/upset.html'

    def get_context_data(self, **kwargs):
        context = super(UpsetView, self).get_context_data(**kwargs)

        scenario = self.object
        tenses = scenario.mds_labels
        fragments = scenario.mds_fragments

        # Get the currently selected TenseCategory. We pick "Present Perfect" as the default here.
        # TODO: we might want to change this magic number into a setting?
        tc_pk = int(self.kwargs.get('tc', TenseCategory.objects.get(title='Present Perfect').pk))

        results = []
        languages = set()
        tense_cache = dict()
        for n, fragment_pk in enumerate(fragments):
            d = {'fragment_pk': fragment_pk}
            for language, t in tenses.items():
                t = t[n]

                if isinstance(t, numbers.Number):
                    if t in tense_cache:
                        tense = tense_cache[t]
                    else:
                        tense = Tense.objects.select_related('category').get(pk=t)
                        tense_cache[t] = tense

                    d[str(language)] = int(tense.category.pk == tc_pk)
                    languages.add(language)

            results.append(d)

        context['tense_categories'] = TenseCategory.objects.all()
        context['selected_tc'] = TenseCategory.objects.get(pk=tc_pk)
        context['data'] = json.dumps(results)
        context['languages'] = json.dumps(list(languages))

        return context

    def post(self, request, pk, *args, **kwargs):
        request.session['fragment_ids'] = json.loads(request.POST['fragment_ids'])
        return HttpResponseRedirect(reverse('stats:fragment_table', kwargs={'pk': pk}))


class SankeyView(ScenarioDetail):
    model = Scenario
    template_name = 'stats/sankey.html'

    def get_context_data(self, **kwargs):
        context = super(SankeyView, self).get_context_data(**kwargs)

        scenario = self.object
        labels = scenario.mds_labels
        fragment_pks = scenario.mds_fragments

        language_from = scenario.languages(as_from=True).first().language.iso
        language_to = self.request.GET.get('language_to', scenario.languages(as_to=True).first().language.iso)
        lto_option = self.request.GET.get('lto_option')
        lto_option = None if lto_option == 'none' else lto_option

        # Retrieve nodes and links
        nodes = set()
        for language, ls in labels.items():
            if language in [language_from, language_to]:
                for iterator, label in enumerate(ls):
                    nodes.add(label)

        lto_values = []
        if lto_option:
            for fragment_pk in fragment_pks:
                annotation = Annotation.objects \
                    .filter(alignment__original_fragment__pk=fragment_pk,
                            alignment__translated_fragment__language__iso=language_to) \
                    .first()
                lto_value = 'none'
                if annotation:
                    lto_value = getattr(annotation, lto_option)
                nodes.add(lto_value)
                lto_values.append(lto_value)

        # Count the links  # TODO: can we do this in a more generic way?
        zipped = list(zip(labels[language_from], labels[language_to]))
        links = Counter(zipped).most_common()
        if lto_values:
            zipped = list(zip(labels[language_to], lto_values))
            links.extend(Counter(zipped).most_common())

        # Convert the nodes into a dictionary
        new_nodes = []
        for node in nodes:
            node_label, node_color, node_category = get_tense_properties(node)

            new_node = {'id': node, 'color': node_color, 'label': node_label}
            new_nodes.append(new_node)

        # Convert the links into a dictionary
        new_links = []
        for link, value in links:
            for l1, l2 in zip(link, link[1:]):
                l1_label, l1_color, l1_category = get_tense_properties(l1)
                l2_label, l2_color, l2_category = get_tense_properties(l2)

                # TODO add links to the Fragments (i.e. on click, go to the set of Fragments related with this link)
                new_link = {'source': l1, 'source_color': l1_color, 'source_label': l1_label,
                            'target': l2, 'target_color': l2_color, 'target_label': l2_label,
                            'value': value, 'link_color': l1_color}

                new_links.append(new_link)

        # JSONify the data and add it to the context
        context['data'] = json.dumps({'nodes': new_nodes, 'links': new_links})

        # Add selection of languages to the context
        context['selected_language_to'] = language_to
        # context['lfrom_options'] = ['other_label', 'formal_structure', 'sentence_function']  # TODO: implement
        context['lto_options'] = ['other_label']
        context['selected_lto_option'] = lto_option
        context['languages_to'] = scenario.languages(as_to=True)

        return context
