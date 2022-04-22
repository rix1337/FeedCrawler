# -*- coding: utf-8 -*-
# DDtoFeedCrawler
# Project by https://github.com/rix1337

import time
from datetime import datetime

import requests

from feedcrawler import internal
from feedcrawler.config import CrawlerConfig
from feedcrawler.db import FeedDb, ListDb
from feedcrawler.myjd import myjd_download
from feedcrawler.sites.shared.internal_feed import dd_rss_feed_to_feedparser_dict, check_hoster


class DD:
    _SITE = 'DD'

    def __init__(self, filename):
        self.url = 'https://' + CrawlerConfig('Hostnames').get('dd')
        self.db = FeedDb('FeedCrawler')
        self.filename = filename
        self.empty_list = False
        self.feed_ids = self.get_feed_id_list()
        self.hoster_fallback = CrawlerConfig("CustomDD").get("hoster_fallback")

    def get_feed_id_list(self):
        cont = ListDb(self.filename).retrieve()
        titles = []
        if cont:
            for title in cont:
                if title:
                    title = title.replace(" ", ".")
                    titles.append(title)
        return titles

    def periodical_task(self):
        for feed_id in self.feed_ids:
            feed_url = self.url + '/rss/' + feed_id
            feed = dd_rss_feed_to_feedparser_dict(requests.get(feed_url).content)
            for post in feed.entries:
                epoch = datetime(1970, 1, 1)
                current_epoch = int(time.time())
                published_format = "%Y-%m-%d %H:%M:%S+00:00"
                # ToDo change from dateutil parser to datetime.strptime
                published_timestamp = str(parser.parse(post.published))
                published_epoch = int((datetime.strptime(
                    published_timestamp, published_format) - epoch).total_seconds())
                if (current_epoch - 1800) > published_epoch:
                    links = []
                    for link in post.links:
                        if check_hoster(link):
                            links.append(link)
                    if not links and self.hoster_fallback:
                        links = post.links
                    storage = self.db.retrieve_all(post.title)
                    if not links:
                        internal.logger.debug(u"Release ignoriert - keine Links gefunden")
                    elif 'added' in storage:
                        internal.logger.debug(post.title + " - Release ignoriert (bereits gefunden)")
                    else:
                        if myjd_download(post.title, "FeedCrawler", links, self.url):
                            self.db.store(post.title, 'added')
                            log_entry = '[Episode/Englisch] - ' + post.title + ' - [' + self._SITE + ']'
                            internal.logger.info(log_entry)
                else:
                    internal.logger.debug(
                        post.title + " - Releases, die weniger als 30 Minuten alt sind, werden ignoriert (da Links noch hochgeladen werden).")
