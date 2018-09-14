from django import template

from annotations.models import Document, Fragment

register = template.Library()


# @register.inclusion_tag('_test.html')
