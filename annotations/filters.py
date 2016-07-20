from django_filters import FilterSet

from .models import Annotation


class AnnotationFilter(FilterSet):
    class Meta:
        model = Annotation
        fields = ['is_no_target', 'is_translation']
