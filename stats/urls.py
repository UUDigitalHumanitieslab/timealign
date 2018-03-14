from django.conf.urls import url

from .views import ScenarioList, ScenarioDetail, MDSView, DescriptiveStatsView

urlpatterns = [
    # List views
    url(r'^scenarios/$', ScenarioList.as_view(), name='scenarios'),

    # List views
    url(r'^show/(?P<pk>\d+)/$', ScenarioDetail.as_view(), name='show'),

    # Multidimensional Scaling
    url(r'^mds/(?P<pk>\d+)/$', MDSView.as_view(), name='mds'),
    url(r'^mds/(?P<pk>\d+)/(?P<language>\w+)/$', MDSView.as_view(), name='mds'),
    url(r'^mds/(?P<pk>\d+)/(?P<language>\w+)/(?P<d1>\d+)/(?P<d2>\d+)/$', MDSView.as_view(), name='mds'),

    # Stats
    url(r'^descriptive/(?P<pk>\d+)/$', DescriptiveStatsView.as_view(), name='descriptive'),
]
