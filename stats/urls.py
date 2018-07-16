from django.conf.urls import url

from .views import (ScenarioList, ScenarioDetail, MDSView,
                    DescriptiveStatsView, FragmentTableView)

urlpatterns = [

    # List views
    url(r'^scenarios/$', ScenarioList.as_view(), name='scenarios'),

    # List views
    url(r'^show/(?P<pk>\d+)/$', ScenarioDetail.as_view(), name='show'),

    # Fragment Table
    url(r'^mds/fragment_table/$',
        FragmentTableView.as_view(), name='fragment_table'),
    # url(r'^mds/(?P<pk>\d+)/(?P<language>\w+)/fragmenttable/$',
    #     FragmentTableView.as_view(), name='fragmenttable'),
    # url(r'^mds/(?P<pk>\d+)/(?P<language>\w+)/(?P<d1>\d+)/(?P<d2>\d+) \
    #     /fragmenttable/$',
    #     FragmentTableView.as_view(), name='fragmenttable'),

    # Multidimensional Scaling
    url(r'^mds/(?P<pk>\d+)/$', MDSView.as_view(), name='mds'),
    url(r'^mds/(?P<pk>\d+)/(?P<language>\w+)/$',
        MDSView.as_view(), name='mds'),
    url(r'^mds/(?P<pk>\d+)/(?P<language>\w+)/(?P<d1>\d+)/(?P<d2>\d+)/$',
        MDSView.as_view(), name='mds'),



    # Stats
    url(r'^descriptive/(?P<pk>\d+)/$',
        DescriptiveStatsView.as_view(), name='descriptive'),
]
