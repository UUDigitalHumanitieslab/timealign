import json
import numbers
import os
import random
import math
from collections import Counter, OrderedDict, defaultdict
from itertools import chain, repeat, count
from zipfile import ZipFile

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Case, When, Prefetch
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views import generic

from django_filters.views import FilterView

from annotations.models import Corpus, Fragment, Language, Tense, TenseCategory, Sentence, Word, Annotation
from annotations.utils import get_available_corpora
from core.utils import HTML

from .filters import ScenarioFilter, FragmentFilter
from .management.commands.scenario_to_feather import export_matrix, export_fragments, export_tensecats
from .models import Scenario, ScenarioLanguage
from .utils import get_label_properties_from_cache, prepare_label_cache


class ScenarioList(LoginRequiredMixin, FilterView):
    """Shows a list of Scenarios"""
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
    """Shows details of a selected Scenario"""
    model = Scenario

    def get_object(self, queryset=None):
        """
        Only show Scenarios that have been run
        """
        qs = Scenario.objects \
            .select_related('corpus') \
            .defer('mds_model', 'mds_matrix', 'mds_fragments', 'mds_labels')  # Don't fetch the PickledObjectFields
        scenario = super().get_object(qs)
        if scenario.corpus not in get_available_corpora(self.request.user):
            raise PermissionDenied
        if not scenario.last_run:
            raise Http404('Scenario has not been run')
        return scenario

    def post(self, request, pk, *args, **kwargs):
        request.session['scenario_pk'] = pk
        request.session['fragment_pks'] = json.loads(request.POST['fragment_ids'])
        return HttpResponseRedirect(reverse('stats:fragment_table'))


