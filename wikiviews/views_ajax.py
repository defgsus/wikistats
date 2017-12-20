# coding=utf-8
from __future__ import unicode_literals, print_function

import numpy as np
import scipy

from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.template.loader import render_to_string

from .models import *


def views_list(request):
    id_list = request.GET.get("ids")
    if id_list:
        id_list = [int(i) for i in id_list.split(",")]
        views = [WikiPageviews.objects.get(pk=i) for i in id_list]
        views.sort(key=lambda v: -v.count)
        ctx = {
            "views": views[:50],
        }
        return render(request, "wikiviews/views-list.html", ctx)
