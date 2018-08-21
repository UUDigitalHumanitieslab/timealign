from django.conf.urls import url

from .views import ThesisList

urlpatterns = [
    # List views
    url(r'^theses/$', ThesisList.as_view(), name='theses'),
]
