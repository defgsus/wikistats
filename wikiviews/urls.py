
from django.conf.urls import url, include
from . import views, views_plot

app_name="wikiviews"
urlpatterns = [
    url(r'^corr/?',                 views.correlation_view,     name="correlation"),
    url(r'^plot/?',                 views_plot.correlation_plot_view, name="correlation_plot"),

    url(r'^autocomplete/?',         views.autocomplete_json,    name="autocomplete"),
]
