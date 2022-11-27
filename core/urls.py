from django.urls import path
from django.views.generic import TemplateView

from core.views import ActivateLanguageView

urlpatterns = [
    path('', TemplateView.as_view(template_name='landing/home.html'), name='home'),
    path('researcher', TemplateView.as_view(template_name='landing/researcher.html'), name='researcher'),
    path('teacher', TemplateView.as_view(template_name='landing/teacher.html'), name='teacher'),
    path('student', TemplateView.as_view(template_name='landing/student.html'), name='student'),
    path('language/activate/<language_code>/', ActivateLanguageView.as_view(), name='activate_language')
]
