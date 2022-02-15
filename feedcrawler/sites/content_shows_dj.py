# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt content_all alle benötigten Parameter für die Feed-Suche auf DJ bereit.

import feedcrawler.sites.shared.content_shows as shared_shows
from feedcrawler.config import CrawlerConfig
from feedcrawler.db import FeedDb
from feedcrawler.sites.shared.internal_feed import j_parse_download
from feedcrawler.sites.shared.internal_feed import j_releases_to_feedparser_dict


class DJ:
    _INTERNAL_NAME = 'DJ'
    _SITE = 'DJ'

    def __init__(self, filename):
        self.hostnames = CrawlerConfig('Hostnames')
        self.url = self.hostnames.get('dj')

        self.config = CrawlerConfig("CustomDJ")
        self.feedcrawler = CrawlerConfig("FeedCrawler")
        self.hosters = CrawlerConfig("Hosters").get_section()
        self.hoster_fallback = self.config.get("hoster_fallback")
        self.filename = filename
        self.db = FeedDb('FeedCrawler')
        self.quality = self.config.get("quality")
        self.cdc = FeedDb('cdc')
        self.last_set = self.cdc.retrieve(self._INTERNAL_NAME + "Set-" + self.filename)
        self.last_sha = self.cdc.retrieve(self._INTERNAL_NAME + "-" + self.filename)
        self.headers = {'If-Modified-Since': str(self.cdc.retrieve(self._INTERNAL_NAME + "Headers-" + self.filename))}
        self.settings_array = ["quality", "rejectlist", "regex", "hoster_fallback"]
        self.settings = []
        self.settings.append(self.feedcrawler.get("english"))
        self.settings.append(self.feedcrawler.get("surround"))
        self.settings.append(self.hosters)
        for s in self.settings_array:
            self.settings.append(self.config.get(s))

        self.retail_only = False
        self.hevc_retail = False

        self.mediatype = "Dokus"
        self.listtype = ""

        self.empty_list = False
        if self.filename == 'List_CustomDJ_Documentaries_Regex':
            self.listtype = " (RegEx)"
        list_content = shared_shows.get_series_list(self)
        if list_content:
            self.pattern = r'^(' + "|".join(list_content).lower() + ')'
        else:
            self.empty_list = True

        self.day = 0
        self.max_days = 8

        self.get_feed_method = j_releases_to_feedparser_dict
        self.parse_download_method = j_parse_download

    def periodical_task(self):
        shared_shows.periodical_task(self)
