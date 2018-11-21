from django.contrib import admin, messages
from django.utils import timezone
from django.utils.safestring import mark_safe

from django_object_actions import DjangoObjectActions

from .forms import ScenarioForm, ScenarioLanguageForm
from .models import Scenario, ScenarioLanguage
from .utils import run_mds


class ScenarioLanguageInline(admin.TabularInline):
    model = ScenarioLanguage
    form = ScenarioLanguageForm
    extra = 1
    verbose_name = 'Language in Scenario'
    verbose_name_plural = 'Languages in Scenario'


@admin.register(Scenario)
class ScenarioAdmin(DjangoObjectActions, admin.ModelAdmin):
    form = ScenarioForm
    list_display = ('title', 'corpus', 'is_test', 'from_languages', 'to_languages', 'last_run', )
    list_filter = ('corpus', 'scenariolanguage__language', 'owner')

    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'is_test', )
        }),
        ('Filters', {
            'fields': ('corpus', 'documents', 'focus_sets', ('formal_structure', 'formal_structure_strict', ), 'sentence_function', )
        }),
        ('Multidimensional Scaling', {
            'classes': ('collapse',),
            'fields': ('mds_dimensions', 'mds_allow_partial')
        })
    )

    inlines = [ScenarioLanguageInline]

    def run_mds(self, request, obj):
        try:
            run_mds(obj)
            obj.last_run = timezone.now()
            obj.save()
        except ValueError:
            self.message_user(request,
                              'Something went wrong while running scenario {}'.format(obj.title),
                              level=messages.ERROR)
        self.message_user(request, mark_safe('Multidimensional Scaling has been run.'))
    run_mds.label = '(Re)run Multidimensional Scaling'
    run_mds.short_description = '(Re)run Multidimensional Scaling'

    change_actions = ['run_mds']

    def save_model(self, request, obj, form, change):
        if obj.owner is None:
            # Avoid changing ownership when editing an existing scenario
            obj.owner = request.user
        super(ScenarioAdmin, self).save_model(request, obj, form, change)
