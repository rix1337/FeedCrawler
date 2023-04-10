# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt content_all alle benötigten Parameter für die Feed-Suche auf HW bereit.

import re

from bs4 import BeautifulSoup

import feedcrawler.external_sites.feed_search.content_all as shared_blogs
from feedcrawler.external_sites.feed_search.shared import FakeFeedParserDict
from feedcrawler.external_sites.feed_search.shared import add_decrypt_instead_of_download
from feedcrawler.external_sites.feed_search.shared import check_release_not_sd
from feedcrawler.external_sites.feed_search.shared import get_download_links
from feedcrawler.external_sites.feed_search.shared import standardize_size_value
from feedcrawler.external_sites.metadata.imdb import get_imdb_id_from_content
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.sqlite_database import FeedDb
from feedcrawler.providers.url_functions import get_url, get_url_headers, get_urls_async


class BL:
    _SITE = 'HW'
    SUBSTITUTE = r"[&#\s/]"

    def __init__(self, filename):
        self.hostnames = CrawlerConfig('Hostnames')
        self.url = self.hostnames.get('hw')
        self.password = self.url.split('.')[0]

        self.URL = 'https://' + self.url
        self.FEED_URLS = [self.URL]
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
            page_url = self.URL + "/page/" + str(i)
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

        self.get_feed_method = hw_feed_enricher
        self.get_url_method = get_url
        self.get_url_headers_method = get_url_headers
        self.get_download_links_method = hw_get_download_links
        self.download_method = add_decrypt_instead_of_download

        try:
            self.imdb = float(self.config.get('imdb'))
        except:
            self.imdb = 0.0

    def periodical_task(self):
        shared_blogs.periodical_task(self)


def hw_get_download_links(self, content, title):
    try:
        try:
            content = BeautifulSoup(content, "html.parser")
        except:
            content = BeautifulSoup(str(content), "html.parser")
        download_links = content.findAll("a", href=re.compile('filecrypt'))
    except:
        print("HW hat die Detail-Seite angepasst. Parsen von Download-Links nicht möglich!")
        return False

    links_string = ""
    for link in download_links:
        links_string += str(link)

    return get_download_links(self, links_string, title)


def hw_feed_enricher(feed):
    feed = BeautifulSoup(feed, "html.parser")
    articles = feed.findAll("article")
    entries = []

    for article in articles:
        try:
            try:
                source = article.header.find("a")["href"]
            except:
                source = ""

            title = article.find("h2", {"class": "entry-title"}).text.strip()

            try:
                imdb_id = get_imdb_id_from_content(title, str(article))
            except:
                imdb_id = ""

            try:
                size = standardize_size_value(article.find("strong",
                                                           text=re.compile(
                                                               r"(size|größe)", re.IGNORECASE)).next.next.text.replace(
                    "|",
                    "").strip())
            except:
                size = ""

            media_post = article.find("strong", text="Format: ")
            if title and media_post:
                published = article.find("p", {"class": "blog-post-meta"}).text.split("|")[0].strip()
                entries.append(FakeFeedParserDict({
                    "title": title,
                    "published": published,
                    "content": [
                        FakeFeedParserDict({
                            "value": str(article)
                        })],
                    "source": source,
                    "size": size,
                    "imdb_id": imdb_id
                }))
        except:
            print("HW hat den Feed angepasst. Parsen teilweise nicht möglich!")
            continue

    feed = {"entries": entries}
    feed = FakeFeedParserDict(feed)
    return feed


def hw_search_results(content, resolution):
    content = BeautifulSoup(content, "html.parser")
    links = content.findAll("a", href=re.compile(r"^(?!.*\/category).*\/(filme|serien).*(?!.*#comments.*)$"))

    async_link_results = []
    for link in links:
        try:
            title = link.text.replace(" ", ".").strip()
            if ".xxx." not in title.lower():
                link = link["href"]
                if "#comments-title" not in link:
                    if resolution and resolution.lower() not in title.lower():
                        if "480p" in resolution:
                            if check_release_not_sd(title):
                                continue
                        else:
                            continue
                    async_link_results.append(link)
        except:
            pass

    links = get_urls_async(async_link_results)

    results = []

    for link in links:
        try:
            try:
                source = link[1]
            except:
                source = ""

            soup = BeautifulSoup(str(link[0]), "html.parser")
            title = soup.find("h2", {"class": "entry-title"}).text.strip().replace(" ", ".")

            try:
                imdb_id = get_imdb_id_from_content(title, str(soup))
            except:
                imdb_id = ""

            try:
                size = standardize_size_value(soup.find("strong",
                                                        text=re.compile(
                                                            r"(size|größe)", re.IGNORECASE)).next.next.text.replace("|",
                                                                                                                    "").strip())
            except:
                size = ""

            result = {
                "title": title,
                "link": link[1],
                "size": size,
                "source": source,
                "imdb_id": imdb_id
            }

            results.append(result)
        except:
            pass

    return results
