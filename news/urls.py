from django.urls import path, re_path

from .views import PostList, PostDetail

urlpatterns = [
    # List views
    path('', PostList.as_view(), name='posts'),

    # Detail views
    re_path(r'^(?P<slug>[\w-]+)$', PostDetail.as_view(), name='show'),
]
