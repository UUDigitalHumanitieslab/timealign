from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views import generic


class ImportMixin(SuccessMessageMixin, generic.FormView):
    def post(self, request, *args, **kwargs):
        # check for errors, and call the save method of the form
        form = self.get_form()
        if form.is_valid():
            try:
                form.save()
                return self.form_valid(form)
            except ValueError as e:
                messages.error(self.request, 'Error during import: {}'.format(e))
                return self.form_invalid(form)
        else:
            return self.form_invalid(form)


class CheckOwnerOrStaff(UserPassesTestMixin):
    """Limits access only to creator of annotation or staff users"""

    def test_func(self):
        return self.get_object().annotated_by == self.request.user or \
               self.request.user.is_staff or self.request.user.is_superuser


class FluidMixin(generic.base.ContextMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['container_fluid'] = True
        return context
