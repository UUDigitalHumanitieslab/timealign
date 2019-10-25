import json
import numbers
import random
from collections import Counter, OrderedDict, defaultdict
from itertools import chain

from braces.views import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Case, When, Prefetch
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views import generic

from django_filters.views import FilterView

from annotations.models import Corpus, Fragment, Language, Tense, TenseCategory, Sentence, Word, Annotation
from annotations.utils import get_available_corpora
from core.utils import HTML

from .filters import ScenarioFilter, FragmentFilter
from .models import Scenario, ScenarioLanguage
from .utils import get_tense_properties_from_cache


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
        languages_from = ScenarioLanguage.objects.filter(as_from=True).select_related('language')
        languages_to = ScenarioLanguage.objects.filter(as_to=True).select_related('language')
        return Scenario.objects \
            .filter(corpus__in=get_available_corpora(self.request.user)) \
            .exclude(last_run__isnull=True) \
            .select_related('corpus') \
            .prefetch_related(Prefetch('scenariolanguage_set', queryset=languages_from, to_attr='languages_from'),
                              Prefetch('scenariolanguage_set', queryset=languages_to, to_attr='languages_to')) \
            .order_by('corpus__title') \
            .defer('mds_model', 'mds_matrix', 'mds_fragments', 'mds_labels')  # Don't fetch the PickledObjectFields


class ScenarioDetail(LoginRequiredMixin, generic.DetailView):
    """
    Shows details of a selected scenario
    """
    model = Scenario

    def get_object(self, queryset=None):
        """
        Only show Scenarios that have been run
        """
        qs = Scenario.objects \
            .select_related('corpus') \
            .defer('mds_model', 'mds_matrix', 'mds_fragments', 'mds_labels')  # Don't fetch the PickledObjectFields
        scenario = super(ScenarioDetail, self).get_object(qs)
        if scenario.corpus not in get_available_corpora(self.request.user):
            raise PermissionDenied
        if not scenario.last_run:
            raise Http404('Scenario has not been run')
        return scenario


class ScenarioManual(generic.TemplateView):
    template_name = 'stats/scenario_manual.html'

    def get_context_data(self, **kwargs):
        context = super(ScenarioManual, self).get_context_data(**kwargs)

        first_scenario = Scenario.objects \
            .exclude(last_run=None) \
            .defer('mds_model', 'mds_matrix', 'mds_fragments', 'mds_labels') \
            .first()

        context['scenario'] = first_scenario

        return context


