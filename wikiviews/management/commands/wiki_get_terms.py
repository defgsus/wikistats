# encoding=utf-8
from __future__ import unicode_literals, print_function

import datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext_lazy as _

from tools.opensearch import opensearch_and_store
from wikiviews.models import *


class Command(BaseCommand):
    help = _('Get Wiki opeansearch results for term')

    def add_arguments(self, parser):
        parser.add_argument('term', type=str, nargs='?')
        parser.add_argument('-limit', type=int, nargs="?", default=100)

    def handle(self, *args, **options):
        starttime = datetime.datetime.now()

        if options["term"] is None:
            for i in range(ord('a'), ord('z') + 1):
                print(chr(i))
                opensearch_and_store(chr(i), options["limit"])
        else:
            opensearch_and_store(options["term"], options["limit"])

        endtime = datetime.datetime.now()
        print("TOOK %s" % (endtime - starttime))

