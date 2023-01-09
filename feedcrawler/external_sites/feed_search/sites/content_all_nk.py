# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt content_all alle benötigten Parameter für die Feed-Suche auf NK bereit.

import re

from bs4 import BeautifulSoup

import feedcrawler.external_sites.feed_search.content_all as shared_blogs
from feedcrawler.external_sites.feed_search.shared import FakeFeedParserDict
from feedcrawler.external_sites.feed_search.shared import add_decrypt_instead_of_download
from feedcrawler.external_sites.feed_search.shared import check_download_links
from feedcrawler.external_sites.feed_search.shared import check_release_not_sd
from feedcrawler.external_sites.feed_search.shared import get_download_links
from feedcrawler.external_sites.feed_search.shared import standardize_size_value
from feedcrawler.external_sites.feed_search.shared import unused_get_feed_parameter
from feedcrawler.external_sites.metadata.imdb import get_imdb_id_from_link
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.sqlite_database import FeedDb
from feedcrawler.providers.url_functions import get_url, get_url_headers, get_urls_async


class BL:
    _SITE = 'NK'
    SUBSTITUTE = r"[&#\s/]"

    def __init__(self, filename):
        self.hostnames = CrawlerConfig('Hostnames')
        self.url = self.hostnames.get('nk')
        self.password = self.url.split('.')[0].capitalize()

        self.URL = 'https://' + self.url + '/'
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
            page_url = self.URL + "page-" + str(i)
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

        self.get_feed_method = nk_feed_enricher
        self.get_url_method = get_url
        self.get_url_headers_method = get_url_headers
        self.get_download_links_method = get_download_links
        self.download_method = add_decrypt_instead_of_download

        try:
            self.imdb = float(self.config.get('imdb'))
        except:
            self.imdb = 0.0

    def periodical_task(self):
        shared_blogs.periodical_task(self)


def nk_feed_enricher(content):
    base_url = "https://" + CrawlerConfig('Hostnames').get('nk')
    content = BeautifulSoup(content, "html.parser")
    posts = content.findAll("a", {"class": "btn"}, href=re.compile("/release/"))
    async_results = []
    for post in posts:
        try:
            async_results.append(base_url + post['href'])
        except:
            pass
    async_results = get_urls_async(async_results)

    entries = []
    if async_results:
        for result in async_results:
            try:
                content = []
                details = BeautifulSoup(result[0], "html.parser").find("div", {"class": "article"})
                title = details.find("span", {"class": "subtitle"}).text
                published = details.find("p", {"class": "meta"}).text
                content.append("mkv ")

                links = details.find_all("a", href=re.compile("/go/"))
                for link in links:
                    content.append('href="' + base_url + link["href"] + '">' + link.text + '<')
                content = "".join(content)

                try:
                    imdb_link = details.find("a", href=re.compile("imdb.com"))
                    imdb_id = get_imdb_id_from_link(title, imdb_link["href"])
                except:
                    imdb_id = ""

                try:
                    size = standardize_size_value(
                        details.find("span", text=re.compile(r"(size|größe)", re.IGNORECASE)).next.next.strip())
                except:
                    size = ""

                try:
                    source = result[1]
                except:
                    source = ""

                entries.append(FakeFeedParserDict({
                    "title": title,
                    "published": published,
                    "content": [FakeFeedParserDict({
                        "value": content})],
                    "source": source,
                    "size": size,
                    "imdb_id": imdb_id
                }))
            except:
                pass

    feed = {"entries": entries}
    feed = FakeFeedParserDict(feed)
    return feed


def nk_search_results(content, base_url, resolution):
    content = BeautifulSoup(content, "html.parser")
    links = content.findAll("a", {"class": "btn"}, href=re.compile("/release/"))

    async_link_results = []
    for link in links:
        try:
            title = link.parent.parent.parent.find("span", {"class": "subtitle"}).text.replace(" ", ".")
            if ".xxx." not in title.lower():
                link = base_url + link["href"]
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
            details = BeautifulSoup(link[0], "html.parser").find("div", {"class": "article"})
            title = details.find("span", {"class": "subtitle"}).text.replace(" ", ".")

            try:
                imdb_link = details.find("a", href=re.compile("imdb.com"))
                imdb_id = get_imdb_id_from_link(title, imdb_link["href"])
            except:
                imdb_id = ""

            try:
                size = standardize_size_value(
                    details.find("span", text=re.compile(r"(size|größe)", re.IGNORECASE)).next.next.strip())
            except:
                size = ""

            try:
                source = link[1]
            except:
                source = ""

            result = {
                "title": title,
                "link": source,
                "size": size,
                "source": source,
                "imdb_id": imdb_id
            }

            results.append(result)
        except:
            pass

    return results


def nk_page_download_link(self, download_link, key):
    unused_get_feed_parameter(key)
    nk = self.hostnames.get('nk')
    download_link = get_url(download_link)
    soup = BeautifulSoup(download_link, "html.parser")
    url_hosters = []
    hosters = soup.find_all("a", href=re.compile("/go/"))
    for hoster in hosters:
        url_hosters.append(['https://' + nk + hoster["href"], hoster.text])
    return check_download_links(self, url_hosters)
