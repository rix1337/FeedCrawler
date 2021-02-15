# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import rsscrawler.sites.shared.content_all as shared_blogs
from rsscrawler.config import RssConfig
from rsscrawler.db import RssDb
from rsscrawler.sites.shared.fake_feed import ww_feed_enricher
from rsscrawler.sites.shared.fake_feed import ww_post_url_headers


class BL:
    _INTERNAL_NAME = 'MB'
    _SITE = 'WW'
    SUBSTITUTE = r"[&#\s/]"

    def __init__(self, configfile, dbfile, device, logging, scraper, filename):
        self.configfile = configfile
        self.dbfile = dbfile
        self.device = device

        self.hostnames = RssConfig('Hostnames', self.configfile)
        self.url = self.hostnames.get('ww')
        self.password = self.url.split('.')[0]

        if "MB_Staffeln" not in filename:
            self.URL = 'https://' + self.url + "/ajax" + "|/cat/movies|p=1&t=c&q=5"
        else:
            self.URL = 'https://' + self.url + "/ajax" + "|/cat/series|p=1&t=c&q=9"
        self.FEED_URLS = [self.URL]

        self.config = RssConfig(self._INTERNAL_NAME, self.configfile)
        self.rsscrawler = RssConfig("RSScrawler", self.configfile)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.scraper = scraper
        self.filename = filename
        self.pattern = False
        self.db = RssDb(self.dbfile, 'rsscrawler')
        self.hevc_retail = self.config.get("hevc_retail")
        self.retail_only = self.config.get("retail_only")
        self.hosters = RssConfig("Hosters", configfile).get_section()
        self.hoster_fallback = self.config.get("hoster_fallback")

        search = int(RssConfig(self._INTERNAL_NAME, self.configfile).get("search"))
        i = 2
        while i <= search:
            if "MB_Staffeln" not in filename:
                page_url = self.URL.replace("|p=1", "|p=" + str(i))
                if page_url not in self.FEED_URLS:
                    self.FEED_URLS.append(page_url)
                i += 1
            else:
                page_url = self.URL.replace("|p=1", "|p=" + str(i))
                if page_url not in self.FEED_URLS:
                    self.FEED_URLS.append(page_url)
                i += 1
        self.cdc = RssDb(self.dbfile, 'cdc')

        self.last_set_all = self.cdc.retrieve("ALLSet-" + self.filename)
        self.headers = {'If-Modified-Since': str(self.cdc.retrieve(self._SITE + "Headers-" + self.filename))}

        self.last_sha_by = self.cdc.retrieve(self._SITE + "-" + self.filename)
        settings = ["quality", "search", "ignore", "regex", "cutoff", "enforcedl", "crawlseasons", "seasonsquality",
                    "seasonpacks", "seasonssource", "imdbyear", "imdb", "hevc_retail", "retail_only", "hoster_fallback"]
        self.settings = []
        self.settings.append(self.rsscrawler.get("english"))
        self.settings.append(self.rsscrawler.get("surround"))
        self.settings.append(self.hosters)
        for s in settings:
            self.settings.append(self.config.get(s))
        self.search_imdb_done = False
        self.search_regular_done = False
        self.dl_unsatisfied = False

        try:
            self.imdb = float(self.config.get('imdb'))
        except:
            self.imdb = 0.0

    def periodical_task(self):
        self.device = shared_blogs.periodical_task(self, ww_feed_enricher, ww_post_url_headers, ww_post_url_headers)
        return self.device
