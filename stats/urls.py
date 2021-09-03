from django.urls import path, re_path

from .views import ScenarioList, ScenarioDetail, ScenarioDownload, ScenarioManual, \
    MDSView, MDSViewOld, \
    DescriptiveStatsView, FragmentTableView, \
    FragmentTableViewMDS, UpsetView, SankeyView, SankeyManual, process_captcha

urlpatterns = [

    # List views
    path('scenarios/', ScenarioList.as_view(), name='scenarios'),

    # Manual
    path('scenarios/manual/', ScenarioManual.as_view(), name='scenarios_manual'),

    # Detail views
    re_path(r'^show/(?P<pk>\d+)/$', ScenarioDetail.as_view(), name='show'),
    re_path(r'^download/(?P<pk>\d+)/$', ScenarioDownload.as_view(), name='download'),

    # Multidimensional Scaling
    re_path(r'^mds/(?P<pk>\d+)/$', MDSView.as_view(), name='mds'),
    re_path(r'^mds/(?P<pk>\d+)/(?P<language>\w+)/$', MDSView.as_view(), name='mds'),
    re_path(r'^mds/(?P<pk>\d+)/(?P<language>\w+)/(?P<d1>\d+)/(?P<d2>\d+)/$', MDSView.as_view(), name='mds'),
    # ... and similar for the old version
    re_path(r'^mds_old/(?P<pk>\d+)/$', MDSViewOld.as_view(), name='mds_old'),
    re_path(r'^mds_old/(?P<pk>\d+)/(?P<language>\w+)/$', MDSViewOld.as_view(), name='mds_old'),
    re_path(r'^mds_old/(?P<pk>\d+)/(?P<language>\w+)/(?P<d1>\d+)/(?P<d2>\d+)/$', MDSViewOld.as_view(), name='mds_old'),

    # Fragment Table
    path('fragment_table/', FragmentTableView.as_view(), name='fragment_table'),
    path('mds/fragment_table/', FragmentTableViewMDS.as_view(), name='fragment_table_mds'),

    # Upset
    re_path(r'upset/(?P<pk>\d+)/$', UpsetView.as_view(), name='upset'),
    re_path(r'upset/(?P<pk>\d+)/(?P<tc>\d+)/$', UpsetView.as_view(), name='upset'),

    # Sankey
    re_path(r'sankey/(?P<pk>\d+)/$', SankeyView.as_view(), name='sankey'),
    path('sankey_manual/', SankeyManual.as_view(), name='sankey_manual'),

    # Descriptive statistics
    re_path(r'^descriptive/(?P<pk>\d+)/$', DescriptiveStatsView.as_view(), name='descriptive'),

    # Captcha
    path('captcha/', process_captcha, name='captcha_check'),
]
