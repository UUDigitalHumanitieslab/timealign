from django.conf.urls import url

from .views import InstructionsView, IntroductionView, StatusView, \
    AnnotationCreate, AnnotationUpdate, AnnotationChoose, FragmentDetail, \
    AnnotationList, FragmentList, PlotMatrixView

urlpatterns = [
    # Static views
    url(r'^introduction/$', IntroductionView.as_view(), name='introduction'),
    url(r'^instructions/(?P<n>\d+)/$', InstructionsView.as_view(), name='instructions'),
    url(r'^status/$', StatusView.as_view(), name='status'),

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
