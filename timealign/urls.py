"""timealign URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.flatpages import views

urlpatterns = [
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', name='login'),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', name='logout'),

    url(r'^timealign/', include('annotations.urls', namespace='annotations')),
    url(r'^vpselect/', include('selections.urls', namespace='selections')),
    url(r'^stats/', include('stats.urls', namespace='stats')),

    url(r'^admin/', include(admin.site.urls)),

    url(r'^$', views.flatpage, {'url': '/home/'}, name='home'),
    url(r'^project/$', views.flatpage, {'url': '/project/'}, name='project'),
    url(r'^project/nl-summary/$', views.flatpage, {'url': '/project/nl-summary/'}, name='nl-summary'),
    url(r'^project/collaborations/$', views.flatpage, {'url': '/project/collaborations/'}, name='collaborations'),
    url(r'^project/videos/$', views.flatpage, {'url': '/project/videos/'}, name='videos'),
    url(r'^publications/$', views.flatpage, {'url': '/publications/'}, name='publications'),
    url(r'^student-research/$', views.flatpage, {'url': '/student-research/'}, name='student-research'),
    url(r'^workshops/$', views.flatpage, {'url': '/workshops/'}, name='workshops'),
    url(r'^expert-meetings/$', views.flatpage, {'url': '/expert-meetings/'}, name='expert-meetings'),
    url(r'^perfectextractor/$', views.flatpage, {'url': '/perfectextractor/'}, name='perfectextractor'),
    url(r'^translation-mining/$', views.flatpage, {'url': '/translation-mining/'}, name='translation-mining'),
    url(r'^contact/$', views.flatpage, {'url': '/contact/'}, name='contact'),
]
