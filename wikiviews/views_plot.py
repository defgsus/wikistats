# coding=utf-8
from __future__ import unicode_literals, print_function

import numpy as np
import scipy

from django.shortcuts import render
from django.http import JsonResponse, Http404

from .models import *
from .plot_tools import get_scatter_plot_markup


def get_pageview_plot_data(reduction_type, transform=None):
    all_pageviews = WikiPageviews.objects.all()
    all_values = list(all_pageviews.values_list("term__name", "count", "per_yearday"))

    ret = dict()
    ret["name"] = [t[0] for t in all_values]
    ret["total"] = [t[1] for t in all_values]

    view_data = np.zeros((len(all_values), 366))
    for y, datatup in enumerate(all_values):
        views = [int(i) for i in datatup[2].split(",")]
        if transform:
            views = transform(views)
        for i in range(366):
            view_data[y][i] = views[i]

    from sklearn.decomposition import PCA, KernelPCA, FactorAnalysis, FastICA, LatentDirichletAllocation, NMF, IncrementalPCA
    from sklearn.manifold import TSNE

    XY = None
    if reduction_type == "pca":
        reducer = KernelPCA(n_components=2, kernel="poly", eigen_solver="arpack", degree=0.01, random_state=42)

    elif reduction_type == "tsne":
        reducer = PCA(n_components=50, svd_solver='full')
        XY = reducer.fit(view_data).transform(view_data)
        reducer2 = TSNE(n_components=2, random_state=42, n_iter=1000, verbose=2)
        XY = reducer2.fit_transform(XY)

    else:
        raise ValueError("Unknown reduction_type '%s'" % reduction_type)

    if XY is None:
        XY = reducer.fit(view_data).transform(view_data)

    ret["x"] = [x[0] for x in XY]
    ret["y"] = [x[1] for x in XY]
    return ret


def correlation_plot_view(request):
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
    transform_name = request.GET.get("transform", "")
    reduction_type = request.GET.get("reduction", "tsne")

    transform = None
    if transform_name:
        trans = sorted(TRANSFORMS, key=lambda x: x[0] == transform_name)[-1]
        transform = trans[2]

    plot_data = get_pageview_plot_data(reduction_type, transform)

    plot_markup = get_scatter_plot_markup(
        plot_data,
        title="Wiki articles grouped by views 2016",
        width=800, height=600,
        #box_select_code=jscode,
    )

    ctx = {
        "content": plot_markup,
    }
    return render(request, "wikiviews/base.html", ctx)