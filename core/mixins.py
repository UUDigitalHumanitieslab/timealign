from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin, AccessMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
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


class SuperuserRequiredMixin(UserPassesTestMixin):
    """Limits access only to superusers"""

    def test_func(self):
        return self.request.user.is_superuser


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


class LimitedPublicAccessMixin(AccessMixin):
    """Verify that the current user is either authenticated or has successfully completed captcha test."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated or self.temporary_access_valid(request):
            return super().dispatch(request, *args, **kwargs)
        else:
            # Redirect user to the captcha form page
            return HttpResponseRedirect("/stats/captcha/")

    def temporary_access_valid(self, request):
        """
        Check the validity of temporary access. Return true if the user has been granted temporary access. In this function, the access will be
        invalidated once it has passed the maximum time limit.
        """
        # Check if captcha has been completed properly
        lack_captcha = not request.session.get('succeed-captcha', False)
        if lack_captcha:
            return False

        return True