class ScenarioManual(generic.TemplateView):
    """Provides the manual for adding Scenarios"""
    template_name = 'stats/scenario_manual.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

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
        context = super().get_context_data(**kwargs)

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
        tenses = scenario.get_labels()
        fragment_pks = scenario.mds_fragments

        # Solution to preserve order taken from https://stackoverflow.com/a/37648265
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(fragment_pks)])
        fragments = list(Fragment.objects.filter(pk__in=fragment_pks).
                         order_by(preserved).
                         prefetch_related('sentence_set', 'sentence_set__word_set'))

        # Turn the pickled model into a scatterplot dictionary
        points = defaultdict(list)
        clusters = []
        label_cache = prepare_label_cache(self.object.corpus)
        label_set = set()

        clustering = self.request.GET.get('clustering', 'on') == 'on'
        cluster_labels = self.request.GET.get('labels', 'on') == 'on'
        hulls = self.request.GET.get('hulls', 'on') == 'on'
        if clustering:
            reduced = self.reduce_model(model, tenses)
        else:
            # Keep original data points as-is
            # (which is the same as having all clusters as size 1)
            reduced = zip(count(), model, repeat(1))
            random.seed(scenario.pk)  # Fixed seed for random jitter

        for n, embedding, cluster_size in reduced:
            # Retrieve x/y dimensions, add some jitter
            x = embedding[d1 - 1]
            y = 0
            if not clustering:
                x += random.uniform(-.5, .5) / 100
                y += random.uniform(-.5, .5) / 100
            if d2 > 0:  # Only add y if it's been requested
                y += embedding[d2 - 1]

            cluster_id = len(clusters)
            clusters.append(dict(x=x, y=y, count=cluster_size))

            try:
                fragment = fragments[n]

                # Retrieve the labels of all languages in this context
                ts = [tenses[language][n] for language in list(tenses.keys())]
                # flatten
                label_list = []
                for t in ts:
                    label, _, _ = get_label_properties_from_cache(t, label_cache, len(label_set))
                    label_list.append(label.replace('<', '&lt;').replace('>', '&gt;'))
                    label_set.add(label)

                # Add all values to the dictionary
                points[tenses[display_language][n]].append(
                    {'cluster': cluster_id, 'x': x, 'y': y,
                     'tenses': label_list, 'fragment_pk': fragment.pk, 'fragment': fragment.full(HTML)})

            except IndexError:
                messages.error(self.request, 'Some of the Fragments in this Scenario have been deleted. '
                                             'Please rerun your Scenario.')
                break

        context['language'] = display_language
        context['languages'] = Language.objects.filter(iso__in=list(tenses.keys())).order_by('iso')
        context['d1'] = d1
        context['d2'] = d2
        context['clustering'] = 'on' if clustering else 'off'
        context['cluster_labels'] = 'on' if cluster_labels else 'off'
        context['hulls'] = 'on' if hulls else 'off'
        context['max_dimensions'] = list(range(1, len(model[0]) + 1))  # We choose dimensions to be 1-based
        context['stress'] = scenario.mds_stress

        # flat data representation for d3
        flat_data, series_list = self.prepare_flat_data(points, label_cache)
        context['flat_data'] = json.dumps(flat_data)
        context['series_list'] = json.dumps(series_list)
        context['clusters'] = json.dumps(clusters)

        return context

    def reduce_model(self, model, tenses):
        cluster_count = defaultdict(int)
        collect = dict()
        # First, reduce points which overlap exactly
        for n, embedding in enumerate(model):
            t = tuple(embedding)
            collect[t] = (n, t)
            cluster_count[t] += 1

        # Reduce points which are very close
        skip = set()

        # Distance helper function
        def distance(origin):
            def _distance(other):
                d = 0
                for a, b in zip(origin, other):
                    d += (a - b) ** 2
                d = math.sqrt(d)
                return 0.1 > d > 0

            return _distance

        # Look among close points for overlap in label tuples
        for coord, point in collect.items():
            if coord in skip:
                continue
            close_by = filter(distance(coord), collect.keys())
            for other_coord in close_by:
                sequence = point[0]
                tenses_a = tuple(tenses[language][sequence] for language in list(tenses.keys()))
                other_sequence = collect[other_coord][0]
                tenses_b = tuple(tenses[language][other_sequence] for language in list(tenses.keys()))

                if tenses_a == tenses_b:
                    skip.add(other_coord)
                    # merge clusters
                    cluster_count[coord] += cluster_count[other_coord]

        return [(n, embedding, cluster_count[embedding]) for n, embedding in collect.values() if embedding not in skip]

    def prepare_flat_data(self, points, label_cache):
        # Transpose the dictionary to the correct format for nvd3.
        # TODO: can this be done in the loop above?
        matrix = []
        labels = set()
        for identifier, values in list(points.items()):
            label, color, _ = get_label_properties_from_cache(identifier, label_cache, len(labels))
            labels.add(label)

            d = dict()
            d['key'] = label
            d['color'] = color
            d['values'] = values
            matrix.append(d)

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
        return flat_data, series_list

    def post(self, request, pk, *args, **kwargs):
        request.session['scenario_pk'] = pk
        request.session['fragment_pks'] = json.loads(request.POST['fragment_ids'])
        return HttpResponseRedirect(reverse('stats:fragment_table_mds'))


class MDSViewOld(MDSView):
    """Loads the matrix plot view, previous version (for the sake of comparison and nostalgia)"""
    template_name = 'stats/mds_old.html'


