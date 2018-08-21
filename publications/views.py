# -*- coding: utf-8 -*-
from django.views import generic

from .models import Thesis


class ThesisList(generic.ListView):
    model = Thesis
    context_object_name = 'theses'
