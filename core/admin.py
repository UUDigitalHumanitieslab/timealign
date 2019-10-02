from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User


class MyUserAdmin(UserAdmin):
    actions = ['activate', 'deactivate', 'grant_staff', 'revoke_staff']

    def activate(self, request, queryset):
        rows_updated = queryset.update(is_active=True)
        self.message_user(request, '{} user(s) successfully activated.'.format(rows_updated))
    activate.short_description = 'Activate selected users'

    def deactivate(self, request, queryset):
        rows_updated = queryset.update(is_active=False)
        self.message_user(request, '{} user(s) successfully deactivated.'.format(rows_updated))
    deactivate.short_description = 'Deactivate selected users'

    def grant_staff(self, request, queryset):
        rows_updated = queryset.update(is_staff=True)
        self.message_user(request, 'Granted staff status to {} user(s) successfully.'.format(rows_updated))
    grant_staff.short_description = 'Grant staff status to selected users'

    def revoke_staff(self, request, queryset):
        rows_updated = queryset.update(is_staff=False)
        self.message_user(request, 'Revoked staff status of {} user(s) successfully .'.format(rows_updated))
    revoke_staff.short_description = 'Revoke staff status of selected users'


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)
