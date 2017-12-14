from django.contrib import admin

from .models import *


class WikiTermAdmin(admin.ModelAdmin):
    list_display = (
        "name", "url", "description"
    )

admin.site.register(WikiTerm, WikiTermAdmin)


class WikiPageviewsAdmin(admin.ModelAdmin):
    list_display = (
        "term",
        "count",
        "views_decorator",
    )
    search_fields = (
        "term__name",
    )

admin.site.register(WikiPageviews, WikiPageviewsAdmin)