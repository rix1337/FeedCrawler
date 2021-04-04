# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337

import feedcrawler.sites.shared.content_shows as shared_shows
from feedcrawler.config import RssConfig
from feedcrawler.db import FeedDb
from feedcrawler.sites.shared.internal_feed import dw_parse_download
from feedcrawler.sites.shared.internal_feed import dw_to_feedparser_dict


class DWs:
    _INTERNAL_NAME = 'DWs'
    _SITE = 'DW'

    def __init__(self, configfile, dbfile, device, logging, scraper, filename):
        self.configfile = configfile
        self.dbfile = dbfile
        self.device = device

        self.hostnames = RssConfig('Hostnames', self.configfile)
        self.url = self.hostnames.get('dw')

        self.filename = filename
        if "MB_Staffeln" in self.filename:
            self.config = RssConfig("MB", self.configfile)
        else:
            self.config = RssConfig("SJ", self.configfile)
        self.rsscrawler = RssConfig("FeedCrawler", self.configfile)
        self.hevc_retail = self.config.get("hevc_retail")
        self.retail_only = self.config.get("retail_only")
        self.hoster_fallback = self.config.get("hoster_fallback")
        self.hosters = RssConfig("Hosters", configfile).get_section()
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.scraper = scraper
        self.db = FeedDb(self.dbfile, 'feedcrawler')
        self.quality = self.config.get("quality")
        self.prefer_dw_mirror = self.rsscrawler.get("prefer_dw_mirror")
        self.cdc = FeedDb(self.dbfile, 'cdc')
        self.last_set = self.cdc.retrieve(self._INTERNAL_NAME + "Set-" + self.filename)
        self.last_sha = self.cdc.retrieve(self._INTERNAL_NAME + "-" + self.filename)
        self.headers = {'If-Modified-Since': str(self.cdc.retrieve(self._INTERNAL_NAME + "Headers-" + self.filename))}
        self.settings_array = ["quality", "rejectlist", "regex", "hevc_retail", "retail_only", "hoster_fallback"]
        self.settings = []
        self.settings.append(self.rsscrawler.get("english"))
        self.settings.append(self.rsscrawler.get("surround"))
        self.settings.append(self.rsscrawler.get("prefer_dw_mirror"))
        self.settings.append(self.hosters)
        for s in self.settings_array:
            self.settings.append(self.config.get(s))

        self.mediatype = "Serien"
        self.listtype = ""

        self.empty_list = False
        if self.filename == 'SJ_Staffeln_Regex':
            self.listtype = " (Staffeln/RegEx)"
        elif self.filename == 'MB_Staffeln':
            self.seasonssource = self.config.get('seasonssource').lower()
            self.listtype = " (Staffeln)"
        elif self.filename == 'SJ_Serien_Regex':
            self.listtype = " (RegEx)"
        list_content = shared_shows.get_series_list(self)
        if list_content:
            self.pattern = r'^(' + "|".join(list_content).lower() + ')'
        else:
            self.empty_list = True

        self.day = 0

        self.get_feed_method = dw_to_feedparser_dict
        self.parse_download_method = dw_parse_download

    def periodical_task(self):
        self.device = shared_shows.periodical_task(self)
        return self.device
