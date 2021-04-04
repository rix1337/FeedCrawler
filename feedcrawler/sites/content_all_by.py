# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337

import feedcrawler.sites.shared.content_all as shared_blogs
from feedcrawler.config import RssConfig
from feedcrawler.db import RssDb
from feedcrawler.myjd import myjd_download
from feedcrawler.sites.shared.internal_feed import by_feed_enricher
from feedcrawler.sites.shared.internal_feed import by_get_download_links
from feedcrawler.url import get_url
from feedcrawler.url import get_url_headers


class BL:
    _INTERNAL_NAME = 'MB'
    _SITE = 'BY'
    SUBSTITUTE = r"[&#\s/]"

    def __init__(self, configfile, dbfile, device, logging, scraper, filename):
        self.configfile = configfile
        self.dbfile = dbfile
        self.device = device

        self.hostnames = RssConfig('Hostnames', self.configfile)
        self.url = self.hostnames.get('by')
        self.password = self.url.split('.')[0]

        if "MB_Staffeln" not in filename:
            self.URL = 'https://' + self.url + "/?cat=1"
        else:
            self.URL = 'https://' + self.url + "/?cat=2"
        self.FEED_URLS = [self.URL]

        self.config = RssConfig(self._INTERNAL_NAME, self.configfile)
        self.rsscrawler = RssConfig("FeedCrawler", self.configfile)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.scraper = scraper
        self.filename = filename
        self.pattern = False
        self.db = RssDb(self.dbfile, 'feedcrawler')
        self.hevc_retail = self.config.get("hevc_retail")
        self.retail_only = self.config.get("retail_only")
        self.hosters = RssConfig("Hosters", configfile).get_section()
        self.hoster_fallback = self.config.get("hoster_fallback")
        self.prefer_dw_mirror = self.rsscrawler.get("prefer_dw_mirror")

        search = int(RssConfig(self._INTERNAL_NAME, self.configfile).get("search"))
        i = 2
        while i <= search:
            page_url = self.URL + "&start=" + str(i)
            if page_url not in self.FEED_URLS:
                self.FEED_URLS.append(page_url)
            i += 1
        self.cdc = RssDb(self.dbfile, 'cdc')

        self.last_set_all = self.cdc.retrieve("ALLSet-" + self.filename)
        self.headers = {'If-Modified-Since': str(self.cdc.retrieve(self._SITE + "Headers-" + self.filename))}

        self.last_sha = self.cdc.retrieve(self._SITE + "-" + self.filename)
        settings = ["quality", "search", "ignore", "regex", "cutoff", "enforcedl", "crawlseasons", "seasonsquality",
                    "seasonpacks", "seasonssource", "imdbyear", "imdb", "hevc_retail", "retail_only", "hoster_fallback"]
        self.settings = []
        self.settings.append(self.rsscrawler.get("english"))
        self.settings.append(self.rsscrawler.get("surround"))
        self.settings.append(self.rsscrawler.get("prefer_dw_mirror"))
        self.settings.append(self.hosters)
        for s in settings:
            self.settings.append(self.config.get(s))
        self.search_imdb_done = False
        self.search_regular_done = False
        self.dl_unsatisfied = False

        self.get_feed_method = by_feed_enricher
        self.get_url_method = get_url
        self.get_url_headers_method = get_url_headers
        self.get_download_links_method = by_get_download_links
        self.download_method = myjd_download

        try:
            self.imdb = float(self.config.get('imdb'))
        except:
            self.imdb = 0.0

    def periodical_task(self):
        self.device = shared_blogs.periodical_task(self)
        return self.device
