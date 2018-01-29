from django.contrib import admin, messages
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
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
    list_filter = ('corpus', 'scenariolanguage__language', )

    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'is_test', )
        }),
        ('Filters', {
            'fields': ('corpus', 'documents', ('formal_structure', 'formal_structure_strict', ), )
        }),
        ('Multidimensional Scaling', {
            'classes': ('collapse',),
            'fields': ('mds_dimensions', )
        })
    )

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
        self.message_user(request, mark_safe('Multidimensional Scaling has been run.'))
    run_mds.label = '(Re)run Multidimensional Scaling'
    run_mds.short_description = '(Re)run Multidimensional Scaling'

    change_actions = ['run_mds']
