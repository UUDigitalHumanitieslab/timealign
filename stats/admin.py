import logging
from django.contrib import admin, messages
from django.db.models import Prefetch
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

from django_object_actions import BaseDjangoObjectActions

from .forms import ScenarioForm, ScenarioLanguageForm
from .models import Scenario, ScenarioLanguage
from .utils import run_mds, copy_scenario, EmptyScenario


logger = logging.getLogger()


class ScenarioLanguageInline(admin.StackedInline):
    model = ScenarioLanguage
    form = ScenarioLanguageForm
    extra = 1
    verbose_name = 'Language in Scenario'
    verbose_name_plural = 'Languages in Scenario'


@admin.register(Scenario)
class ScenarioAdmin(BaseDjangoObjectActions, admin.ModelAdmin):
    form = ScenarioForm
    list_display = ('title', 'corpus', 'is_test', 'from_languages', 'to_languages', 'last_run', )
    list_filter = ('corpus', 'scenariolanguage__language', 'owner')
    list_per_page = 25

    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'is_test', )
        }),
        ('Filters', {
            'fields': ('corpus', 'documents', 'subcorpora',
                       ('formal_structure', 'formal_structure_strict', ),
                       'sentence_function', )
        }),
        ('Multidimensional Scaling', {
            'classes': ('collapse',),
            'fields': ('mds_dimensions', 'mds_allow_partial')
        })
    )

    inlines = [ScenarioLanguageInline]

    def get_queryset(self, request):
        languages_from = ScenarioLanguage.objects.filter(as_from=True).select_related('language')
        languages_to = ScenarioLanguage.objects.filter(as_to=True).select_related('language')
        return super().get_queryset(request) \
            .prefetch_related(Prefetch('scenariolanguage_set', queryset=languages_from, to_attr='languages_from'),
                              Prefetch('scenariolanguage_set', queryset=languages_to, to_attr='languages_to')) \
            .defer('mds_model', 'mds_matrix', 'mds_fragments', 'mds_labels')  # Don't fetch the PickledObjectFields

    def run_mds(self, request, obj):
        try:
            run_mds(obj)
            obj.last_run = timezone.now()
            obj.save()
            self.message_user(request, mark_safe('Multidimensional Scaling has been run.'))
        except EmptyScenario:
            self.message_user(request, 'Scenario configuration produced an empty data set', level=messages.ERROR)
        except ValueError:
            message = 'Something went wrong while running scenario {}'.format(obj.title)
            self.message_user(request, message, level=messages.ERROR)
            logger.exception('Error running scenario {}'.format(obj.title))

    run_mds.label = '(Re)run Multidimensional Scaling'
    run_mds.short_description = '(Re)run Multidimensional Scaling'

    def copy_scenario(self, request, obj):
        try:
            new_scenario = copy_scenario(request, obj)
            success_link = reverse('admin:stats_scenario_change', args=(new_scenario.pk,))
            message = 'Scenario has been copied. <a href="{}">Find it here</a>.'.format(success_link)
            self.message_user(request, mark_safe(message))
        except ValueError:
            message = 'Something went wrong while copying scenario {}'.format(obj.title)
            self.message_user(request, message, level=messages.ERROR)
    copy_scenario.label = 'Copy scenario'
    copy_scenario.short_description = 'Copy scenario'

    change_actions = ['run_mds', 'copy_scenario']

    def save_model(self, request, obj, form, change):
        if obj.owner is None:
            # Avoid changing ownership when editing an existing scenario
            obj.owner = request.user
        super().save_model(request, obj, form, change)
