# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt content_all alle benötigten Parameter für die Feed-Suche auf SF bereit.

import datetime
import json
import re

from bs4 import BeautifulSoup

import feedcrawler.external_sites.feed_search.content_shows as shared_shows
from feedcrawler.external_sites.feed_search.shared import FakeFeedParserDict
from feedcrawler.external_sites.feed_search.shared import standardize_size_value
from feedcrawler.external_sites.metadata.imdb import get_imdb_id_from_link
from feedcrawler.providers import shared_state
from feedcrawler.providers.common_functions import check_valid_release, rreplace, check_hoster
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.notifications import notify
from feedcrawler.providers.sqlite_database import FeedDb
from feedcrawler.providers.url_functions import get_url


class SF:
    _INTERNAL_NAME = 'SF'
    _SITE = 'SF'

    def __init__(self, filename):
        self.hostnames = CrawlerConfig('Hostnames')
        self.url = self.hostnames.get('sf')

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
        self.max_days = int(CrawlerConfig('CustomF').get('search'))

        self.get_feed_method = sf_releases_to_feedparser_dict
        self.parse_download_method = sf_parse_download

    def periodical_task(self):
        shared_shows.periodical_task(self)


def sf_releases_to_feedparser_dict(releases, list_type, base_url, check_seasons_or_episodes):
    content = BeautifulSoup(releases, "html.parser")
    releases = content.findAll("div", {"class": "row"}, style=re.compile("order"))
    entries = []

    for release in releases:
        a = release.find("a", href=re.compile("/"))
        title = a.text
        is_episode = re.match(r'.*(S\d{1,3}E\d{1,3}).*', title)
        if check_seasons_or_episodes:
            try:
                if list_type == 'seasons' and is_episode:
                    continue
                elif list_type == 'episodes' and not is_episode:
                    continue
            except:
                continue

        series_url = base_url + a['href']
        published = release.find("div", {"class": "datime"}).text

        entries.append(FakeFeedParserDict({
            "title": title,
            "series_url": series_url,
            "published": published,
            "source": series_url,
            "size": "",
            "imdb_id": "",
        }))

    feed = {"entries": entries}
    feed = FakeFeedParserDict(feed)
    return feed


def sf_parse_download(self, series_url, title, language_id):
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
        if language_id == 2:
            lang = 'EN'
        else:
            lang = 'DE'
        epoch = str(datetime.datetime.now().timestamp()).replace('.', '')[:-3]
        season_page = get_url(series_url)
        season_details = re.findall(r"initSeason\('(.+?)\',(.+?),", season_page)[-1]

        season_page_soup = BeautifulSoup(season_page, "html.parser")
        imdb_link = ""
        try:
            imdb = season_page_soup.find("a", href=re.compile("imdb.com"))
            imdb_link = imdb["href"].replace("https://anonym.to/?", "")
        except:
            pass

        try:
            imdb_id = get_imdb_id_from_link(title, imdb_link)
        except:
            imdb_id = ""

        season_id = season_details[0]
        season_nr = season_details[1]

        sf = CrawlerConfig('Hostnames').get('sf')

        api_url = 'https://' + sf + '/api/v1/' + season_id + '/season/' + season_nr + '?lang=' + lang + '&_=' + epoch

        response = get_url(api_url)
        clean_response_content = BeautifulSoup(response, "html.parser").body.text
        info = json.loads(clean_response_content)

        is_episode = re.findall(r'.*\.(s\d{1,3}e\d{1,3})\..*', title, re.IGNORECASE)
        multiple_episodes = False
        if is_episode:
            episode_string = re.findall(r'.*S\d{1,3}(E\d{1,3}).*', is_episode[0])[0].lower()
            season_string = re.findall(r'.*(S\d{1,3})E\d{1,3}.*', is_episode[0])[0].lower()
            season_title = rreplace(title.lower().replace(episode_string, ''), "-", ".*", 1).lower().replace(
                ".repack", "")
            season_title = season_title.replace(".untouched", ".*").replace(".dd+51", ".dd.51")
            episode = str(int(episode_string.replace("e", "")))
            season = str(int(season_string.replace("s", "")))
            episode_name = re.findall(r'.*\.s\d{1,3}(\..*).german', season_title, re.IGNORECASE)
            if episode_name:
                season_title = season_title.replace(episode_name[0], '')
            codec_tags = [".h264", ".x264"]
            for tag in codec_tags:
                season_title = season_title.replace(tag, ".*264")
            web_tags = [".web-rip", ".webrip", ".webdl", ".web-dl"]
            for tag in web_tags:
                season_title = season_title.replace(tag, ".web.*")
        else:
            season = False
            episode = False
            season_title = title
            multiple_episodes = re.findall(r'(e\d{1,3}-e*\d{1,3}\.)', season_title, re.IGNORECASE)
            if multiple_episodes:
                season_title = season_title.replace(multiple_episodes[0], '.*')

        content = BeautifulSoup(info['html'], "html.parser")
        release_info = content.find("small", text=re.compile(season_title, re.IGNORECASE)).parent.parent.parent

        try:
            size = standardize_size_value(
                release_info.findAll("div", {'class': 'row'})[1].parent.find("span", {"class": "morespec"}).text.split(
                    "|")[
                    1].strip())
        except:
            size = ""

        if is_episode or multiple_episodes:
            try:
                try:
                    number_of_episodes = release_info.find("div", {"class": "list"}).findAll("div", recursive=False)[
                        -1].div.text.strip()
                except:
                    number_of_episodes = re.findall(r'E(\d{1,3})', title)[-1]

                total_episodes = int(''.join(filter(str.isdigit, number_of_episodes)))
                total_size = float(re.sub('[^0-9,.]', '', size))
                size_unit = re.sub('[0-9,.]', '', size).strip()

                episode_size = round(total_size / total_episodes, 2)

                if multiple_episodes:
                    episodes_in_title = re.findall(r'E(\d{1,3})', title)
                    first_episode_in_title = episodes_in_title[0]
                    last_episode_in_title = episodes_in_title[-1]
                    episodes_in_title = int(last_episode_in_title) - int(first_episode_in_title) + 1
                    episode_size = round(episode_size * episodes_in_title, 2)

                size = "~" + standardize_size_value(str(episode_size) + " " + size_unit)
            except:
                pass

        links = release_info.findAll("div", {'class': 'row'})[1].findAll('a')
        download_link = False
        for link in links:
            if check_hoster(link.text.replace('\n', '')):
                download_link = "https://" + self.url + link['href']
                break
        if not download_link and not self.hoster_fallback:
            storage = self.db.retrieve_all(title)
            if 'added' not in storage and 'notdl' not in storage:
                wrong_hoster = '[SF/Hoster fehlt] - ' + title
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
                "download_link": download_link,
                "language_id": language_id,
                "season": season,
                "episode": episode,
                "size": size,
                "imdb_id": imdb_id
            }
    except:
        print(u"SF hat die Serien-API angepasst. Breche Download-Prüfung ab!")
        return False