class MDSView(ScenarioDetail):
    """Loads the matrix plot view"""
    model = Scenario
    template_name = 'stats/mds.html'

    def get_context_data(self, **kwargs):
        context = super(MDSView, self).get_context_data(**kwargs)

        # Retrieve kwargs
        scenario = self.object
        default_language = scenario.languages().order_by('language__iso').first()
        display_language = self.kwargs.get('language', default_language.language.iso)
        # We choose dimensions to be 1-based
        d1 = int(self.kwargs.get('d1', 1))
        d2 = int(self.kwargs.get('d2', 2))

        # Check whether the languages provided are correct, and included in this Scenario
        language_object = get_object_or_404(Language, iso=display_language)
        if language_object not in [sl.language for sl in scenario.languages()]:
            raise Http404('Language {} does not exist in Scenario {}'.format(language_object, scenario.pk))

        # Retrieve pickled data
        model = scenario.mds_model
        tenses = scenario.mds_labels
        fragment_pks = scenario.mds_fragments

        # Retrieve Fragments, but keep order intact
        # Solution taken from https://stackoverflow.com/a/38390480
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(fragment_pks)])
        fragments = list(Fragment.objects.filter(pk__in=fragment_pks).
                         order_by(preserved).
                         prefetch_related('sentence_set', 'sentence_set__word_set'))

        # Turn the pickled model into a scatterplot dictionary
        random.seed(scenario.pk)  # Fixed seed for random jitter
        j = defaultdict(list)
        tense_cache = {t.pk: (t.title, t.category.color, t.category.title)
                       for t in Tense.objects.select_related('category')}
        for n, embedding in enumerate(model):
            # Retrieve x/y dimensions, add some jitter
            x = embedding[d1 - 1] + random.uniform(-.5, .5) / 100
            y = random.uniform(-.5, .5) / 100
            if d2 > 0:  # Only add y if it's been requested
                y += embedding[d2 - 1]

            fragment = fragments[n]

            # Retrieve the labels of all languages in this context
            ts = [tenses[language][n] for language in list(tenses.keys())]
            labels = []
            for t in ts:
                label, _, _ = get_tense_properties_from_cache(t, tense_cache, len(labels))
                labels.append(label)

            # Add all values to the dictionary
            j[tenses[display_language][n]].append({'x': x, 'y': y, 'tenses': labels,
                                                   'fragment_pk': fragment.pk, 'fragment': fragment.full(HTML)})

        # Transpose the dictionary to the correct format for nvd3.
        # TODO: can this be done in the loop above?
        matrix = []
        labels = set()
        for tense, values in list(j.items()):
            tense_label, tense_color, _ = get_tense_properties_from_cache(tense, tense_cache, len(labels))
            labels.add(tense_label)

            d = dict()
            d['key'] = tense_label
            d['color'] = tense_color
            d['values'] = values
            matrix.append(d)

        # Add all variables to the context
        context['matrix'] = json.dumps(matrix)
        context['language'] = display_language
        context['languages'] = Language.objects.filter(iso__in=list(tenses.keys())).order_by('iso')
        context['d1'] = d1
        context['d2'] = d2
        context['max_dimensions'] = list(range(1, len(model[0]) + 1))  # We choose dimensions to be 1-based
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
                        iter(s.items()),
                        iter(fragment.items())
                    ))
                )
        context['flat_data'] = json.dumps(flat_data)
        context['series_list'] = json.dumps(series_list)

        return context

    def post(self, request, pk, *args, **kwargs):
        request.session['scenario_pk'] = pk
        request.session['fragment_pks'] = json.loads(request.POST['fragment_ids'])
        request.session['tenses'] = json.loads(request.POST['tenses'])
        return HttpResponseRedirect(reverse('stats:fragment_table'))


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
        languages = Language.objects.filter(iso__in=list(tenses.keys()))

        counters_tenses = dict()
        counters_tensecats = dict()
        tuples = defaultdict(tuple)
        colors = dict()
        distinct_tensecats = set()

        tense_cache = {t.pk: (t.title, t.category.color, t.category.title)
                       for t in Tense.objects.select_related('category')}
        for l in languages:
            c_tenses = Counter()
            c_tensecats = Counter()
            n = 0
            labels = set()
            for t in tenses[l.iso]:
                tense_label, tense_color, tense_category = get_tense_properties_from_cache(t, tense_cache, len(labels))

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
                if tensecat in list(tensecat_counts.keys()):
                    tensecat_table[tensecat].append(tensecat_counts[tensecat])
                else:
                    tensecat_table[tensecat].append(0)

        tensecat_table_ordered = OrderedDict(
            sorted(list(tensecat_table.items()), key=lambda item: sum(item[1]) if item[0] else 0, reverse=True))

        context['counters'] = counters_tenses
        context['counters_json'] = json.dumps({language.iso: values for language, values in list(counters_tenses.items())})
        context['tensecat_table'] = tensecat_table_ordered
        context['tuples'] = Counter(list(tuples.values())).most_common()
        context['colors_json'] = json.dumps(colors)
        context['languages'] = languages
        context['languages_json'] = json.dumps({l.iso: l.title for l in languages})

        return context


class FragmentTableView(LoginRequiredMixin, FilterView):
    model = Fragment
    context_object_name = 'fragments'
    filterset_class = FragmentFilter
    paginate_by = 15

    def get_queryset(self):
        fragment_pks = self.request.session.get('fragment_pks', [])
        target_words = Sentence.objects. \
            prefetch_related(Prefetch('word_set', queryset=Word.objects.filter(is_target=True)))

        return Fragment.objects \
            .filter(pk__in=fragment_pks) \
            .select_related('document') \
            .prefetch_related('sentence_set',
                              'sentence_set__word_set',
                              Prefetch('sentence_set', queryset=target_words, to_attr='targets_prefetched')) \
            .order_by('pk')

    def get_context_data(self, **kwargs):
        context = super(FragmentTableView, self).get_context_data(**kwargs)

        scenario_pk = self.request.session.get('scenario_pk')

        if not scenario_pk:
            return Http404

        # Don't fetch the PickledObjectFields
        scenario = Scenario.objects \
            .defer('mds_model', 'mds_matrix', 'mds_fragments', 'mds_labels') \
            .get(pk=scenario_pk)
        tenses = self.request.session.get('tenses', [])

        context['scenario'] = scenario
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
        tense_cache = {t.pk: t for t in Tense.objects.select_related('category')}
        for n, fragment_pk in enumerate(fragments):
            d = {'fragment_pk': fragment_pk}
            for language, t in list(tenses.items()):
                t = t[n]

                if isinstance(t, numbers.Number):
                    tense = tense_cache.get(t)
                    d[str(language)] = int(tense.category.pk == tc_pk)
                    languages.add(language)

            results.append(d)

        context['tense_categories'] = TenseCategory.objects.all()
        context['selected_tc'] = TenseCategory.objects.get(pk=tc_pk)
        context['data'] = json.dumps(results)
        context['languages'] = json.dumps(list(languages))

        return context

    def post(self, request, pk, *args, **kwargs):
        request.session['scenario_pk'] = pk
        request.session['fragment_pks'] = json.loads(request.POST['fragment_ids'])
        return HttpResponseRedirect(reverse('stats:fragment_table'))


