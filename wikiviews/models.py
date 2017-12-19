# coding=utf-8
from __future__ import unicode_literals

import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.validators import validate_comma_separated_integer_list
from picklefield import PickledObjectField


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

    def views_decorator(self, transform=None):
        import numpy as np
        views = self.views_per_day()
        if transform is not None:
            views = transform(views)
        NUM_DAYS = 3 if len(views) > 180 else 1
        views_av = [0] * ((len(views)+NUM_DAYS-1) // NUM_DAYS)
        for i, v in enumerate(views):
            views_av[i//NUM_DAYS] += v
        min_views, max_views = min(views_av), max(views_av)
        if min_views > 0:
            min_views = min_views * 2 // 3
        max_views = max(min_views+1, max_views)
        html = '<div class="histogram">'
        start_ord = datetime.date(self.year, 1, 1).toordinal()
        for i, v in enumerate(views_av):
            title = "%s views between %s and %s" % (
                v,
                datetime.date.fromordinal(start_ord + i*NUM_DAYS),
                datetime.date.fromordinal(start_ord + (i+1)*NUM_DAYS-1),
            )
            html += '<span class="histogram-bin" title="%s">' % title
            html += '<span class="histogram-value" style="height: %s%%;">' % round(
                        100. - (float(v) - min_views) / (max_views - min_views) * 100., 1)
            html += '</span></span>'
        html += '</div>'
        return html
    views_decorator.short_description = _("views")
    views_decorator.allow_tags = True


class PickleCache(models.Model):
    """Cache for picklable data"""

    id = models.CharField(max_length=100, verbose_name=_("id"), unique=True, primary_key=True)
    created = models.DateTimeField(verbose_name=_("created on"), auto_now=True)
    data = PickledObjectField(verbose_name=_("headers"), default=None, blank=True, null=True)

    @classmethod
    def clear(cls, id):
        qset = cls.objects.filter(id=id)
        if qset.exists():
            qset.delete()
            return True
        return False

    @classmethod
    def clear_like(cls, id):
        qset = cls.objects.filter(id__icontains=id)
        if qset.exists():
            qset.delete()
            return True
        return False

    @classmethod
    def store(cls, id, data):
        try:
            o = cls.objects.get(id=id)
            o.created = datetime.datetime.now()
            o.data = data
            o.save()
        except cls.DoesNotExist:
            cls.objects.create(
                id=id,
                data=data
            )

    @classmethod
    def restore(cls, id):
        try:
            o = cls.objects.get(id=id)
            return o.data
        except cls.DoesNotExist:
            return None
