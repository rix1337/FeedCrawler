# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt content_all alle benötigten Parameter für die Feed-Suche auf FX bereit.

import re

from bs4 import BeautifulSoup

import feedcrawler.external_sites.feed_search.content_all as shared_blogs
from feedcrawler.external_sites.feed_search.shared import FakeFeedParserDict
from feedcrawler.external_sites.feed_search.shared import add_decrypt_instead_of_download
from feedcrawler.external_sites.feed_search.shared import standardize_size_value
from feedcrawler.external_sites.feed_search.shared import unused_get_feed_parameter
from feedcrawler.external_sites.metadata.imdb import get_imdb_id_from_content
from feedcrawler.providers.common_functions import simplified_search_term_in_title
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.sqlite_database import FeedDb
from feedcrawler.providers.url_functions import get_url, get_url_headers, get_urls_async


class BL:
    _SITE = 'FX'
    SUBSTITUTE = r"[&#\s/]"

    def __init__(self, filename):
        self.hostnames = CrawlerConfig('Hostnames')
        self.url = self.hostnames.get('fx')
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

        self.get_feed_method = fx_feed_enricher
        self.get_url_method = get_url
        self.get_url_headers_method = get_url_headers
        self.get_download_links_method = fx_get_download_links
        self.download_method = add_decrypt_instead_of_download

        try:
            self.imdb = float(self.config.get('imdb'))
        except:
            self.imdb = 0.0

    def periodical_task(self):
        shared_blogs.periodical_task(self)


def fx_content_to_soup(content):
    content = BeautifulSoup(content, "html.parser")
    return content


def fx_get_details(content, search_title):
    fx = CrawlerConfig('Hostnames').get('fx')

    try:
        content = BeautifulSoup(content, "html.parser")
    except:
        content = BeautifulSoup(str(content), "html.parser")

    size = ""
    imdb_id = ""

    titles = content.findAll("a", href=re.compile("(filecrypt|safe." + fx + ")"))
    i = 0
    for title in titles:
        title = title.text.encode("ascii", errors="ignore").decode().replace("/", "").replace(" ", ".")
        if search_title in title:
            try:
                imdb_id = get_imdb_id_from_content(title, str(content))
            except:
                imdb_id = ""

            try:
                size = standardize_size_value(content.findAll("strong",
                                                              text=re.compile(
                                                                  r"(size|größe)", re.IGNORECASE))[i]. \
                                              next.next.text.replace("|", "").strip())
            except:
                size = ""
        i += 1

    details = {
        "size": size,
        "imdb_id": imdb_id
    }

    return details


def fx_get_download_links(self, content, title):
    unused_get_feed_parameter(self)
    try:
        try:
            content = BeautifulSoup(content, "html.parser")
        except:
            content = BeautifulSoup(str(content), "html.parser")
        try:
            download_links = [content.find("a", text=re.compile(r".*" + title + r".*"))['href']]
        except:
            fx = CrawlerConfig('Hostnames').get('fx')
            download_links = re.findall(re.compile('"(.+?(?:filecrypt|safe.' + fx + ').+?)"'), str(content))
    except:
        return False
    return download_links


def fx_feed_enricher(feed):
    feed = BeautifulSoup(feed, "html.parser")
    fx = CrawlerConfig('Hostnames').get('fx')
    articles = feed.findAll("article")
    entries = []

    for article in articles:
        try:
            article = BeautifulSoup(str(article), "html.parser")
            try:
                source = article.header.find("a")["href"]
            except:
                source = ""

            titles = article.findAll("a", href=re.compile("(filecrypt|safe." + fx + ")"))
            i = 0
            for title in titles:
                title = title.text.encode("ascii", errors="ignore").decode().replace("/", "").replace(" ", ".")
                if title:
                    try:
                        imdb_id = get_imdb_id_from_content(title, str(article))
                    except:
                        imdb_id = ""

                    try:
                        size = standardize_size_value(article.findAll("strong",
                                                                      text=re.compile(
                                                                          r"(size|größe)", re.IGNORECASE))[i]. \
                                                      next.next.text.replace("|", "").strip())
                    except:
                        size = ""

                    if "download" in title.lower():
                        try:
                            title = str(article.find("strong", text=re.compile(r".*Release.*")).nextSibling)
                        except:
                            continue
                    published = ""
                    dates = article.findAll("time")
                    for date in dates:
                        published = date["datetime"]
                    entries.append(FakeFeedParserDict({
                        "title": title,
                        "published": published,
                        "content": [
                            FakeFeedParserDict({
                                "value": str(article) + " mkv"
                            })],
                        "source": source,
                        "size": size,
                        "imdb_id": imdb_id
                    }))
                    i += 1
        except:
            print("FX hat den Feed angepasst. Parsen teilweise nicht möglich!")
            continue

    feed = {"entries": entries}
    feed = FakeFeedParserDict(feed)
    return feed


def fx_search_results(content, search_term):
    fx = CrawlerConfig('Hostnames').get('fx')
    articles = content.find("main").find_all("article")

    async_link_results = []
    for article in articles:
        if simplified_search_term_in_title(search_term, article.find("h2").text):
            link = article.find("a")["href"]
            if link:
                async_link_results.append(link)

    links = get_urls_async(async_link_results)

    results = []

    for link in links:
        article = BeautifulSoup(str(link[0]), "html.parser")
        titles = article.findAll("a", href=re.compile("(filecrypt|safe." + fx + ")"))
        i = 0
        for title in titles:
            try:
                try:
                    source = link[1]
                except:
                    source = ""

                link = article.find("link", rel="canonical")["href"]
                title = title.text.encode("ascii", errors="ignore").decode().replace("/", "").replace(" ", ".")
                if title and "-fun" in title.lower():
                    try:
                        imdb_id = get_imdb_id_from_content(title, str(article))
                    except:
                        imdb_id = ""

                    try:
                        size = standardize_size_value(article.findAll("strong",
                                                                      text=re.compile(
                                                                          r"(size|größe)", re.IGNORECASE))[i]. \
                                                      next.next.text.replace("|", "").strip())
                    except:
                        size = ""

                    if "download" in title.lower():
                        try:
                            title = str(content.find("strong", text=re.compile(r".*Release.*")).nextSibling)
                        except:
                            continue

                    result = {
                        "title": title,
                        "link": link,
                        "size": size,
                        "source": source,
                        "imdb_id": imdb_id
                    }

                    results.append(result)
                    i += 1
            except:
                pass
    return results
