# -*- coding: utf-8 -*-
# DDtoFeedCrawler
# Project by https://github.com/rix1337

from datetime import datetime

from feedcrawler import internal
from feedcrawler.config import CrawlerConfig
from feedcrawler.db import FeedDb, ListDb
from feedcrawler.external_sites.shared.internal_feed import dd_rss_feed_to_feedparser_dict, check_hoster
from feedcrawler.myjd import myjd_download
from feedcrawler.notifiers import notify
from feedcrawler.url import get_url


class DD:
    _SITE = 'DD'

    def __init__(self, filename):
        self.url = ''
        dd = CrawlerConfig('Hostnames').get('dd')
        if dd:
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
        if not self.url:
            internal.logger.debug("Kein Hostname gesetzt. Stoppe Suche für Episoden! (" + self.filename + ")")
            return
        else:
            for feed_id in self.feed_ids:
                feed_url = self.url + '/rss/' + feed_id
                feed = dd_rss_feed_to_feedparser_dict(get_url(feed_url))
                for post in feed.entries:
                    current_epoch = datetime.utcnow().timestamp()
                    published_epoch = datetime.strptime(post.published, '%a, %d %b %Y %X %Z').timestamp()
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
                                log_entry = '[Episode/Englisch] - ' + post.title + ' - [' + self._SITE + '] - ' + post.size + ' - ' + post.source
                                internal.logger.info(log_entry)
                                notify([{"text": log_entry, 'imdb_id': post.imdb_id}])
                    else:
                        internal.logger.debug(
                            post.title + " - Releases, die weniger als 30 Minuten alt sind, werden ignoriert (da Links noch hochgeladen werden).")
