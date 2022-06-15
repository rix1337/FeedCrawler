# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt content_all alle benötigten Parameter für die Feed-Suche auf SJ bereit.

import json
import re

import feedcrawler.external_sites.feed_search.content_shows as shared_shows
from feedcrawler.external_sites.feed_search.shared import FakeFeedParserDict
from feedcrawler.providers import shared_state
from feedcrawler.providers.common_functions import check_valid_release, check_hoster
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.notifications import notify
from feedcrawler.providers.sqlite_database import FeedDb
from feedcrawler.providers.url_functions import get_url


class SJ:
    _INTERNAL_NAME = 'SJ'
    _SITE = 'SJ'

    def __init__(self, filename):
        self.hostnames = CrawlerConfig('Hostnames')
        self.url = self.hostnames.get('sj')

        self.filename = filename
        if "List_ContentAll_Seasons" in self.filename:
            self.config = CrawlerConfig("ContentAll")
        else:
            self.config = CrawlerConfig("ContentShows")
        self.feedcrawler = CrawlerConfig("FeedCrawler")
        self.hevc_retail = self.config.get("hevc_retail")
        self.retail_only = self.config.get("retail_only")
        self.hoster_fallback = self.config.get("hoster_fallback")
        self.hosters = CrawlerConfig("Hosters").get_section()
        self.db = FeedDb('FeedCrawler')
        self.quality = self.config.get("quality")
        self.cdc = FeedDb('cdc')
        self.last_set = self.cdc.retrieve(self._INTERNAL_NAME + "Set-" + self.filename)
        self.last_sha = self.cdc.retrieve(self._INTERNAL_NAME + "-" + self.filename)
        self.headers = {'If-Modified-Since': str(self.cdc.retrieve(self._INTERNAL_NAME + "Headers-" + self.filename))}
        self.settings_array = ["quality", "rejectlist", "regex", "hevc_retail", "retail_only", "hoster_fallback"]
        self.settings = []
        self.settings.append(self.feedcrawler.get("english"))
        self.settings.append(self.feedcrawler.get("surround"))
        self.settings.append(self.hosters)
        for s in self.settings_array:
            self.settings.append(self.config.get(s))

        self.mediatype = "Serien"
        self.listtype = ""

        self.empty_list = False
        if self.filename == 'List_ContentShows_Seasons_Regex':
            self.listtype = " (Staffeln/RegEx)"
        elif self.filename == 'List_ContentAll_Seasons':
            self.seasonssource = self.config.get('seasonssource').lower()
            self.listtype = " (Staffeln)"
        elif self.filename == 'List_ContentShows_Shows_Regex':
            self.listtype = " (RegEx)"
        list_content = shared_shows.get_series_list(self)
        if list_content:
            self.pattern = r'^(' + "|".join(list_content).lower() + ')'
        else:
            self.empty_list = True

        self.day = 0
        self.max_days = 8

        self.get_feed_method = sj_releases_to_feedparser_dict
        self.parse_download_method = sj_parse_download

    def periodical_task(self):
        shared_shows.periodical_task(self)


def sj_releases_to_feedparser_dict(releases, list_type, base_url, check_seasons_or_episodes):
    releases = json.loads(releases)
    entries = []

    for release in releases:
        if check_seasons_or_episodes:
            try:
                if list_type == 'seasons' and release['episode']:
                    continue
                elif list_type == 'episodes' and not release['episode']:
                    continue
            except:
                continue
        title = release['name']
        series_url = base_url + '/serie/' + release["_media"]['slug']
        published = release['createdAt']

        entries.append(FakeFeedParserDict({
            "title": title,
            "series_url": series_url,
            "published": published,
            "source": series_url + "#" + title,
            "size": "",
            "imdb_id": ""
        }))

    feed = {"entries": entries}
    feed = FakeFeedParserDict(feed)
    return feed


def sj_parse_download(self, series_url, title, language_id):
    if not check_valid_release(title, self.retail_only, self.hevc_retail):
        shared_state.logger.debug(title + u" - Release ignoriert (Gleiche oder bessere Quelle bereits vorhanden)")
        return False
    if self.filename == 'List_ContentAll_Seasons':
        if not self.config.get("seasonpacks"):
            staffelpack = re.search(r"s\d.*(-|\.).*s\d", title.lower())
            if staffelpack:
                shared_state.logger.debug(
                    "%s - Release ignoriert (Staffelpaket)" % title)
                return False
        if not re.search(self.seasonssource, title.lower()):
            shared_state.logger.debug(title + " - Release hat falsche Quelle")
            return False
    try:
        series_info = get_url(series_url)
        series_id = re.findall(r'data-mediaid="(.*?)"', series_info)[0]
        api_url = 'https://' + self.url + '/api/media/' + series_id + '/releases'

        response = get_url(api_url)
        seasons = json.loads(response)
        for season in seasons:
            season = seasons[season]
            for item in season['items']:
                if item['name'] == title:
                    valid = False
                    for hoster in item['hoster']:
                        if hoster:
                            if check_hoster(hoster):
                                valid = True
                    if not valid and not self.hoster_fallback:
                        storage = self.db.retrieve_all(title)
                        if 'added' not in storage and 'notdl' not in storage:
                            wrong_hoster = '[' + self._INTERNAL_NAME + ' / Hoster fehlt] - ' + title
                            if 'wrong_hoster' not in storage:
                                print(wrong_hoster)
                                self.db.store(title, 'wrong_hoster')
                                notify([{"text": wrong_hoster}])
                            else:
                                shared_state.logger.debug(wrong_hoster)
                            return False
                    else:
                        return {
                            "title": title,
                            "download_link": series_url,
                            "language_id": language_id,
                            "season": False,
                            "episode": False,
                            "size": "",  # Info not available
                            "imdb_id": ""  # Info not available
                        }
    except:
        print(self._INTERNAL_NAME + u" hat die Serien-API angepasst. Breche Download-Prüfung ab!")
        return False
