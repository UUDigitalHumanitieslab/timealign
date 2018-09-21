from django.conf.urls import url

from .views import ScenarioList, ScenarioDetail, MDSView, MDSViewOld, DescriptiveStatsView, FragmentTableView

urlpatterns = [

    # List views
    url(r'^scenarios/$', ScenarioList.as_view(), name='scenarios'),

    # List views
    url(r'^show/(?P<pk>\d+)/$', ScenarioDetail.as_view(), name='show'),

    # Multidimensional Scaling
    url(r'^mds/(?P<pk>\d+)/$', MDSView.as_view(), name='mds'),
    url(r'^mds/(?P<pk>\d+)/(?P<language>\w+)/$', MDSView.as_view(), name='mds'),
    url(r'^mds/(?P<pk>\d+)/(?P<language>\w+)/(?P<d1>\d+)/(?P<d2>\d+)/$', MDSView.as_view(), name='mds'),
    # ... and similar for the old version
    url(r'^mds_old/(?P<pk>\d+)/$', MDSViewOld.as_view(), name='mds_old'),
    url(r'^mds_old/(?P<pk>\d+)/(?P<language>\w+)/$', MDSViewOld.as_view(), name='mds_old'),
    url(r'^mds_old/(?P<pk>\d+)/(?P<language>\w+)/(?P<d1>\d+)/(?P<d2>\d+)/$', MDSViewOld.as_view(), name='mds_old'),

    # Fragment Table
    url(r'^mds/fragment_table/(?P<pk>\d+)/$', FragmentTableView.as_view(), name='fragment_table'),

    # Descriptive statistics
    url(r'^descriptive/(?P<pk>\d+)/$', DescriptiveStatsView.as_view(), name='descriptive'),
]
