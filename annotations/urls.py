from django.conf.urls import url

from .views import InstructionsView, IntroductionView, StatusView, \
    AnnotationCreate, AnnotationUpdate, AnnotationDelete, AnnotationChoose, \
    FragmentEdit, FragmentDetail, FragmentDetailPlain, \
    AnnotationList, FragmentList, ExportPOSDownload, ExportPOSPrepare, PrepareDownload, TenseCategoryList, \
    ImportLabelsView, CorpusList, CorpusDetail, DocumentDetail, SourceDetail, AddFragmentsView

urlpatterns = [
    # Static views
    url(r'^introduction/$', IntroductionView.as_view(), name='introduction'),
    url(r'^instructions/(?P<n>\d+)/$', InstructionsView.as_view(), name='instructions'),
    url(r'^status/$', StatusView.as_view(), name='status'),
    url(r'^status/(?P<pk>\d+)/$', StatusView.as_view(), name='status'),

    # Creating and editing Annotations
    url(r'^create/(?P<corpus>\d+)/(?P<pk>\d+)/$', AnnotationCreate.as_view(), name='create'),
    url(r'^edit/(?P<pk>\d+)/$', AnnotationUpdate.as_view(), name='edit'),
    url(r'^delete/(?P<pk>\d+)/$', AnnotationDelete.as_view(), name='delete'),
    url(r'^choose/(?P<corpus>\d+)/(?P<l1>\w+)/(?P<l2>\w+)/$', AnnotationChoose.as_view(), name='choose'),
    url(r'^choose/(?P<l1>\w+)/(?P<l2>\w+)/$', AnnotationChoose.as_view(), name='choose'),

    # Showing Fragments
    url(r'^show/(?P<pk>\d+)/$', FragmentDetail.as_view(), name='show'),
    url(r'^show/(?P<pk>\d+)/plain/$', FragmentDetailPlain.as_view(), name='show_plain'),
    url(r'^edit_fragment/(?P<pk>\d+)/$', FragmentEdit.as_view(), name='edit_fragment'),

    # Showing Corpora
    url(r'^corpora/$', CorpusList.as_view(), name='corpora'),
    url(r'^corpus/(?P<pk>\d+)/$', CorpusDetail.as_view(), name='corpus'),

    # Showing Documents
    url(r'^document/(?P<pk>\d+)/$', DocumentDetail.as_view(), name='document'),

    # Showing Sources
    url(r'^source/(?P<pk>\d+)/$', SourceDetail.as_view(), name='source'),

    # List views
    url(r'^list/(?P<l1>\w+)/(?P<l2>\w+)/$', AnnotationList.as_view(), name='list'),
    url(r'^matrix/(?P<language>\w+)/$', FragmentList.as_view(), name='matrix'),
    url(r'^matrix/(?P<language>\w+)/(?P<showtenses>\w+)/$', FragmentList.as_view(), name='tense_matrix'),
    url(r'^tenses/$', TenseCategoryList.as_view(), name='tenses'),

    # Downloads
    url(r'^prepare_download/(?P<language>\w+)/(?P<corpus>\w+)$', PrepareDownload.as_view(), name='prepare_download'),
    url(r'^prepare_download/(?P<language>\w+)$', PrepareDownload.as_view(), name='prepare_download'),
    url(r'^download$', ExportPOSPrepare.as_view(), name='download_start'),
    url(r'^download_ready$', ExportPOSDownload.as_view(), name='download_ready'),

    # Importing of labels
    url(r'^import_labels/$', ImportLabelsView.as_view(), name='import-labels'),
    url(r'^add_fragments/$', AddFragmentsView.as_view(), name='add-fragments'),
]
