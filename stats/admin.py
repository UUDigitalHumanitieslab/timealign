from django.contrib import admin

from .models import Scenario, ScenarioLanguage
from .utils import run_mds


class ScenarioLanguageInline(admin.TabularInline):
    model = ScenarioLanguage


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ('title', )
    inlines = [ScenarioLanguageInline]
    actions = ['run_mds']

    def run_mds(self, request, queryset):
        for scenario in queryset:
            run_mds(scenario)

    run_mds.short_description = 'Run Multidimensional Scaling'
