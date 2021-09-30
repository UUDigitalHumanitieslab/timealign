from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path('landing', TemplateView.as_view(template_name='base/landing.html'), name='landing'),
    path('landing/researcher', TemplateView.as_view(template_name='base/landing-researcher.html'), name='landing-researcher'),
    path('landing/teacher', TemplateView.as_view(template_name='base/landing-teacher.html'), name='landing-teacher'),
    path('landing/student', TemplateView.as_view(template_name='base/landing-student.html'), name='landing-student'),
]
