# coding=utf-8
from __future__ import unicode_literals

import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.validators import validate_comma_separated_integer_list


class WikiTerm(models.Model):

    name = models.CharField(verbose_name=_("name"), max_length=128)
    url = models.URLField(verbose_name=_("url"))
    description = models.TextField(verbose_name=_("description"))

    def __unicode__(self):
        return self.name


class WikiPageviews(models.Model):

    term = models.ForeignKey(verbose_name=_("term"), to=WikiTerm)
    year = models.IntegerField(verbose_name=_("year"))
    project = models.CharField(verbose_name=_("project/site"), max_length=30)
    agent = models.CharField(verbose_name=_("agent"), max_length=10)
    access = models.CharField(verbose_name=_("access"), max_length=10)

    count = models.IntegerField(verbose_name=_("count"))
    per_yearday = models.CharField(verbose_name=_("per year-day"), max_length=4096,
                                   validators=[validate_comma_separated_integer_list])

    def views_per_day(self):
        return [int(x) for x in self.per_yearday.split(",")]

    def views_decorator(self):
        NUM_DAYS = 3
        views = self.views_per_day()
        views_av = [0] * ((len(views)+NUM_DAYS-1) // NUM_DAYS)
        for i, v in enumerate(views):
            views_av[i//NUM_DAYS] += v
        max_views = max(views_av)
        max_views = max(1, max_views)
        html = '<div>'
        start_ord = datetime.date(self.year, 1, 1).toordinal()
        for i, v in enumerate(views_av):
            title = "%s views between %s and %s" % (
                v,
                datetime.date.fromordinal(start_ord + i*NUM_DAYS),
                datetime.date.fromordinal(start_ord + (i+1)*NUM_DAYS-1),
            )
            html += '<span style="display: inline-block; position: relative; ' \
                    'width:5px; height: 48px; margin-right: 1px; background: #79aec8;" ' \
                    'title="%s">' % title
            html += '<span style="display: block; height: %s%%; background: #eee">' % round(100. - float(v) / max_views * 100., 1)
            html += '</span></span>'
        html += '</div>'
        return html
    views_decorator.short_description = _("views")
    views_decorator.allow_tags = True