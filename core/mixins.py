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


class SelectSegmentMixin:
    def get_form_kwargs(self):
        """Sets select_fragment as a form kwarg"""
        kwargs = super(SelectSegmentMixin, self).get_form_kwargs()
        kwargs['select_segment'] = self.request.session.get('select_segment', False)
        return kwargs

    def form_valid(self, form):
        """save user preferred selection tool on the session"""
        self.request.session['select_segment'] = form.cleaned_data['select_segment']
        return super(SelectSegmentMixin, self).form_valid(form)


class FluidMixin(generic.base.ContextMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['container_fluid'] = True
        return context
