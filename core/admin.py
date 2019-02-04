from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User


class MyUserAdmin(UserAdmin):
    actions = ['activate', 'deactivate']

    def activate(self, request, queryset):
        rows_updated = queryset.update(is_active=True)
        self.message_user(request, '{} user(s) successfully activated.'.format(rows_updated))
    activate.short_description = 'Activate selected users'

    def deactivate(self, request, queryset):
        rows_updated = queryset.update(is_active=False)
        self.message_user(request, '{} user(s) successfully deactivated.'.format(rows_updated))
    deactivate.short_description = 'Deactivate selected users'


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)
