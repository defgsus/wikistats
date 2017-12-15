# coding=utf-8
from __future__ import unicode_literals

import json
import datetime
import requests

from .credentials import CONTACT_EMAIL

def get_pageviews_daily(year, article,
                        project="de.wikipedia.org", access="all-access", agent="user"):
    url = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/" \
          "%s/%s/%s/%s/daily/%s/%s" % (project, access, agent, article, "%s0101" % year, "%s1231" % year)

    ret = [0] * 366
    res = requests.get(url, headers={"User-Agent": CONTACT_EMAIL})
    data = json.loads(res.content)
    start_o = datetime.date(year, 1, 1).toordinal()
    if "items" in data:
        for item in data["items"]:
            date = datetime.datetime.strptime(item["timestamp"], "%Y%m%d00")
            o = date.date().toordinal() - start_o
            views = item["views"]
            ret[o] = views
    return ret


def get_pageviews_and_store(year, wikiterm,
                            project="de.wikipedia.org", access="all-access", agent="user"):
    from wikiviews.models import WikiPageviews
    views = get_pageviews_daily(year, wikiterm, project=project, access=access, agent=agent)
    WikiPageviews.objects.create(
        term=wikiterm,
        year=year,
        project=project,
        agent=agent,
        access=access,
        count=sum(views),
        per_yearday=",".join("%s" % v for v in views),
    )
    return views



if __name__ == "__main__":
    res = get_pageviews_daily(2016, "Romantik")
    print(res)
