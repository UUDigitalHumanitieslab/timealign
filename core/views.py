from django.shortcuts import redirect
from django.utils import translation
from django.views.generic.base import View


class ActivateLanguageView(View):
    language_code = ''
    redirect_to = ''

    def get(self, request, *args, **kwargs):
        self.redirect_to = request.META.get('HTTP_REFERER')
        self.language_code = kwargs.get('language_code')
        translation.activate(self.language_code)
        request.session[translation.LANGUAGE_SESSION_KEY] = self.language_code
        return redirect(self.redirect_to)
