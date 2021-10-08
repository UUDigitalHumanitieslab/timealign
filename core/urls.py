from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name='landing/home.html'), name='home'),
    path('researcher', TemplateView.as_view(template_name='landing/researcher.html'), name='researcher'),
    path('teacher', TemplateView.as_view(template_name='landing/teacher.html'), name='teacher'),
    path('student', TemplateView.as_view(template_name='landing/student.html'), name='student'),
]