class SankeyView(ScenarioDetail):
    model = Scenario
    template_name = 'stats/sankey.html'

    def get_context_data(self, **kwargs):
        context = super(SankeyView, self).get_context_data(**kwargs)

        scenario = self.object
        labels = scenario.mds_labels
        fragment_pks = scenario.mds_fragments
        languages_from = scenario.languages(as_from=True)
        languages_to = scenario.languages(as_to=True)

        language_from = self.request.GET.get('language_from', languages_from.first().language.iso)
        language_to = self.request.GET.get('language_to', languages_to.first().language.iso)
        lfrom_option = self.request.GET.get('lfrom_option')
        lfrom_option = None if lfrom_option == 'none' else lfrom_option
        lto_option = self.request.GET.get('lto_option')
        lto_option = None if lto_option == 'none' else lto_option

        # Retrieve nodes and links
        nodes = set()
        for language, ls in list(labels.items()):
            if language in [language_from, language_to]:
                for iterator, label in enumerate(ls):
                    nodes.add(label)

        # Retrieve the values for the source language
        lfrom_values = []
        if lfrom_option:
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(fragment_pks)])
            fragments = Fragment.objects.filter(pk__in=fragment_pks).order_by(preserved)
            for fragment in fragments:
                lfrom_value = getattr(fragment, lfrom_option)() if lfrom_option.endswith('display') \
                    else getattr(fragment, lfrom_option)
                nodes.add(lfrom_value)
                lfrom_values.append(lfrom_value)

        # Retrieve the values for the target language
        lto_values = []
        if lto_option:
            annotations = Annotation.objects \
                .filter(alignment__original_fragment__pk__in=fragment_pks,
                        alignment__translated_fragment__language__iso=language_to) \
                .select_related('alignment__original_fragment')
            annotations = {a.alignment.original_fragment.pk: a for a in annotations}
            for fragment_pk in fragment_pks:
                annotation = annotations.get(fragment_pk)
                lto_value = 'none'
                if annotation:
                    lto_value = getattr(annotation, lto_option)
                nodes.add(lto_value)
                lto_values.append(lto_value)

        # Count the links  # TODO: can we do this in a more generic way?
        list_of_lists = [labels[language_from]]
        for l in [lfrom_values, labels[language_to], lto_values]:
            if l:
                list_of_lists.append(l)

        links = defaultdict(list)
        for l1, l2 in zip(list_of_lists, list_of_lists[1:]):
            zipped = list(zip(l1, l2))
            for n, link in enumerate(zipped):
                links[(link[0], link[1])].append(fragment_pks[n])

        # Convert the nodes into a dictionary
        tense_cache = {t.pk: (t.title, t.category.color, t.category.title)
                       for t in Tense.objects.select_related('category')}
        labels = set()
        new_nodes = []
        for node in nodes:
            node_label, node_color, _ = get_tense_properties_from_cache(node, tense_cache, len(labels))

            labels.add(node_label)
            new_node = {'id': node, 'color': node_color, 'label': node_label}
            new_nodes.append(new_node)

        # Convert the links into a dictionary
        new_links = []
        for link, fragment_pks in list(links.items()):
            for l1, l2 in zip(link, link[1:]):
                l1_label, l1_color, _ = get_tense_properties_from_cache(l1, tense_cache)
                l2_label, l2_color, _ = get_tense_properties_from_cache(l2, tense_cache)

                new_link = {'source': l1, 'source_color': l1_color, 'source_label': l1_label,
                            'target': l2, 'target_color': l2_color, 'target_label': l2_label,
                            'value': len(fragment_pks), 'fragment_pks': fragment_pks, 'link_color': l1_color}

                new_links.append(new_link)

        # JSONify the data and add it to the context
        context['data'] = json.dumps({'nodes': new_nodes, 'links': new_links})

        # Add selection of languages to the context
        context['languages_from'] = languages_from
        context['languages_to'] = languages_to
        context['selected_language_from'] = language_from
        context['selected_language_to'] = language_to
        context['lfrom_options'] = {
            'other_label': 'Other label',
            'get_formal_structure_display': 'Formal structure',
            'get_sentence_function_display': 'Sentence function'
        }
        context['selected_lfrom_option'] = lfrom_option
        context['lto_options'] = {
            'other_label': 'Other label'
        }
        context['selected_lto_option'] = lto_option

        return context

    def post(self, request, pk, *args, **kwargs):
        request.session['scenario_pk'] = pk
        request.session['fragment_pks'] = json.loads(request.POST['fragment_ids'])
        return HttpResponseRedirect(reverse('stats:fragment_table'))


class SankeyManual(generic.TemplateView):
    template_name = 'stats/sankey_manual.html'

    def get_context_data(self, **kwargs):
        context = super(SankeyManual, self).get_context_data(**kwargs)

        context['corpora'] = Corpus.objects.filter(check_structure=True)

        return context
