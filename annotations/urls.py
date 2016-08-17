from django.conf.urls import url

from .views import StartView, HomeView, InstructionsView, ContactView,\
    AnnotationCreate, AnnotationUpdate, AnnotationChoose, AnnotationList, FragmentList

urlpatterns = [
    # Static views
    url(r'^$', StartView.as_view(), name='start'),
    url(r'^home/$', HomeView.as_view(), name='home'),
    url(r'^instructions/(?P<n>\d+)/$', InstructionsView.as_view(), name='instructions'),
    url(r'^contact/$', ContactView.as_view(), name='contact'),

    # Creating and editing Annotations
    url(r'^create/(?P<pk>\d+)/$', AnnotationCreate.as_view(), name='create'),
    url(r'^edit/(?P<pk>\d+)/$', AnnotationUpdate.as_view(), name='edit'),
    url(r'^choose/(?P<l1>\w+)/(?P<l2>\w+)/$', AnnotationChoose.as_view(), name='choose'),

    # List views
    url(r'^list/(?P<l1>\w+)/(?P<l2>\w+)/$', AnnotationList.as_view(), name='list'),
    url(r'^matrix/(?P<language>\w+)/$', FragmentList.as_view(), name='matrix'),
    url(r'^matrix/(?P<language>\w+)/(?P<showtenses>\w+)/$', FragmentList.as_view(), name='tense_matrix'),
]
