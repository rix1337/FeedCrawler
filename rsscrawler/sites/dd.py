# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import re
from datetime import datetime
from time import time

import feedparser
from dateutil import parser

from rsscrawler.myjd import myjd_download
from rsscrawler.notifiers import notify
from rsscrawler.rssconfig import RssConfig
from rsscrawler.rssdb import RssDb
from rsscrawler.url import get_url


class DD:
    _INTERNAL_NAME = 'DD'

    def __init__(self, configfile, dbfile, device, logging):
        self.configfile = configfile
        self.dbfile = dbfile
        self.device = device
        self.config = RssConfig(self._INTERNAL_NAME, self.configfile)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.db = RssDb(self.dbfile, 'rsscrawler')

    def periodical_task(self):
        feeds = self.config.get("feeds")
        if feeds:
            added_items = []
            feeds = feeds.replace(" ", "").split(',')
            hoster = re.compile(self.config.get("hoster"))
            for feed in feeds:
                feed = feedparser.parse(get_url(feed, self.configfile, self.dbfile))
                for post in feed.entries:
                    key = post.title.replace(" ", ".")

                    epoch = datetime(1970, 1, 1)
                    current_epoch = int(time())
                    published_format = "%Y-%m-%d %H:%M:%S+00:00"
                    published_timestamp = str(parser.parse(post.published))
                    published_epoch = int((datetime.strptime(
                        published_timestamp, published_format) - epoch).total_seconds())
                    if (current_epoch - 1800) > published_epoch:
                        link_pool = post.summary
                        unicode_links = re.findall(r'(http.*)', link_pool)
                        links = []
                        for link in unicode_links:
                            if re.match(hoster, link):
                                links.append(str(link))
                        if not links:
                            self.log_debug(
                                "%s - Release ignoriert (kein passender Link gefunden)" % key)
                        elif self.db.retrieve(key) == 'added':
                            self.log_debug(
                                "%s - Release ignoriert (bereits gefunden)" % key)
                        else:
                            self.device = myjd_download(self.configfile, self.device, key, "RSScrawler", links, "")
                            if self.device:
                                self.db.store(
                                    key,
                                    'added'
                                )
                                log_entry = '[DD] - Englisch - ' + key
                                self.log_info(log_entry)
                                notify([log_entry], self.configfile)
                                added_items.append(log_entry)
                    else:
                        self.log_debug(
                            "%s - Releasezeitpunkt weniger als 30 Minuten in der Vergangenheit - wird ignoriert." % key)
        return self.device
