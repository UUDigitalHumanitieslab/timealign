from django.urls import path, re_path

from .views import InstructionsView, IntroductionView, StatusView, \
    AnnotationCreate, AnnotationUpdate, AnnotationDelete, AnnotationChoose, \
    FragmentEdit, FragmentDetail, FragmentDetailPlain, AnnotationList, FragmentList, ExportPOSDownload, ExportPOSPrepare, PrepareDownload, \
    TenseCategoryList, LabelList, ImportLabelsView, CorpusList, CorpusDetail, DocumentDetail, SourceDetail, AddFragmentsView

urlpatterns = [
    # Static views
    path('introduction/', IntroductionView.as_view(), name='introduction'),
    re_path(r'^instructions/(?P<n>\d+)/$', InstructionsView.as_view(), name='instructions'),
    path('status/', StatusView.as_view(), name='status'),
    re_path(r'^status/(?P<pk>\d+)/$', StatusView.as_view(), name='status'),

    # Creating and editing Annotations
    re_path(r'^create/(?P<corpus>\d+)/(?P<pk>\d+)/$', AnnotationCreate.as_view(), name='create'),
    re_path(r'^edit/(?P<pk>\d+)/$', AnnotationUpdate.as_view(), name='edit'),
    re_path(r'^delete/(?P<pk>\d+)/$', AnnotationDelete.as_view(), name='delete'),
    re_path(r'^choose/(?P<corpus>\d+)/(?P<l1>\w+)/(?P<l2>\w+)/$', AnnotationChoose.as_view(), name='choose'),
    re_path(r'^choose/(?P<l1>\w+)/(?P<l2>\w+)/$', AnnotationChoose.as_view(), name='choose'),

    # Showing Fragments
    re_path(r'^show/(?P<pk>\d+)/$', FragmentDetail.as_view(), name='show'),
    re_path(r'^show/(?P<pk>\d+)/plain/$', FragmentDetailPlain.as_view(), name='show_plain'),
    re_path(r'^edit_fragment/(?P<pk>\d+)/$', FragmentEdit.as_view(), name='edit_fragment'),

    # Showing Corpora
    path('corpora/', CorpusList.as_view(), name='corpora'),
    re_path(r'^corpus/(?P<pk>\d+)/$', CorpusDetail.as_view(), name='corpus'),

    # Showing Documents
    re_path(r'^document/(?P<pk>\d+)/$', DocumentDetail.as_view(), name='document'),

    # Showing Sources
    re_path(r'^source/(?P<pk>\d+)/$', SourceDetail.as_view(), name='source'),

    # List views
    re_path(r'^list/(?P<l1>\w+)/(?P<l2>\w+)/$', AnnotationList.as_view(), name='list'),
    re_path(r'^matrix/(?P<language>\w+)/$', FragmentList.as_view(), name='matrix'),
    re_path(r'^matrix/(?P<language>\w+)/(?P<showtenses>\w+)/$', FragmentList.as_view(), name='tense_matrix'),
    path('tenses/', TenseCategoryList.as_view(), name='tenses'),
    path('labels/', LabelList.as_view(), name='labels'),
    re_path(r'^labels/(?P<corpus>\d+)/$', LabelList.as_view(), name='labels'),

    # Downloads
    re_path(r'^prepare_download/(?P<language>\w+)/(?P<corpus>\w+)$', PrepareDownload.as_view(), name='prepare_download'),
    re_path(r'^prepare_download/(?P<language>\w+)$', PrepareDownload.as_view(), name='prepare_download'),
    path('download/', ExportPOSPrepare.as_view(), name='download_start'),
    path('download_ready/', ExportPOSDownload.as_view(), name='download_ready'),

    # Importing of labels
    path('import_labels/', ImportLabelsView.as_view(), name='import-labels'),
    path('add_fragments/', AddFragmentsView.as_view(), name='add-fragments'),
]
