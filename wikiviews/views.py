# coding=utf-8
from __future__ import unicode_literals, print_function

import numpy as np
import scipy

from django.shortcuts import render
from django.http import JsonResponse, Http404

from .models import *
from tools.opensearch import opensearch_and_store
from tools.pageviews import get_pageviews_and_store


def autocomplete_json(request):
    query = request.GET.get("q")
    if not query:
        raise Http404

    if "w" in request.GET:
        res = opensearch_and_store(query, limit=100)
        return JsonResponse({
            "items": [i["name"] for i in res[:20]]
        })

    qset = WikiPageviews.objects.filter(term__name__icontains=query)
    items = qset.order_by("term__name").values_list("term__name")
    items = [t[0] for t in items[:20]]
    return JsonResponse({
        "items": items
    })



def correlation_view(request):
    def _normalize(a):
        m = np.linalg.norm(a)
        if m:
            return a / m
        return a

    WEEKDAYS = [datetime.date.fromordinal(datetime.date(2016, 1, 1).toordinal()+i).weekday() for i in range(366)]
    def _weekday(a):
        r = np.zeros(7)
        for i, v in enumerate(a):
            r[WEEKDAYS[i]] += v
        return r

    TRANSFORMS = (
        ("", "none", None),
        ("grad", "np.gradient", lambda a: np.gradient(a)),
        ("diff", "np.diff", lambda a: np.diff(a)),
        ("fft", "np.fft", lambda a: np.real(np.fft.fft(a))[2:len(a)//2+1]),
        ("clip", "clip mean+std", lambda a: np.clip(a, 0, np.mean(a)+np.std(a))),
        ("weekday", "weekday", lambda a: _weekday(a))
    )
    COMPARISONS = (
        ("corr", "correlation",
            lambda x, y: np.corrcoef(x, y)[0][1],
            lambda v: v <= -.3 or v >= .5,
            lambda v: -v,
        ),
        ("ndist", "norm distance",
            lambda x, y: np.linalg.norm(x-y) / np.sum(np.abs(x-y)),
            lambda v: v < .5,
            lambda v: v,
        ),
    )

    art_name = request.GET.get("article")
    transform_name = request.GET.get("transform", "")
    compare_name = request.GET.get("compare", "corr")

    transform = None
    if transform_name:
        trans = sorted(TRANSFORMS, key=lambda x: x[0] == transform_name)[-1]
        transform = trans[2]

    compr = sorted(COMPARISONS, key=lambda x: x[0] == compare_name)[-1]


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
        else:
            a = np.array(a, dtype="float64")
        return a

    qset = WikiPageviews.objects.filter(term__name=art_name)
    if qset.exists():

        base_views = qset[0]
        term = base_views.term
        base_array = _get_array(base_views)

        qset = WikiPageviews.objects.all()
        for view in qset:
            comp_array = _get_array(view)
            corr = compr[2](base_array, comp_array)
            if compr[3](corr):
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
        "correlations": sorted(correlations, key=lambda c: compr[4](c["correlation"]))[:100],
        "transforms": TRANSFORMS,
        "comparisons": COMPARISONS,
        "current_transform": transform_name,
        "current_compare": compare_name,
        "current_compare_name": compr[1],
    }
    return render(request, "wikiviews/correlations.html", ctx)