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
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView
from django.contrib.flatpages import views
from django.urls import include, path, re_path

urlpatterns = [
    path('accounts/login/', LoginView.as_view(), name='login'),
    path('accounts/logout/', LogoutView.as_view(), name='logout'),
    path('accounts/password/change/', PasswordChangeView.as_view(), name='password_change'),
    path('accounts/password/change/done/', PasswordChangeDoneView.as_view(), name='password_change_done'),

    path('captcha/', include('captcha.urls')),

    re_path(r'^timealign/', include(('annotations.urls', 'annotations'), namespace='annotations')),
    re_path(r'^preselect/', include(('selections.urls', 'selections'), namespace='selections')),
    re_path(r'^stats/', include(('stats.urls', 'stats'), namespace='stats')),
    re_path(r'^news/', include(('news.urls', 'news'), namespace='news')),

    re_path(r'^admin/', admin.site.urls),

    path('', views.flatpage, {'url': '/home/'}, name='home'),
    path('project/', views.flatpage, {'url': '/project/'}, name='project'),
    path('project/nl-summary/', views.flatpage, {'url': '/project/nl-summary/'}, name='nl-summary'),
    path('project/collaborations/', views.flatpage, {'url': '/project/collaborations/'}, name='collaborations'),
    path('project/videos/', views.flatpage, {'url': '/project/videos/'}, name='videos'),
    path('publications/', views.flatpage, {'url': '/publications/'}, name='publications'),
    path('student-research/', views.flatpage, {'url': '/student-research/'}, name='student-research'),
    path('workshops/', views.flatpage, {'url': '/workshops/'}, name='workshops'),
    path('expert-meetings/', views.flatpage, {'url': '/expert-meetings/'}, name='expert-meetings'),
    path('perfectextractor/introduction/', views.flatpage, {'url': '/perfectextractor/introduction/'}, name='perfectextractor'),
    path('translation-mining/', views.flatpage, {'url': '/translation-mining/'}, name='translation-mining'),
    path('contact/', views.flatpage, {'url': '/contact/'}, name='contact'),

    re_path(r'^ckeditor/', include('ckeditor_uploader.urls')),
    re_path(r'^nested_admin/', include('nested_admin.urls')),
    re_path(r'^robots\.txt', include('robots.urls')),
    re_path(r'^perfectextractor/', include('perfectextractor_ui.urls'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# if settings.DEBUG:
#     import debug_toolbar
#
#     urlpatterns = [
#         re_path(r'^__debug__/', include(debug_toolbar.urls)),
#     ] + urlpatterns
