from django.views import generic


class StartView(generic.TemplateView):
    """Loads a static start view"""
    template_name = 'core/start.html'


class PeopleView(generic.TemplateView):
    """Loads a static people view"""
    template_name = 'core/people.html'


class ContactView(generic.TemplateView):
    """Loads a static contact view"""
    template_name = 'core/contact.html'


class IntroductionView(generic.TemplateView):
    """Loads a static contact view"""
    template_name = 'core/introduction.html'