class DescriptiveStatsView(ScenarioDetail):
    """Shows descriptive statistics of a selected Scenario"""
    model = Scenario
    template_name = 'stats/descriptive.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        fragment_pks = self.object.mds_fragments
        scenario_labels = self.object.get_labels()
        languages = Language.objects.filter(iso__in=list(scenario_labels.keys())).order_by('iso')

        counters_labels = OrderedDict()
        counters_tensecats = dict()
        tuples = defaultdict(tuple)
        colors = dict()
        categories = dict()
        distinct_tensecats = set()

        label_cache = prepare_label_cache(self.object.corpus)

        for language in languages:
            c_labels = Counter()
            c_tensecats = Counter()
            labels = set()
            for n, identifier in enumerate(scenario_labels[language.iso]):
                label, color, category = get_label_properties_from_cache(identifier, label_cache, len(labels))

                # multiple labels are expected, handle single tense labels
                if not isinstance(label, tuple):
                    label = (label,)

                for tense_label in label:
                    labels.add(tense_label)
                    c_labels.update([tense_label])
                    tuples[n] += (tense_label,)
                    colors[tense_label] = color
                    categories[tense_label] = category

                distinct_tensecats.add(category)
                c_tensecats.update([category])

            counters_labels[language] = c_labels.most_common()
            counters_tensecats[language] = c_tensecats

        categories_table = defaultdict(list)
        for language in languages:
            tensecat_counts = counters_tensecats[language]
            for tensecat in distinct_tensecats:
                if tensecat in list(tensecat_counts.keys()):
                    categories_table[tensecat].append(tensecat_counts[tensecat])
                else:
                    categories_table[tensecat].append(0)

        categories_table_ordered = OrderedDict(
            sorted(list(categories_table.items()), key=lambda item: sum(item[1]) if item[0] else 0, reverse=True))

        tuples_with_fragments = defaultdict(list)
        for n, label_tuple in enumerate(tuples.values()):
            tuples_with_fragments[label_tuple].append(fragment_pks[n])

        context['counters'] = counters_labels
        context['counters_json'] = json.dumps({language.iso: vs for language, vs in list(counters_labels.items())})
        context['tensecat_table'] = categories_table_ordered
        context['tuples_with_fragments'] = dict(tuples_with_fragments)
        context['colors_json'] = json.dumps(colors)
        context['tensecats_json'] = json.dumps(categories)
        context['languages'] = languages
        context['languages_json'] = json.dumps({language.iso: language.title for language in languages})

        return context


class FragmentTableView(LoginRequiredMixin, FilterView):
    """Shows the drill-through to Fragments"""
    model = Fragment
    context_object_name = 'fragments'
    filterset_class = FragmentFilter
    paginate_by = 15

    def get_queryset(self):
        fragment_pks = self.request.session.get('fragment_pks', [])
        return self.queryset_for_fragments(fragment_pks)

    def queryset_for_fragments(self, fragment_pks):
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
        context = super().get_context_data(**kwargs)

        scenario_pk = self.request.session.get('scenario_pk')
        fragment_pks = self.request.session.get('fragment_pks')

        if not scenario_pk or not fragment_pks:
            return Http404

        # Don't fetch some of the PickledObjectFields
        scenario = Scenario.objects \
            .defer('mds_model', 'mds_matrix') \
            .get(pk=scenario_pk)

        # Find the index of the first Fragment
        index = 0
        for n, fragment in enumerate(scenario.mds_fragments):
            if int(fragment_pks[0]) == fragment:
                index = n
                break

        # Retrieve the labels for this specific Fragment
        label_cache = prepare_label_cache(scenario.corpus)
        labels = []
        for values in scenario.get_labels().values():
            for n, value in enumerate(values):
                if index == n:
                    label, _, _ = get_label_properties_from_cache(value, label_cache)
                    labels.append(label)
                    break

        context['scenario'] = scenario
        context['labels'] = labels

        return context


class FragmentTableViewMDS(FragmentTableView):
    """Shows the drill-through for Fragments coming from the MDS solution"""
    def get_queryset(self):
        fragment_pks = self.request.session.get('fragment_pks', [])
        scenario_pk = self.request.session.get('scenario_pk')

        # Include all fragments whose label set matches that of the selected fragment
        fragment = int(fragment_pks[0])
        fragment_pks = []
        scenario = Scenario.objects.get(pk=scenario_pk)
        all_labels = scenario.get_labels()
        scenario_fragments = scenario.mds_fragments
        sequence = scenario_fragments.index(fragment)
        languages = all_labels.keys()
        label_key = tuple(all_labels[lang][sequence] for lang in languages)

        for seq, frag in enumerate(scenario_fragments):
            labels = tuple(all_labels[lang][seq] for lang in languages)
            if labels == label_key:
                fragment_pks.append(frag)

        return self.queryset_for_fragments(fragment_pks)


