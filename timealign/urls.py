"""timealign URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView
from django.contrib.flatpages import views

urlpatterns = [
    url(r'^accounts/login/$', LoginView.as_view(), name='login'),
    url(r'^accounts/logout/$', LogoutView.as_view(), name='logout'),
    url(r'^accounts/password/change/$', PasswordChangeView.as_view(), name='password_change'),
    url(r'^accounts/password/change/done/$', PasswordChangeDoneView.as_view(), name='password_change_done'),

    url(r'^timealign/', include(('annotations.urls', 'annotations'), namespace='annotations')),
    url(r'^preselect/', include(('selections.urls', 'selections'), namespace='selections')),
    url(r'^stats/', include(('stats.urls', 'stats'), namespace='stats')),
    url(r'^news/', include(('news.urls', 'news'), namespace='news')),

    url(r'^admin/', admin.site.urls),

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

    url(r'^ckeditor/', include('ckeditor_uploader.urls')),
    url(r'^nested_admin/', include('nested_admin.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
