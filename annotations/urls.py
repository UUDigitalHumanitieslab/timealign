from django.conf.urls import url

from .views import StartView, HomeView, InstructionsView, ContactView,\
    AnnotationCreate, AnnotationList, AnnotationChoose

urlpatterns = [
    url(r'^$', StartView.as_view(), name='start'),
    url(r'^home/$', HomeView.as_view(), name='home'),
    url(r'^instructions/(?P<n>\d+)/$', InstructionsView.as_view(), name='instructions'),
    url(r'^contact/$', ContactView.as_view(), name='contact'),

    # List views
    url(r'^annotate/(?P<pk>\d+)/$', AnnotationCreate.as_view(), name='annotate'),
    url(r'^list/(?P<l1>\w+)/(?P<l2>\w+)/$', AnnotationList.as_view(), name='list'),
    url(r'^choose/(?P<l1>\w+)/(?P<l2>\w+)/$', AnnotationChoose.as_view(), name='choose'),
]
