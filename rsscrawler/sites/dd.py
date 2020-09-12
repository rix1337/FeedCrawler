# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import re
from datetime import datetime
from time import time

import feedparser
from dateutil import parser

from rsscrawler.common import check_hoster
from rsscrawler.config import RssConfig
from rsscrawler.db import RssDb
from rsscrawler.myjd import myjd_download
from rsscrawler.notifiers import notify
from rsscrawler.url import get_url


class DD:
    _INTERNAL_NAME = 'DD'

    def __init__(self, configfile, dbfile, device, logging, scraper):
        self.configfile = configfile
        self.dbfile = dbfile
        self.device = device
        self.config = RssConfig(self._INTERNAL_NAME, self.configfile)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.scraper = scraper
        self.db = RssDb(self.dbfile, 'rsscrawler')

    def periodical_task(self):
        feeds = self.config.get("feeds")
        if feeds:
            added_items = []
            feeds = feeds.replace(" ", "").split(',')
            for feed in feeds:
                feed = feedparser.parse(get_url(feed, self.configfile, self.dbfile, self.scraper))
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
                            if check_hoster(link, self.configfile):
                                links.append(str(link))
                        if self.config.get("hoster_fallback") and not links:
                            for link in unicode_links:
                                links.append(str(link))
                        storage = self.db.retrieve_all(key)
                        if not links:
                            if 'added' not in storage and 'notdl' not in storage:
                                wrong_hoster = '[DD/Hoster fehlt] - ' + key
                                if 'wrong_hoster' not in storage:
                                    self.log_info(wrong_hoster)
                                    self.db.store(key, 'wrong_hoster')
                                    notify([wrong_hoster], self.configfile)
                                else:
                                    self.log_debug(wrong_hoster)
                        elif 'added' in storage:
                            self.log_debug(
                                "%s - Release ignoriert (bereits gefunden)" % key)
                        else:
                            self.device = myjd_download(self.configfile, self.dbfile, self.device, key, "RSScrawler",
                                                        links, "")
                            if self.device:
                                self.db.store(
                                    key,
                                    'added'
                                )
                                log_entry = '[Englisch] - ' + key + ' - [DD]'
                                self.log_info(log_entry)
                                notify([log_entry], self.configfile)
                                added_items.append(log_entry)
                    else:
                        self.log_debug(
                            "%s - Releasezeitpunkt weniger als 30 Minuten in der Vergangenheit - wird ignoriert." % key)
        else:
            self.log_debug("Liste ist leer. Stoppe Suche für DD!")
        return self.device
