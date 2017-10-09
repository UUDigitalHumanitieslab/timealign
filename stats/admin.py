from django.contrib import admin, messages
from django.utils import timezone

from django_object_actions import DjangoObjectActions

from .forms import ScenarioLanguageForm
from .models import Scenario, ScenarioLanguage
from .utils import run_mds


class ScenarioLanguageInline(admin.TabularInline):
    model = ScenarioLanguage
    form = ScenarioLanguageForm


@admin.register(Scenario)
class ScenarioAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = ('title', 'corpus', 'mds_dimensions', 'last_run', )
    list_filter = ('corpus', )
    inlines = [ScenarioLanguageInline]

    def run_mds(self, request, obj):
        try:
            run_mds(obj)
            obj.last_run = timezone.now()
            obj.save()
        except ValueError as e:
            self.message_user(request,
                              'Something went wrong while running scenario {}'.format(obj.title),
                              level=messages.ERROR)
        self.message_user(request, 'Multidimensional Scaling has been run')
    run_mds.label = '(Re)run Multidimensional Scaling'
    run_mds.short_description = '(Re)run Multidimensional Scaling'

    change_actions = ['run_mds']
