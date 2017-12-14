# encoding=utf-8
from __future__ import unicode_literals, print_function

import datetime
import time

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from tools.pageviews import get_pageviews_daily
from wikiviews.models import *


class Command(BaseCommand):
    help = _('Get Wiki pageview data')

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        starttime = datetime.datetime.now()

        update_pageviews(2016)

        endtime = datetime.datetime.now()
        print("TOOK %s" % (endtime - starttime))


def update_pageviews(year, agent="user", project="de.wikipedia.org", access="all-access"):
    for term_pk, term_url in WikiTerm.objects.all().values_list("id", "url"):
        if not WikiPageviews.objects.filter(term=term_pk, year=year, agent=agent, project=project, access=access).exists():
            term = term_url[term_url.rfind("/")+1:]
            views = get_pageviews_daily(year, term, project=project, access=access, agent=agent)
            count = sum(views)
            print("%s: %s" % (term, count))
            WikiPageviews.objects.create(
                term=WikiTerm.objects.get(pk=term_pk),
                year=year,
                project=project,
                agent=agent,
                access=access,
                count=count,
                per_yearday=",".join("%s" % v for v in views),
            )
            time.sleep(60./100.)

