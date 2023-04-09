# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt content_all alle benötigten Parameter für die Feed-Suche auf HW bereit.

import json
import re

from bs4 import BeautifulSoup

import feedcrawler.external_sites.feed_search.content_all as shared_blogs
from feedcrawler.external_sites.feed_search.shared import FakeFeedParserDict
from feedcrawler.external_sites.feed_search.shared import add_decrypt_instead_of_download
from feedcrawler.external_sites.feed_search.shared import check_download_links
from feedcrawler.external_sites.feed_search.shared import check_release_not_sd
from feedcrawler.external_sites.feed_search.shared import standardize_size_value
from feedcrawler.external_sites.metadata.imdb import get_imdb_id_from_link
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.sqlite_database import FeedDb
from feedcrawler.providers.url_functions import get_url, get_url_headers, get_urls_async, post_url


class BL:
    _SITE = 'DW'
    SUBSTITUTE = r"[&#\s/]"

    def __init__(self, filename):
        self.hostnames = CrawlerConfig('Hostnames')
        self.url = self.hostnames.get('dw')
        self.password = self.url.split('.')[0]

        self.URL = 'https://' + self.url
        self.FEED_URLS = [self.URL + "/?s="]
        self.config = CrawlerConfig("ContentAll")
        self.feedcrawler = CrawlerConfig("FeedCrawler")
        self.filename = filename
        self.pattern = False
        self.db = FeedDb('FeedCrawler')
        self.hevc_retail = self.config.get("hevc_retail")
        self.retail_only = self.config.get("retail_only")
        self.hosters = CrawlerConfig("Hosters").get_section()
        self.hoster_fallback = self.config.get("hoster_fallback")

        search = int(CrawlerConfig("ContentAll").get("search"))
        i = 2
        while i <= search:
            page_url = self.URL + "/page/" + str(i) + "/?s"
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

        self.get_feed_method = dw_feed_enricher
        self.get_url_method = get_url
        self.get_url_headers_method = get_url_headers
        self.get_download_links_method = dw_get_download_links
        self.download_method = add_decrypt_instead_of_download

        try:
            self.imdb = float(self.config.get('imdb'))
        except:
            self.imdb = 0.0

    def periodical_task(self):
        shared_blogs.periodical_task(self)


def dw_get_download_links(self, content, title):
    try:
        try:
            content = BeautifulSoup(content, "html.parser")
        except:
            content = BeautifulSoup(str(content), "html.parser")
        download_buttons = content.findAll("button", {"class": "show_link"})
    except:
        print("DW hat die Detail-Seite angepasst. Parsen von Download-Links für " + title + " nicht möglich!")
        return False

    dw = CrawlerConfig('Hostnames').get('dw')
    ajax_url = "https://" + dw + "/wp-admin/admin-ajax.php"

    download_links = []
    try:
        for button in download_buttons:
            payload = "action=show_link&link_id=" + button["value"]
            response = json.loads(post_url(ajax_url, payload))
            if response["success"]:
                link = response["data"].split(",")[0]
                hoster = button.nextSibling.img["src"].split("/")[-1].replace(".png", "")
                download_links.append([link, hoster])
    except:
        print("DW hat die Detail-Seite angepasst. Parsen von Download-Links nicht möglich!")
        pass

    return check_download_links(self, download_links)


def dw_feed_enricher(feed):
    feed = BeautifulSoup(feed, "html.parser")
    articles = feed.findAll("article")
    entries = []

    async_results = []
    for article in articles:
        try:
            async_results.append(article.find("h4").find("a")["href"])
        except:
            pass
    async_results = get_urls_async(async_results)

    for result in async_results:
        try:
            details = BeautifulSoup(result[0], "html.parser")

            title = details.find("h1").text.strip()

            try:
                imdb_link = details.find("a", href=re.compile("imdb.com"))
                imdb_id = get_imdb_id_from_link(title, imdb_link["href"])
            except:
                imdb_id = ""

            try:
                size = standardize_size_value(details.find("strong", text=re.compile(r"(size|größe)",
                                                                                     re.IGNORECASE)).nextSibling.nextSibling.text.split(
                    "|")[-1].strip())
            except:
                size = ""

            try:
                source = result[1]
            except:
                source = ""

            try:
                published = details.find("strong", text=re.compile(r"(date|datum)",
                                                                   re.IGNORECASE)).nextSibling.nextSibling.text.strip()
            except:
                published = ""

            if title:
                entries.append(FakeFeedParserDict({
                    "title": title,
                    "published": published,
                    "content": [
                        FakeFeedParserDict({
                            "value": str(details)
                        })],
                    "source": source,
                    "size": size,
                    "imdb_id": imdb_id
                }))
        except:
            print("DW hat den Feed angepasst. Parsen teilweise nicht möglich!")
            continue

    feed = {"entries": entries}
    feed = FakeFeedParserDict(feed)
    return feed


def dw_search_results(content, resolution):
    content = BeautifulSoup(content, "html.parser")
    articles = content.findAll("article")

    async_results = []
    for article in articles:
        try:
            title = article.find("h4").find("a")["title"].replace(" ", ".").strip()
            if ".xxx." not in title.lower():
                link = article.find("h4").find("a")["href"]
                if resolution and resolution.lower() not in title.lower():
                    if "480p" in resolution:
                        if check_release_not_sd(title):
                            continue
                    else:
                        continue
                async_results.append(link)
        except:
            pass
    async_results = get_urls_async(async_results)

    results = []

    for result in async_results:
        try:
            details = BeautifulSoup(result[0], "html.parser")

            title = details.find("h1").text.strip()

            try:
                imdb_link = details.find("a", href=re.compile("imdb.com"))
                imdb_id = get_imdb_id_from_link(title, imdb_link["href"])
            except:
                imdb_id = ""

            try:
                size = standardize_size_value(details.find("strong", text=re.compile(r"(size|größe)",
                                                                                     re.IGNORECASE)).nextSibling.nextSibling.text.split(
                    "|")[-1].strip())
            except:
                size = ""

            try:
                source = result[1]
            except:
                source = ""

            result = {
                "title": title,
                "link": result[1],
                "size": size,
                "source": source,
                "imdb_id": imdb_id
            }

            results.append(result)
        except:
            pass

    return results
