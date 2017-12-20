# encoding=utf-8
from __future__ import unicode_literals, print_function

import datetime
import time

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from tools.pageviews import get_pageviews_daily
from wikiviews.views_plot import get_pageview_plot_data_cached


class Command(BaseCommand):
    help = _('Precalc Wiki plot data')

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        starttime = datetime.datetime.now()

        get_pageview_plot_data_cached("tsne", "weekday", "corr", clear_cache=True)

        endtime = datetime.datetime.now()
        print("TOOK %s" % (endtime - starttime))