class UpsetView(ScenarioDetail):
    model = Scenario
    template_name = 'stats/upset.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        scenario = self.object
        labels = scenario.get_labels()
        fragments = scenario.mds_fragments

        # Get the currently selected TenseCategory. We pick "Present Perfect" as the default here.
        # TODO: we might want to change this magic number into a setting?
        tc_pk = int(self.kwargs.get('tc', TenseCategory.objects.get(title='Present Perfect').pk))

        results = []
        languages = set()
        tense_cache = {t.pk: t for t in Tense.objects.select_related('category')}
        for n, fragment_pk in enumerate(fragments):
            d = {'fragment_pk': fragment_pk}
            for language, label in list(labels.items()):
                languages.add(language)
                label = label[n]
                if isinstance(label, numbers.Number):
                    tense = tense_cache.get(label)
                # TODO: below is a temporary fix to work with newer Scenarios.
                # Ideally, we first make sure the Scenario works with Tense only.
                if isinstance(label, tuple):
                    tense_pk = int(label[0].split(':')[1])
                    tense = tense_cache.get(tense_pk)
                d[str(language)] = int(tense.category.pk == tc_pk)

            results.append(d)

        context['tense_categories'] = TenseCategory.objects.all()
        context['selected_tc'] = TenseCategory.objects.get(pk=tc_pk)
        context['data'] = json.dumps(results)
        context['languages'] = json.dumps(list(languages))

        return context


class SankeyView(ScenarioDetail):
    model = Scenario
    template_name = 'stats/sankey.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        scenario = self.object
        mds_labels = scenario.get_labels()
        fragment_pks = scenario.mds_fragments
        languages_from = scenario.languages(as_from=True)
        languages_to = scenario.languages(as_to=True)

        language_from_iso = self.request.GET.get('language_from', languages_from.first().language.iso)
        language_to_iso = self.request.GET.get('language_to', languages_to.first().language.iso)
        language_from = ScenarioLanguage.objects.get(scenario=scenario, language__iso=language_from_iso)
        language_to = ScenarioLanguage.objects.get(scenario=scenario, language__iso=language_to_iso)
        lfrom_option = self.request.GET.get('lfrom_option')
        lfrom_option = None if lfrom_option == 'none' else lfrom_option
        lto_option = self.request.GET.get('lto_option')
        lto_option = None if lto_option == 'none' else lto_option

        # Simplify labels (from tuples to single values)
        def simplify(value, index=0):
            try:
                result = value[index] if isinstance(value, tuple) else value
            except IndexError:
                result = None
            if not result:
                result = '-'
            return result

        labels = dict()
        for language, values in mds_labels.items():
            labels[language] = [simplify(v) for v in values]

        # Retrieve nodes and links
        nodes = defaultdict(set)
        for language, ls in labels.items():
            if language in [language_from_iso, language_to_iso]:
                for label in ls:
                    nodes[language].add(label) if label else nodes[language].add('-')

        # Retrieve the values for the source language
        lfrom_values = []
        if lfrom_option:
            # Solution to preserve order taken from https://stackoverflow.com/a/37648265
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(fragment_pks)])
            fragments = Fragment.objects.filter(pk__in=fragment_pks).order_by(preserved)
            for n, fragment in enumerate(fragments):
                lfrom_value = getattr(fragment, lfrom_option)() if lfrom_option.endswith('display') \
                    else simplify(mds_labels[language_from_iso][n], 1)
                nodes['-'].add(lfrom_value)
                lfrom_values.append(lfrom_value)

        # Retrieve the values for the target language
        lto_values = []
        if lto_option:
            annotations = Annotation.objects \
                .filter(alignment__original_fragment__pk__in=fragment_pks,
                        alignment__translated_fragment__language__iso=language_to_iso) \
                .select_related('alignment__original_fragment')
            annotations = {a.alignment.original_fragment.pk: a for a in annotations}
            for n, fragment_pk in enumerate(fragment_pks):
                annotation = annotations.get(fragment_pk)
                lto_value = 'none'
                if annotation:
                    lto_value = simplify(mds_labels[language_to_iso][n], 1)
                nodes['-'].add(lto_value)
                lto_values.append(lto_value)

        # Count the links  # TODO: can we do this in a more generic way?
        list_of_lists = [labels[language_from_iso]]
        for label in [lfrom_values, labels[language_to_iso], lto_values]:
            if label:
                list_of_lists.append(label)

        links = defaultdict(list)
        for l1, l2 in zip(list_of_lists, list_of_lists[1:]):
            zipped = list(zip(l1, l2))
            for n, link in enumerate(zipped):
                origin = list_of_lists[0][n]
                links[(origin, link[0], link[1])].append(fragment_pks[n])

        # Convert the nodes into a dictionary
        label_cache = prepare_label_cache(scenario.corpus)
        new_nodes = []
        i = 0
        for language, nodes_per_language in nodes.items():
            for node in nodes_per_language:
                node_label, node_color, _ = get_label_properties_from_cache(node, label_cache, allow_empty=True)
                new_node = {'id': i, 'language': language, 'node': node, 'color': node_color, 'label': node_label}
                new_nodes.append(new_node)
                i += 1

        def find_node(list_of_dicts, language, node):
            result = {}
            for item in list_of_dicts:
                if item.get('language') in [language, '-'] and item.get('node') == node:
                    result = item
                    break
            return result

        # Convert the links into a dictionary
        new_links = []
        for link, fragment_pks in links.items():
            for l0, l1, l2 in zip(link, link[1:], link[2:]):
                l0_label, l0_color, _ = get_label_properties_from_cache(l0, label_cache)
                source = find_node(new_nodes, language_from_iso, l1)
                if not source:
                    source = find_node(new_nodes, language_to_iso, l1)
                new_link = {
                    'origin': find_node(new_nodes, language_from_iso, l0).get('id'),
                    'origin_label': l0_label, 'origin_color': l0_color,
                    'source': source.get('id'),
                    'target': find_node(new_nodes, language_to_iso, l2).get('id'),
                    'value': len(fragment_pks), 'fragment_pks': fragment_pks
                }
                new_links.append(new_link)
        new_links = sorted(new_links, key=lambda l: l['origin_color'])

        # JSONify the data and add it to the context
        context['data'] = json.dumps({'nodes': new_nodes, 'links': new_links})

        # Add selection of languages to the context
        context['languages_from'] = languages_from
        context['languages_to'] = languages_to
        context['selected_language_from'] = language_from_iso
        context['selected_language_to'] = language_to_iso
        context['lfrom_options'] = {
            'get_formal_structure_display': 'Formal structure',
            'get_sentence_function_display': 'Sentence function'
        }
        context['selected_lfrom_option'] = lfrom_option
        context['lto_options'] = {}  # None as of yet...
        context['selected_lto_option'] = lto_option

        if language_from.use_labels:
            for key in language_from.include_keys.all():
                context['lfrom_options'][key.title] = key.title

        if language_to.use_labels:
            for key in language_to.include_keys.all():
                context['lto_options'][key.title] = key.title

        return context


