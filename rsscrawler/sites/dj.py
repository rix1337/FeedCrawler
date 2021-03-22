# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import rsscrawler.sites.shared.content_shows as shared_shows
from rsscrawler.config import RssConfig
from rsscrawler.db import RssDb
from rsscrawler.sites.shared.fake_feed import j_parse_download
from rsscrawler.sites.shared.fake_feed import j_releases_to_feedparser_dict


class DJ:
    _INTERNAL_NAME = "DJ"

    def __init__(self, configfile, dbfile, device, logging, scraper, filename):
        self.configfile = configfile
        self.dbfile = dbfile
        self.device = device

        self.hostnames = RssConfig('Hostnames', self.configfile)
        self.j = self.hostnames.get('dj')

        self.config = RssConfig(self._INTERNAL_NAME, self.configfile)
        self.rsscrawler = RssConfig("RSScrawler", self.configfile)
        self.hosters = RssConfig("Hosters", configfile).get_section()
        self.hoster_fallback = self.config.get("hoster_fallback")
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.scraper = scraper
        self.filename = filename
        self.db = RssDb(self.dbfile, 'rsscrawler')
        self.quality = self.config.get("quality")
        self.cdc = RssDb(self.dbfile, 'cdc')
        self.last_set_dj = self.cdc.retrieve("DJSet-" + self.filename)
        self.last_sha_dj = self.cdc.retrieve("DJ-" + self.filename)
        self.headers = {'If-Modified-Since': str(self.cdc.retrieve("DJHeaders-" + self.filename))}
        self.settings_array = ["quality", "rejectlist", "regex", "hoster_fallback"]
        self.settings = []
        self.settings.append(self.rsscrawler.get("english"))
        self.settings.append(self.rsscrawler.get("surround"))
        self.settings.append(self.hosters)
        for s in self.settings_array:
            self.settings.append(self.config.get(s))

        self.retail_only = False
        self.hevc_retail = False

        self.mediatype = "Dokus"
        self.listtype = ""

        self.empty_list = False
        if self.filename == 'DJ_Dokus_Regex':
            self.listtype = " (RegEx)"
        list_content = shared_shows.get_series_list(self)
        if list_content:
            self.pattern = r'^(' + "|".join(list_content).lower() + ')'
        else:
            self.empty_list = True

        self.day = 0

        self.get_feed_method = j_releases_to_feedparser_dict
        self.parse_download_method = j_parse_download

    def periodical_task(self):
        self.device = shared_shows.periodical_task(self)
        return self.device
