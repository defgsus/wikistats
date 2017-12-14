# coding=utf-8
from __future__ import unicode_literals, print_function

import numpy as np

from django.shortcuts import render
from django.http import JsonResponse, Http404

from .models import *
from tools.opensearch import opensearch_and_store
from tools.pageviews import get_pageviews_and_store


def autocomplete_json(request):
    query = request.GET.get("q")
    if not query:
        raise Http404

    res = opensearch_and_store(query, limit=100)
    return JsonResponse({
        "items": [i["name"] for i in res[:20]]
    })



def correlation_view(request):
    art_name = request.GET.get("article")

    term = None
    correlations = []
    qset = WikiPageviews.objects.filter(term__name=art_name)

    # try to retrieve pageviews
    if not qset.exists():
        qset = WikiTerm.objects.filter(name=art_name)
        if qset.exists():
            get_pageviews_and_store(2016, qset[0])

    qset = WikiPageviews.objects.filter(term__name=art_name)
    if qset.exists():

        base_views = qset[0]
        term = base_views.term
        base_views = base_views.views_per_day()

        qset = WikiPageviews.objects.all()
        for view in qset:
            corr = np.corrcoef(base_views, view.views_per_day())[0][1]
            if abs(corr) > .5:
                correlations.append({
                    "name": view.term.name,
                    "url": view.term.url,
                    "count": view.count,
                    "correlation": round(corr, 3),
                    "views_decorator": view.views_decorator(),
                })

    ctx = {
        "term": term,
        "correlations": sorted(correlations, key=lambda c: -c["correlation"])[:100],
    }
    return render(request, "wikiviews/correlations.html", ctx)