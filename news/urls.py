from django.conf.urls import url

from .views import PostList, PostDetail

urlpatterns = [
    # List views
    url(r'^$', PostList.as_view(), name='posts'),

    # Detail views
    url(r'^(?P<slug>[\w-]+)$', PostDetail.as_view(), name='show'),
]