class SankeyManual(generic.TemplateView):
    template_name = 'stats/sankey_manual.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['corpora'] = Corpus.objects.filter(check_structure=True)

        return context


class ScenarioDownload(ScenarioDetail):
    def get(self, request, *args, **kwargs):
        scenario = self.get_object()

        try:
            matrix_filename = 's{}-matrix.feather'.format(scenario.pk)
            export_matrix(matrix_filename, scenario)
        except ValueError:
            matrix_filename = None

        tensecats_filename = 'tensecats.feather'
        export_tensecats(tensecats_filename)

        fragments_filename = 's{}-labels.feather'.format(scenario.pk)
        export_fragments(fragments_filename, scenario)

        zip_filename = 's{}.zip'.format(scenario.pk)
        zip_file = ZipFile(zip_filename, 'w')
        if matrix_filename:
            zip_file.write(matrix_filename)
        zip_file.write(tensecats_filename)
        zip_file.write(fragments_filename)
        zip_file.close()

        with open(zip_filename, 'rb') as f:
            contents = f.read()
        if matrix_filename:
            os.unlink(matrix_filename)
        os.unlink(tensecats_filename)
        os.unlink(fragments_filename)
        os.unlink(zip_filename)

        response = HttpResponse(contents, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename={}'.format(zip_filename)
        return response
