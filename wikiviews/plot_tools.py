# -*- coding: UTF-8 -*-
from __future__ import unicode_literals
import datetime, math

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, BoxSelectTool, CustomJS
from bokeh.embed import components
from bokeh.models import NumeralTickFormatter
from bokeh.models.formatters import DatetimeTickFormatter

from django.utils.translation import ugettext_lazy as _


def get_datetime_formatter():
    return DatetimeTickFormatter(
        hours=["%Y-%m-%d %H:%M"],
        days=["%Y-%m-%d"],
        months=["%Y/%m"],
        years=["%Y"],
    )



def get_scatter_plot_markup(data, width=400, height=400, title=None,
                            box_select_code=None):
    """`data` is a mapping and must contain at least `x` and `y` arrays"""
    DRAW_PARAMS = ("x", "y", "color", "size")

    source = ColumnDataSource(data=data)

    tooltips = []
    for key in data:
        if key not in DRAW_PARAMS:
            tooltips.append((key, "@%s" % key))

    tools = ["pan", "wheel_zoom", "reset", "save"]
    tools.append(HoverTool(tooltips=tooltips))
    if box_select_code is not None:
        tools.append("box_select")
        #tools.append(BoxSelectTool(callback=box_select_callback))
        source.callback = CustomJS(args={"source": source}, code=box_select_code)

    plot = figure(
        width=width, height=height,
        tools=tools,
        title=title,
    )

    params = dict(source=source)
    for key in DRAW_PARAMS:
        if key in data:
            params[key] = key
    plot.scatter(**params)

    return "\n".join(components(plot))