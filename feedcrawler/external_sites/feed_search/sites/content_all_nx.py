# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt content_all alle benötigten Parameter für die Feed-Suche auf NX bereit.

import json

import feedcrawler.external_sites.feed_search.content_all as shared_blogs
from feedcrawler.external_sites.feed_search.shared import FakeFeedParserDict
from feedcrawler.external_sites.feed_search.shared import add_decrypt_instead_of_download
from feedcrawler.external_sites.feed_search.shared import standardize_size_value
from feedcrawler.external_sites.feed_search.shared import unused_get_feed_parameter
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.sqlite_database import FeedDb
from feedcrawler.providers.url_functions import get_url, get_url_headers


class BL:
    _SITE = 'NX'
    SUBSTITUTE = r"[&#\s/]"

    def __init__(self, filename):
        self.hostnames = CrawlerConfig('Hostnames')
        self.url = self.hostnames.get('nx')
        self.password = self.url.split('.')[0]
        self.filename = filename

        if self.filename == "List_ContentAll_Seasons":
            category = "episode"
        else:
            category = "movie"

        self.URL = 'https://' + self.url + '/api/frontend/releases/category/' + category + '/tag/all/'
        self.FEED_URLS = [self.URL + '1/51?sort=date']
        self.config = CrawlerConfig("ContentAll")
        self.feedcrawler = CrawlerConfig("FeedCrawler")
        self.pattern = False
        self.db = FeedDb('FeedCrawler')
        self.hevc_retail = self.config.get("hevc_retail")
        self.retail_only = self.config.get("retail_only")
        self.hosters = CrawlerConfig("Hosters").get_section()
        self.hoster_fallback = self.config.get("hoster_fallback")

        search = int(CrawlerConfig("ContentAll").get("search"))
        i = 2
        while i <= search:
            page_url = self.URL + str(i) + '/51?sort=date'
            if page_url not in self.FEED_URLS:
                self.FEED_URLS.append(page_url)
            i += 1
        self.cdc = FeedDb('cdc')

        self.last_set_all = self.cdc.retrieve("ALLSet-" + self.filename)
        self.headers = {'If-Modified-Since': str(self.cdc.retrieve(self._SITE + "Headers-" + self.filename))}

        self.last_sha = self.cdc.retrieve(self._SITE + "-" + self.filename)
        settings = ["quality", "search", "ignore", "regex", "cutoff", "enforcedl", "crawlseasons", "seasonsquality",
                    "seasonpacks", "seasonssource", "imdbyear", "imdb", "hevc_retail", "retail_only", "hoster_fallback"]
        self.settings = []
        self.settings.append(self.feedcrawler.get("english"))
        self.settings.append(self.feedcrawler.get("surround"))
        self.settings.append(self.hosters)
        for s in settings:
            self.settings.append(self.config.get(s))
        self.search_imdb_done = False
        self.search_regular_done = False
        self.dl_unsatisfied = False

        self.get_feed_method = nx_feed_enricher
        self.get_url_method = get_url
        self.get_url_headers_method = get_url_headers
        self.get_download_links_method = nx_get_download_links
        self.download_method = add_decrypt_instead_of_download

        try:
            self.imdb = float(self.config.get('imdb'))
        except:
            self.imdb = 0.0

    def periodical_task(self):
        shared_blogs.periodical_task(self)


def nx_get_download_links(self, content, title):
    unused_get_feed_parameter(self)
    unused_get_feed_parameter(title)

    download_links = []
    try:
        source = content.split("|")[0]
        if source:
            download_links.append(source)
    except:
        return False
    return download_links


def nx_feed_enricher(feed):
    feed = json.loads(feed)
    nx = CrawlerConfig('Hostnames').get('nx')
    entries = []
    items = feed['result']['list']

    for item in items:
        try:
            try:
                source = "https://" + nx + "/release/" + item['slug']
            except:
                source = ""

            title = item['name']
            if title:
                try:
                    imdb_id = item['_media']['imdbid']
                except:
                    imdb_id = ""

                try:
                    size = standardize_size_value(item['size'] + item['sizeunit'])
                except:
                    size = ""

                try:
                    published = item['publishat']
                except:
                    published = ""

                entries.append(FakeFeedParserDict({
                    "title": title,
                    "published": published,
                    "content": [
                        FakeFeedParserDict({
                            "value": source + "|mkv"
                        })],
                    "source": source,
                    "size": size,
                    "imdb_id": imdb_id
                }))

        except:
            print(u"NX hat den Feed angepasst. Parsen teilweise nicht möglich!")
            continue

    feed = {"entries": entries}
    feed = FakeFeedParserDict(feed)
    return feed
