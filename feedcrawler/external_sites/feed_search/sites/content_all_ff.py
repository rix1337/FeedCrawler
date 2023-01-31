# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt content_all alle benötigten Parameter für die Feed-Suche auf FF bereit.

import datetime
import json
import re

from bs4 import BeautifulSoup

import feedcrawler.external_sites.feed_search.content_all as shared_blogs
from feedcrawler.external_sites.feed_search.shared import FakeFeedParserDict
from feedcrawler.external_sites.feed_search.shared import add_decrypt_instead_of_download
from feedcrawler.external_sites.feed_search.shared import standardize_size_value
from feedcrawler.external_sites.feed_search.shared import unused_get_feed_parameter
from feedcrawler.external_sites.metadata.imdb import get_imdb_id_from_link
from feedcrawler.providers import shared_state
from feedcrawler.providers.common_functions import check_hoster
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.sqlite_database import FeedDb
from feedcrawler.providers.url_functions import get_url, get_url_headers


class BL:
    _SITE = 'FF'
    SUBSTITUTE = r"[&#\s/]"

    def __init__(self, filename):
        self.hostnames = CrawlerConfig('Hostnames')
        self.url = self.hostnames.get('ff')
        self.password = self.url.split('.')[0]

        self.URL = 'https://' + self.url
        self.FEED_URLS = []
        self.config = CrawlerConfig("ContentAll")
        self.feedcrawler = CrawlerConfig("FeedCrawler")
        self.filename = filename
        self.pattern = False
        self.db = FeedDb('FeedCrawler')
        self.hevc_retail = self.config.get("hevc_retail")
        self.retail_only = self.config.get("retail_only")
        self.hosters = CrawlerConfig("Hosters").get_section()
        self.hoster_fallback = self.config.get("hoster_fallback")

        self.day = 0
        while self.day <= int(CrawlerConfig('CustomF').get('search')) - 1:
            delta = (datetime.datetime.now() - datetime.timedelta(days=self.day)).strftime("%Y-%m-%d")
            page_url = 'https://' + self.url + '/updates/' + delta
            if page_url not in self.FEED_URLS:
                self.FEED_URLS.append(page_url)
            self.day += 1
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

        self.get_feed_method = ff_feed_enricher
        self.get_url_method = get_url
        self.get_url_headers_method = get_url_headers
        self.get_download_links_method = ff_get_download_links
        self.download_method = add_decrypt_instead_of_download

        try:
            self.imdb = float(self.config.get('imdb'))
        except:
            self.imdb = 0.0

    def periodical_task(self):
        shared_blogs.periodical_task(self)


def ff_get_download_links(self, content, title):
    unused_get_feed_parameter(title)
    try:
        try:
            content = BeautifulSoup(content, "html.parser")
        except:
            content = BeautifulSoup(str(content), "html.parser")
        links = content.findAll("div", {'class': 'row'})[1].findAll('a')
        download_link = False
        for link in links:
            if check_hoster(link.text.replace('\n', '')):
                download_link = "https://" + self.url + link['href']
                break
    except:
        print(u"FF hat die Detail-Seite angepasst. Parsen von Download-Links nicht möglich!")
        return False

    return [download_link]


def ff_feed_enricher(releases):
    entries = []
    if releases:
        try:
            base_url = CrawlerConfig('Hostnames').get('ff')
            page = BeautifulSoup(releases, "html.parser")
            day = page.find("li", {"class": "active"}).find("a")["href"].replace("/updates/", "").replace("#list", "")
            movies = page.findAll("div", {"class": "sra"}, style=re.compile("order"))

            for movie in movies:
                movie_url = "https://" + base_url + movie.find("a")["href"]
                details = BeautifulSoup(get_url(movie_url), "html.parser")
                api_secret = details.find("script", text=re.compile(".*initMovie.*")).text.split("'")[1]
                epoch = str(datetime.datetime.now().timestamp()).replace('.', '')[:-3]
                api_url = "https://" + base_url + '/api/v1/' + api_secret + '?lang=ALL&_=' + epoch
                response = get_url(api_url)
                clean_response_content = BeautifulSoup(response, "html.parser").body.text
                info = BeautifulSoup(json.loads(clean_response_content)["html"], "html.parser")

                releases = movie.findAll("a", href=re.compile("^(?!.*(genre))"), text=re.compile("\S"))
                for release in releases:
                    title = release.text.strip()
                    time = movie.find("span", {"class": "lsf-icon timed"}).text
                    published = day + "|" + time

                    imdb_link = ""
                    try:
                        imdb_infos = details.find("ul", {"class": "info"})
                        imdb_link = str(imdb_infos.find("a")["href"])
                    except:
                        pass

                    try:
                        imdb_id = get_imdb_id_from_link(title, imdb_link)
                    except:
                        imdb_id = ""

                    release_infos = info.findAll("div", {"class": "entry"})
                    release_info = False
                    for check_info in release_infos:
                        if check_info.find("span", text=title):
                            release_info = str(check_info)

                    if release_info:
                        try:
                            size = standardize_size_value(
                                BeautifulSoup(release_info, "html.parser").findAll("span")[2].text.split(":", 1)[
                                    1].strip())
                        except:
                            size = ""

                        entries.append(FakeFeedParserDict({
                            "title": title,
                            "published": published,
                            "content": [FakeFeedParserDict({
                                "value": release_info + " mkv"})],
                            "source": movie_url,
                            "size": size,
                            "imdb_id": imdb_id
                        }))
        except Exception as e:
            shared_state.logger.debug("FF-Feed konnte nicht gelesen werden: " + str(e))
            pass

    feed = {"entries": entries}
    feed = FakeFeedParserDict(feed)
    return feed
