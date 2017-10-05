from django.contrib import admin, messages
from django.utils import timezone

from .forms import ScenarioLanguageForm
from .models import Scenario, ScenarioLanguage
from .utils import run_mds


class ScenarioLanguageInline(admin.TabularInline):
    model = ScenarioLanguage
    form = ScenarioLanguageForm


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ('title', 'corpus', 'mds_dimensions', 'last_run')
    list_filter = ('corpus', )
    inlines = [ScenarioLanguageInline]
    actions = ['run_mds']

    def run_mds(self, request, queryset):
        for scenario in queryset:
            try:
                run_mds(scenario)
                scenario.last_run = timezone.now()
                scenario.save()
            except ValueError as e:
                self.message_user(request,
                                  'Something went wrong while running scenario {}'.format(scenario.title),
                                  level=messages.ERROR)
        self.message_user(request, 'Selected scenarios have been run')

    run_mds.short_description = '(Re)run Multidimensional Scaling'
