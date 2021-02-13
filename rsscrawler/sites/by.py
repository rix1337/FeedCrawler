# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import feedparser
import hashlib

import rsscrawler.shared_blogs as shared_blogs
from rsscrawler.config import RssConfig
from rsscrawler.db import RssDb
from rsscrawler.url import get_url
from rsscrawler.url import get_url_headers


class BL:
    _INTERNAL_NAME = 'MB'
    SUBSTITUTE = r"[&#\s/]"

    def __init__(self, configfile, dbfile, device, logging, scraper, filename):
        self.configfile = configfile
        self.dbfile = dbfile
        self.device = device

        self.hostnames = RssConfig('Hostnames', self.configfile)
        self.url = self.hostnames.get('by')

        self.URL = 'https://' + self.url + '/feed/'
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
            page_url = self.URL + "?paged=" + str(i)
            if page_url not in self.FEED_URLS:
                self.FEED_URLS.append(page_url)
            i += 1

        self.cdc = RssDb(self.dbfile, 'cdc')

        self.last_set_all = self.cdc.retrieve("ALLSet-" + self.filename)
        self.headers_by = {'If-Modified-Since': str(self.cdc.retrieve("BYHeaders-" + self.filename))}

        self.last_sha_by = self.cdc.retrieve("BY-" + self.filename)
        settings = ["quality", "search", "ignore", "regex", "cutoff", "crawl3d", "crawl3dtype", "enforcedl",
                    "crawlseasons", "seasonsquality", "seasonpacks", "seasonssource", "imdbyear", "imdb",
                    "hevc_retail", "retail_only", "hoster_fallback"]
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
        imdb = self.imdb
        urls = []

        if self.filename == 'MB_Staffeln':
            if not self.config.get('crawlseasons'):
                return self.device
            liste = shared_blogs.get_movies_list(self, self.filename)
            if liste:
                self.pattern = r'(' + "|".join(liste).lower() + ').*'
        elif self.filename == 'MB_Regex':
            if not self.config.get('regex'):
                self.log_debug(
                    "Regex deaktiviert. Stoppe Suche für Filme! (" + self.filename + ")")
                return self.device
            liste = shared_blogs.get_movies_list(self, self.filename)
            if liste:
                self.pattern = r'(' + "|".join(liste).lower() + ').*'
        elif self.filename == "IMDB":
            self.pattern = self.filename
        else:
            if self.filename == 'MB_3D':
                if not self.config.get('crawl3d'):
                    self.log_debug(
                        "3D-Suche deaktiviert. Stoppe Suche für Filme! (" + self.filename + ")")
                    return self.device
            liste = shared_blogs.get_movies_list(self, self.filename)
            if liste:
                self.pattern = r'(' + "|".join(liste).lower() + ').*'

        if self.url:
            for URL in self.FEED_URLS:
                urls.append(URL)

        if not self.pattern:
            self.log_debug(
                "Liste ist leer. Stoppe Suche für Filme! (" + self.filename + ")")
            return self.device

        if self.filename == 'IMDB' and imdb == 0:
            self.log_debug(
                "IMDB-Suchwert ist 0. Stoppe Suche für Filme! (" + self.filename + ")")
            return self.device

        loading_304 = False
        try:
            first_page_raw = get_url_headers(urls[0], self.configfile, self.dbfile, self.headers_by, self.scraper)
            self.scraper = first_page_raw[1]
            first_page_raw = first_page_raw[0]
            first_page_content = feedparser.parse(first_page_raw.content)
            if first_page_raw.status_code == 304:
                loading_304 = True
        except:
            loading_304 = True
            first_page_content = False
            self.log_debug("Fehler beim Abruf von BY - breche BY-Suche ab!")

        set_all = shared_blogs.settings_hash(self, False)

        if self.last_set_all == set_all:
            if loading_304:
                urls = []
                self.log_debug("BY-Feed seit letztem Aufruf nicht aktualisiert - breche BY-Suche ab!")

        sha = None

        if self.filename != 'IMDB':
            if not loading_304 and first_page_content:
                for i in first_page_content.entries:
                    concat_by = i.title + i.published + str(self.settings) + str(self.pattern)
                    sha = hashlib.sha256(concat_by.encode('ascii', 'ignore')).hexdigest()
                    break
        else:
            if not loading_304 and first_page_content:
                for i in first_page_content.entries:
                    concat_by = i.title + i.published + str(self.settings) + str(self.imdb)
                    sha = hashlib.sha256(concat_by.encode('ascii', 'ignore')).hexdigest()
                    break

        added_items = []
        if self.filename == "IMDB":
            if imdb > 0:
                i = 0
                for url in urls:
                    if not self.search_imdb_done:
                        if i == 0 and first_page_content:
                            by_parsed_url = first_page_content
                        else:
                            by_parsed_url = feedparser.parse(
                                get_url(url, self.configfile, self.dbfile, self.scraper))
                        found = shared_blogs.search_imdb(self, imdb, by_parsed_url, "BY")
                        if found:
                            for f in found:
                                added_items.append(f)
                        i += 1
        else:
            i = 0
            for url in urls:
                if not self.search_regular_done:
                    if i == 0 and first_page_content:
                        by_parsed_url = first_page_content
                    else:
                        by_parsed_url = feedparser.parse(
                            get_url(url, self.configfile, self.dbfile, self.scraper))
                    found = shared_blogs.search_feed(self, by_parsed_url, "BY")
                    if found:
                        for f in found:
                            added_items.append(f)
                    i += 1
            i = 0

        settings_changed = False
        if set_all:
            new_set_all = shared_blogs.settings_hash(self, True)
            if set_all == new_set_all:
                self.cdc.delete("ALLSet-" + self.filename)
                self.cdc.store("ALLSet-" + self.filename, new_set_all)
            else:
                settings_changed = True
        if sha:
            if not self.dl_unsatisfied and not settings_changed:
                self.cdc.delete("BY-" + self.filename)
                self.cdc.store("BY-" + self.filename, sha)
            else:
                self.log_debug(
                    "Für ein oder mehrere Release(s) wurde kein zweisprachiges gefunden. Setze kein neues BY-CDC!")
        if not loading_304:
            try:
                header = first_page_raw.headers['Last-Modified']
            except KeyError:
                header = False
            if header:
                self.cdc.delete("BYHeaders-" + self.filename)
                self.cdc.store("BYHeaders-" + self.filename, header)

        return self.device
