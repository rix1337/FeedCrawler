# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt content_all alle benötigten Parameter für die Feed-Suche auf WW bereit.

import re

from bs4 import BeautifulSoup

import feedcrawler.external_sites.feed_search.content_all as shared_blogs
from feedcrawler.external_sites.feed_search.shared import FakeFeedParserDict
from feedcrawler.external_sites.feed_search.shared import add_decrypt_instead_of_download
from feedcrawler.external_sites.feed_search.shared import get_download_links
from feedcrawler.external_sites.feed_search.shared import standardize_size_value
from feedcrawler.external_sites.metadata.imdb import get_imdb_id_from_title
from feedcrawler.providers import shared_state
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.sqlite_database import FeedDb
from feedcrawler.providers.url_functions import get_url, post_url_headers


class BL:
    _SITE = 'WW'
    SUBSTITUTE = r"[&#\s/]"

    def __init__(self, filename):
        self.hostnames = CrawlerConfig('Hostnames')
        self.url = self.hostnames.get('ww')
        self.password = self.url.split('.')[0]

        if "List_ContentAll_Seasons" not in filename:
            self.URL = 'https://' + self.url + "/ajax" + "|/cat/movies|p=1&t=c&q=5"
        else:
            self.URL = 'https://' + self.url + "/ajax" + "|/cat/series|p=1&t=c&q=9"
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
            if "List_ContentAll_Seasons" not in filename:
                page_url = self.URL.replace("|p=1", "|p=" + str(i))
                if page_url not in self.FEED_URLS:
                    self.FEED_URLS.append(page_url)
                i += 1
            else:
                page_url = self.URL.replace("|p=1", "|p=" + str(i))
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

        self.get_feed_method = ww_feed_enricher
        self.get_url_method = ww_post_url_headers
        self.get_url_headers_method = ww_post_url_headers
        self.get_download_links_method = ww_get_download_links
        self.download_method = add_decrypt_instead_of_download

        try:
            self.imdb = float(self.config.get('imdb'))
        except:
            self.imdb = 0.0

    def periodical_task(self):
        shared_blogs.periodical_task(self)


def ww_post_url_headers(url, headers=False):
    try:
        if not headers:
            headers = {}
        payload = url.split("|")
        url = payload[0]
        referer = payload[0].replace("/ajax", payload[1])
        data = payload[2]
        headers["Referer"] = referer
        response = post_url_headers(url, headers, data)
        if not response["text"] or response["status_code"] is not (200 or 304) or not '<span class="main-rls">' in \
                                                                                      response["text"]:
            if not shared_state.values["ww_blocked"]:
                print("WW hat den Feed-Anruf während der Feed-Suche blockiert.")
                shared_state.update("ww_blocked", True)
            return ""
        return response
    except:
        return ""


def ww_get_download_links(self, content, title):
    base_url = "https://" + CrawlerConfig('Hostnames').get('ww')
    content = content.replace("mkv|", "")
    download_links = []
    try:
        response = get_url(content)
        if not response or "NinjaFirewall 429" in response:
            if not shared_state.values["ww_blocked"]:
                print(
                    "WW hat den Link-Abruf für " + title + " blockiert. Eine spätere Anfrage hat möglicherweise Erfolg!")
                shared_state.update("ww_blocked", True)
            return False
        links = BeautifulSoup(response, "html.parser").findAll("div", {"id": "download-links"})
        for link in links:
            hoster = link.text
            if 'Direct Download 100 MBit/s' not in hoster:
                url = base_url + link.find("a")["href"]
                download_links.append('href="' + url + '" ' + hoster + '<')
        download_links = "".join(download_links)

        download_links = get_download_links(self, download_links, title)
        return download_links
    except:
        return False


def ww_feed_enricher(content):
    base_url = "https://" + CrawlerConfig('Hostnames').get('ww')
    try:
        response = BeautifulSoup(content, "html.parser")
    except:
        response = BeautifulSoup(content["text"], "html.parser")
    posts = response.findAll("li")
    entries = []
    if posts:
        for post in posts:
            try:
                link = post.findAll("a", href=re.compile("/download"))[1]
                title = link.nextSibling.nextSibling.strip()
                published = post.find("span", {"class": "main-date"}).text.replace("\n", "")

                try:
                    imdb_id = get_imdb_id_from_title(title)
                    if not imdb_id:
                        imdb_id = ""
                except:
                    imdb_id = ""

                try:
                    size = standardize_size_value(post.find("span", {"class": "main-size"}).text.strip())
                except:
                    size = ""

                try:
                    source = base_url + link["href"]
                except:
                    source = ""

                content = "mkv|" + source

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
