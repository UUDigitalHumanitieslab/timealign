from django.urls import path, re_path

from .views import InstructionsView, IntroductionView, StatusView, \
    SelectionCreate, SelectionUpdate, SelectionDelete, SelectionChoose, SelectionList, \
    PrepareDownload, SelectionsPrepare, SelectionsDownload, \
    AddPreProcessFragmentsView, ConvertSelectionsView

urlpatterns = [
    # Static views
    path('introduction/', IntroductionView.as_view(), name='introduction'),
    re_path(r'^instructions/(?P<n>\d+)/$', InstructionsView.as_view(), name='instructions'),
    path('status/', StatusView.as_view(), name='status'),
    re_path(r'^status/(?P<pk>\d+)/$', StatusView.as_view(), name='status'),

    # Creating and editing Selections
    re_path(r'^create/(?P<pk>\d+)/$', SelectionCreate.as_view(), name='create'),
    re_path(r'^edit/(?P<pk>\d+)/$', SelectionUpdate.as_view(), name='edit'),
    re_path(r'^delete/(?P<pk>\d+)/$', SelectionDelete.as_view(), name='delete'),
    re_path(r'^choose/(?P<corpus>\d+)/(?P<language>\w+)/$', SelectionChoose.as_view(), name='choose'),
    re_path(r'^choose/(?P<language>\w+)/$', SelectionChoose.as_view(), name='choose'),

    # List views
    re_path(r'^list/(?P<language>\w+)/$', SelectionList.as_view(), name='list'),

    # Downloads
    re_path(r'^prepare_download/(?P<language>\w+)/(?P<corpus>\w+)$', PrepareDownload.as_view(), name='prepare_download'),
    re_path(r'^prepare_download/(?P<language>\w+)$', PrepareDownload.as_view(), name='prepare_download'),
    path('download/', SelectionsPrepare.as_view(), name='download_start'),
    path('download_ready/', SelectionsDownload.as_view(), name='download_ready'),

    # Imports
    path('add_fragments/', AddPreProcessFragmentsView.as_view(), name='add-fragments'),
    path('convert_selections/', ConvertSelectionsView.as_view(), name='convert-selections'),
]
