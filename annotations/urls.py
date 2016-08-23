from django.conf.urls import url

from .views import StartView, HomeView, InstructionsView, ContactView,\
    AnnotationCreate, AnnotationUpdate, AnnotationChoose, AnnotationList, FragmentList,\
    PlotMatrixView, FragmentDetail

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

    # Showing Fragments
    url(r'^show/(?P<pk>\d+)/$', FragmentDetail.as_view(), name='show'),

    # List views
    url(r'^list/(?P<l1>\w+)/(?P<l2>\w+)/$', AnnotationList.as_view(), name='list'),
    url(r'^matrix/(?P<language>\w+)/$', FragmentList.as_view(), name='matrix'),
    url(r'^matrix/(?P<language>\w+)/(?P<showtenses>\w+)/$', FragmentList.as_view(), name='tense_matrix'),

    # Graphs
    url(r'^plot/$', PlotMatrixView.as_view(), name='plot'),
    url(r'^plot/(?P<language>\w+)/$', PlotMatrixView.as_view(), name='plot'),
    url(r'^plot/(?P<language>\w+)/(?P<d1>\d+)/(?P<d2>\d+)/$', PlotMatrixView.as_view(), name='plot'),
]
