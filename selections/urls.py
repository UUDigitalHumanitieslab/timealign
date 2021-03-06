from django.conf.urls import url

from .views import InstructionsView, IntroductionView, StatusView, \
    SelectionCreate, SelectionUpdate, SelectionDelete, SelectionChoose, SelectionList, \
    PrepareDownload, SelectionsPrepare, SelectionsDownload, \
    AddPreProcessFragmentsView, ConvertSelectionsView

urlpatterns = [
    # Static views
    url(r'^introduction/$', IntroductionView.as_view(), name='introduction'),
    url(r'^instructions/(?P<n>\d+)/$', InstructionsView.as_view(), name='instructions'),
    url(r'^status/$', StatusView.as_view(), name='status'),
    url(r'^status/(?P<pk>\d+)/$', StatusView.as_view(), name='status'),

    # Creating and editing Selections
    url(r'^create/(?P<pk>\d+)/$', SelectionCreate.as_view(), name='create'),
    url(r'^edit/(?P<pk>\d+)/$', SelectionUpdate.as_view(), name='edit'),
    url(r'^delete/(?P<pk>\d+)/$', SelectionDelete.as_view(), name='delete'),
    url(r'^choose/(?P<corpus>\d+)/(?P<language>\w+)/$', SelectionChoose.as_view(), name='choose'),
    url(r'^choose/(?P<language>\w+)/$', SelectionChoose.as_view(), name='choose'),

    # List views
    url(r'^list/(?P<language>\w+)/$', SelectionList.as_view(), name='list'),

    # Downloads
    url(r'^prepare_download/(?P<language>\w+)/(?P<corpus>\w+)$', PrepareDownload.as_view(), name='prepare_download'),
    url(r'^prepare_download/(?P<language>\w+)$', PrepareDownload.as_view(), name='prepare_download'),
    url(r'^download$', SelectionsPrepare.as_view(), name='download_start'),
    url(r'^download_ready$', SelectionsDownload.as_view(), name='download_ready'),

    # Imports
    url(r'^add_fragments/$', AddPreProcessFragmentsView.as_view(), name='add-fragments'),
    url(r'^convert_selections/$', ConvertSelectionsView.as_view(), name='convert-selections'),
]
