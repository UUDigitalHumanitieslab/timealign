from django.conf.urls import url

from .views import StartView, PeopleView, ContactView, IntroductionView


urlpatterns = [
    # Static views
    url(r'^$', StartView.as_view(), name='start'),
    url(r'^people/$', PeopleView.as_view(), name='people'),
    url(r'^contact/$', ContactView.as_view(), name='contact'),

    url(r'^introduction/$', IntroductionView.as_view(), name='introduction'),
]
