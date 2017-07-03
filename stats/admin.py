from django.contrib import admin, messages

from .models import Scenario, ScenarioLanguage
from .utils import run_mds


class ScenarioLanguageInline(admin.TabularInline):
    model = ScenarioLanguage


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ('title', 'corpus', 'mds_dimensions')
    list_filter = ('corpus', )
    inlines = [ScenarioLanguageInline]
    actions = ['run_mds']

    def run_mds(self, request, queryset):
        for scenario in queryset:
            try:
                run_mds(scenario)
            except ValueError as e:
                self.message_user(request, 'Something went wrong while running scenario {}'.format(scenario.title), level=messages.ERROR)
        self.message_user(request, 'Selected scenarios have been run')

    run_mds.short_description = 'Run Multidimensional Scaling'
