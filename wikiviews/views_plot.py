# coding=utf-8
from __future__ import unicode_literals, print_function

import numpy as np
import scipy

from django.shortcuts import render
from django.http import JsonResponse, Http404

from .models import *
from .plot_tools import get_scatter_plot_markup

WEEKDAYS = [datetime.date.fromordinal(datetime.date(2016, 1, 1).toordinal() + i).weekday() for i in range(366)]

def _weekday(a):
    r = np.zeros(7)
    for i, v in enumerate(a):
        r[WEEKDAYS[i]] += v
    return r

DISTANCES = {
    "euclid": ("euclidean", lambda x, y: np.linalg.norm(x-y)),
    "corr": ("correlation", lambda x, y: 1. - np.corrcoef(x, y)[0][1]),
}

TRANSFORMS = {
    "": ("none", None),
    "grad": ("np.gradient", lambda a: np.gradient(a)),
    "diff": ("np.diff", lambda a: np.diff(a)),
    "fft": ("np.fft", lambda a: np.real(np.fft.fft(a))[2:len(a) // 2 + 1]),
    "clip": ("clip mean+std", lambda a: np.clip(a, 0, np.mean(a) + np.std(a))),
    "weekday": ("weekday", lambda a: _weekday(a)),
}


def get_pageview_plot_data(reduction_type, transform_type, distance_type):
    all_pageviews = WikiPageviews.objects.filter(count__gt=0)[:1000]
    all_values = list(all_pageviews.values_list("term__pk", "term__name", "count", "per_yearday"))

    ret = dict()
    ret["pk"] = [t[0] for t in all_values]
    ret["name"] = [t[1] for t in all_values]
    ret["total"] = [t[2] for t in all_values]

    view_data = np.zeros((len(all_values), 366))
    for y, datatup in enumerate(all_values):
        views = [int(i) for i in datatup[3].split(",")]
        if TRANSFORMS[transform_type][1]:
            views = TRANSFORMS[transform_type][1](views)
        for i in range(366):
            view_data[y][i] = views[i]

    from sklearn.decomposition import PCA, KernelPCA, FactorAnalysis, FastICA, LatentDirichletAllocation, NMF, IncrementalPCA
    from sklearn.manifold import TSNE

    XY = None
    if reduction_type == "pca":
        reducer = KernelPCA(n_components=2, kernel="poly", eigen_solver="arpack", degree=0.01, random_state=42)

    elif reduction_type == "tsne":
        #reducer = PCA(n_components=50, svd_solver='full')
        #XY = reducer.fit(view_data).transform(view_data)
        reducer = TSNE(n_components=2, random_state=42, n_iter=1000, verbose=2, metric=DISTANCES[distance_type][1])
        XY = reducer.fit_transform(view_data)

    else:
        raise ValueError("Unknown reduction_type '%s'" % reduction_type)

    if XY is None:
        XY = reducer.fit(view_data).transform(view_data)

    ret["x"] = [x[0] for x in XY]
    ret["y"] = [x[1] for x in XY]
    return ret


def get_pageview_plot_data_cached(reduction_type, transform_type, distance_type):
    cache_id = "pageview-plot-%s-%s-%s" % (reduction_type, transform_type, distance_type)
    data = PickleCache.restore(cache_id)
    if data is None:
        data = get_pageview_plot_data(reduction_type, transform_type, distance_type)
        PickleCache.store(cache_id, data)
    return data


def correlation_plot_view(request):
    WEEKDAYS = [datetime.date.fromordinal(datetime.date(2016, 1, 1).toordinal()+i).weekday() for i in range(366)]
    def _weekday(a):
        r = np.zeros(7)
        for i, v in enumerate(a):
            r[WEEKDAYS[i]] += v
        return r

    transform_type = request.GET.get("transform", "")
    distance_type = request.GET.get("distance", "corr")
    reduction_type = request.GET.get("reduction", "tsne")

    data = get_pageview_plot_data_cached(reduction_type, transform_type, distance_type)

    data["size"] = []
    min_total, max_total = min(data["total"]), max(data["total"])
    for i in range(len(data["pk"])):
        data["size"].append((float(data["total"][i])-min_total) / (max_total-min_total) * 8. + 2.)

    plot_markup = get_scatter_plot_markup(
        data,
        title="Wiki articles grouped by views 2016",
        width=800, height=600,
        #box_select_code=jscode,
    )

    ctx = {
        "content": plot_markup,
    }
    return render(request, "wikiviews/base.html", ctx)