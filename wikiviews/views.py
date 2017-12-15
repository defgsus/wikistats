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
    TRANSFORMS = (
        ("", "none", None),
        ("grad", "np.gradient", lambda a: np.gradient(a)),
        ("diff", "np.diff", lambda a: np.diff(a)),
        ("fft", "np.fft", lambda a: np.real(np.fft.fft(a))[2:len(a)//2+1]),
        ("clip", "clip mean+std", lambda a: np.clip(a, 0, np.mean(a)+np.std(a)))
    )

    art_name = request.GET.get("article")
    transform_name = request.GET.get("transform", "")

    transform = None
    if transform_name:
        trans = sorted(TRANSFORMS, key=lambda x: x[0] == transform_name)[-1]
        transform = trans[2]

    term = None
    correlations = []
    qset = WikiPageviews.objects.filter(term__name=art_name)

    # try to retrieve pageviews
    if not qset.exists():
        qset = WikiTerm.objects.filter(name=art_name)
        if qset.exists():
            get_pageviews_and_store(2016, qset[0])

    def _get_array(views):
        a = views.views_per_day()
        if transform is not None:
            a = transform(a)
        return a

    qset = WikiPageviews.objects.filter(term__name=art_name)
    if qset.exists():

        base_views = qset[0]
        term = base_views.term
        base_array = _get_array(base_views)

        qset = WikiPageviews.objects.all()
        for view in qset:
            comp_array = _get_array(view)
            corr = np.corrcoef(base_array, comp_array)[0][1]
            if corr <= -.3 or corr >= .5:
                correlations.append({
                    "name": view.term.name,
                    "desc": view.term.description,
                    "url": view.term.url,
                    "corr_url": "?article=%s&transform=%s" % (view.term.name, transform_name),
                    "count": view.count,
                    "correlation": round(corr, 3),
                    "views_decorator": view.views_decorator(transform=transform),
                })

    ctx = {
        "term": term,
        "correlations": sorted(correlations, key=lambda c: -c["correlation"])[:100],
        "transforms": TRANSFORMS,
        "current_transform": transform_name,
    }
    return render(request, "wikiviews/correlations.html", ctx)