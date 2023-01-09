# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt content_all alle benötigten Parameter für die Feed-Suche auf BY bereit.

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
    _SITE = 'BY'
    SUBSTITUTE = r"[&#\s/]"

    def __init__(self, filename):
        self.hostnames = CrawlerConfig('Hostnames')
        self.url = self.hostnames.get('by')
        self.password = self.url.split('.')[0]

        if "List_ContentAll_Seasons" not in filename:
            self.URL = 'https://' + self.url + "/?cat=1"
        else:
            self.URL = 'https://' + self.url + "/?cat=2"
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
            page_url = self.URL + "&start=" + str(i)
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

        self.get_feed_method = by_feed_enricher
        self.get_url_method = get_url
        self.get_url_headers_method = get_url_headers
        self.get_download_links_method = by_get_download_links
        self.download_method = add_decrypt_instead_of_download

        try:
            self.imdb = float(self.config.get('imdb'))
        except:
            self.imdb = 0.0

    def periodical_task(self):
        shared_blogs.periodical_task(self)


def by_get_download_links(self, content, title):
    async_link_results = re.findall(r'href="(http[^"\'>]*)"', content)
    links = get_urls_async(async_link_results)

    content = []
    for link in links:
        if link[0]:
            link = BeautifulSoup(link[0], "html.parser").find("a", href=re.compile("/go\.php\?"))
            try:
                content.append('href="' + link["href"] + '">' + link.text.replace(" ", "") + '<')
            except:
                pass

    content = "".join(content)
    download_links = get_download_links(self, content, title)
    return download_links


def by_feed_enricher(content):
    base_url = "https://" + CrawlerConfig('Hostnames').get('by')
    content = BeautifulSoup(content, "html.parser")
    posts = content.findAll("a", href=re.compile("/category/"), text=re.compile("Download"))
    async_results = []
    for post in posts:
        try:
            async_results.append(base_url + post['href'])
        except:
            pass
    results = get_urls_async(async_results)

    entries = []
    if results:
        for result in results:
            try:
                content = []
                result = BeautifulSoup(result[0], "html.parser")
                details = result.findAll("td", {"valign": "TOP", "align": "CENTER"})[1]
                title = details.find("small").text
                published = details.find("th", {"align": "RIGHT"}).text

                imdb_link = ""
                try:
                    imdb = details.find("a", href=re.compile("imdb.com"))
                    imdb_link = imdb["href"].replace("https://anonym.to/?", "")
                except:
                    pass

                try:
                    imdb_id = get_imdb_id_from_link(title, imdb_link)
                except:
                    imdb_id = ""

                try:
                    size = standardize_size_value(
                        details.findAll("td", {"align": "LEFT"})[-1].text.split(" ", 1)[1].strip())
                except:
                    size = ""

                try:
                    source = result.head.find("link")["href"]
                except:
                    source = ""

                links = result.find_all("iframe")
                for link in links:
                    content.append('href="' + link["src"] + '"')

                content = "".join(content)

                entries.append(FakeFeedParserDict({
                    "title": title,
                    "published": published,
                    "content": [FakeFeedParserDict({
                        "value": content + " mkv"})],
                    "source": source,
                    "size": size,
                    "imdb_id": imdb_id,
                }))
            except:
                pass

    feed = {"entries": entries}
    feed = FakeFeedParserDict(feed)
    return feed


def by_search_results(content, base_url, resolution):
    content = BeautifulSoup(content, "html.parser")
    links = content.findAll("a", href=re.compile("/category/"))

    async_link_results = []
    for link in links:
        try:
            title = link.text.replace(" ", ".").strip()
            if ".xxx." not in title.lower():
                link = "https://" + base_url + link['href']
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
            soup = BeautifulSoup(link[0], "html.parser")
            details = soup.findAll("td", {"valign": "TOP", "align": "CENTER"})[1]
            title = details.find("small").text.replace(" ", ".")

            imdb_link = ""
            try:
                imdb = details.find("a", href=re.compile("imdb.com"))
                imdb_link = imdb["href"].replace("https://anonym.to/?", "")
            except:
                pass

            try:
                imdb_id = get_imdb_id_from_link(title, imdb_link)
            except:
                imdb_id = ""

            try:
                size = standardize_size_value(
                    details.findAll("td", {"align": "LEFT"})[-1].text.split(" ", 1)[1].strip())
            except:
                size = ""

            try:
                source = link[1]
            except:
                source = ""

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


def by_page_download_link(self, download_link, key):
    unused_get_feed_parameter(key)
    by = self.hostnames.get('by')
    download_link = get_url(download_link)
    soup = BeautifulSoup(download_link, "html.parser")
    links = soup.find_all("iframe")
    async_link_results = []
    for link in links:
        link = link["src"]
        if 'https://' + by in link:
            async_link_results.append(link)
    links = get_urls_async(async_link_results)

    url_hosters = []
    for link in links:
        if link[0]:
            link = BeautifulSoup(link[0], "html.parser").find("a", href=re.compile("/go\.php\?"))
            if link:
                url_hosters.append([link["href"], link.text.replace(" ", "")])
    return check_download_links(self, url_hosters)
