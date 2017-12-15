# coding=utf-8
from __future__ import unicode_literals

import json
import requests

from .credentials import CONTACT_EMAIL


def opensearch(term, limit=10):
    url = "https://de.wikipedia.org/w/api.php"
    res = requests.get(
        url,
        headers={"User-Agent": CONTACT_EMAIL},
        params={
            "action": "opensearch",
            "format": "json",
            "limit": limit,
            "search": term,
        }
    )
    data = json.loads(res.content)
    return [{
        "name": data[1][i],
        "desc": data[2][i],
        "url": data[3][i],
    } for i in range(len(data[1]))]


def opensearch_and_store(term, limit=10):
    from django.db import transaction
    from wikiviews.models import WikiTerm
    res = opensearch(term, limit=limit)
    with transaction.atomic():
        for term in res:
            WikiTerm.objects.get_or_create(
                name=term["name"][:128],
                description=term["desc"],
                url=term["url"],
            )
    return res


if __name__ == "__main__":
    res = opensearch("Romantik")
    print(res)



