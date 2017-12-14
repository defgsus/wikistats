
from django.conf.urls import url, include
from . import views

app_name="wikiviews"
urlpatterns = [
    url(r'^corr/?',                 views.correlation_view,     name="correlation"),
    url(r'^autocomplete/?',         views.autocomplete_json,    name="autocomplete"),
]
