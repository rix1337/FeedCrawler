# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import datetime
import hashlib
import json
import re
from bs4 import BeautifulSoup

import rsscrawler.sites.shared.content_shows as shared_shows
from rsscrawler.common import add_decrypt
from rsscrawler.common import check_hoster
from rsscrawler.common import check_valid_release
from rsscrawler.common import rreplace
from rsscrawler.config import RssConfig
from rsscrawler.db import RssDb
from rsscrawler.notifiers import notify
from rsscrawler.sites.shared.fake_feed import sf_releases_to_feedparser_dict
from rsscrawler.url import get_redirected_url
from rsscrawler.url import get_url
from rsscrawler.url import get_url_headers


class SF:
    _INTERNAL_NAME = "SJ"

    def __init__(self, configfile, dbfile, device, logging, scraper, filename):
        self.configfile = configfile
        self.dbfile = dbfile
        self.device = device

        self.hostnames = RssConfig('Hostnames', self.configfile)
        self.sf = self.hostnames.get('sf')

        if "MB_Staffeln" in self.filename:
            self.config = RssConfig("MB", self.configfile)
        else:
            self.config = RssConfig(self._INTERNAL_NAME, self.configfile)
        self.rsscrawler = RssConfig("RSScrawler", self.configfile)
        self.hevc_retail = self.config.get("hevc_retail")
        self.retail_only = self.config.get("retail_only")
        self.hoster_fallback = self.config.get("hoster_fallback")
        self.hosters = RssConfig("Hosters", configfile).get_section()
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.scraper = scraper
        self.filename = filename
        self.db = RssDb(self.dbfile, 'rsscrawler')
        self.quality = self.config.get("quality")
        self.cdc = RssDb(self.dbfile, 'cdc')
        self.last_set_sf = self.cdc.retrieve("SFSet-" + self.filename)
        self.last_sha_sf = self.cdc.retrieve("SF-" + self.filename)
        self.headers = {'If-Modified-Since': str(self.cdc.retrieve("SFHeaders-" + self.filename))}
        self.settings_array = ["quality", "rejectlist", "regex", "hevc_retail", "retail_only", "hoster_fallback"]
        self.settings = []
        self.settings.append(self.rsscrawler.get("english"))
        self.settings.append(self.rsscrawler.get("surround"))
        self.settings.append(self.hosters)
        for s in self.settings_array:
            self.settings.append(self.config.get(s))

        self.mediatype = "Serien"
        self.listtype = ""

        self.empty_list = False
        if self.filename == 'SJ_Staffeln_Regex':
            self.listtype = " (Staffeln/RegEx)"
        elif self.filename == 'MB_Staffeln':
            self.seasonssource = self.config.get('seasonssource').lower()
            self.listtype = " (Staffeln)"
        elif self.filename == 'SJ_Serien_Regex':
            self.listtype = " (RegEx)"
        list_content = shared_shows.get_series_list(self)
        if list_content:
            self.pattern = r'^(' + "|".join(list_content).lower() + ')'
        else:
            self.empty_list = True

        self.day = 0

    # ToDo Refactor to content_shows
    def parse_download(self, series_url, title, language_id):
        if not check_valid_release(title, self.retail_only, self.hevc_retail, self.dbfile):
            self.log_debug(title + u" - Release ignoriert (Gleiche oder bessere Quelle bereits vorhanden)")
            return
        if self.filename == 'MB_Staffeln':
            if not self.config.get("seasonpacks"):
                staffelpack = re.search(r"s\d.*(-|\.).*s\d", title.lower())
                if staffelpack:
                    self.log_debug(
                        "%s - Release ignoriert (Staffelpaket)" % title)
                    return
            if not re.search(self.seasonssource, title.lower()):
                self.log_debug(title + " - Release hat falsche Quelle")
                return
        try:
            if language_id == 2:
                lang = 'EN'
            else:
                lang = 'DE'
            epoch = str(datetime.datetime.now().timestamp()).replace('.', '')[:-3]
            api_url = series_url + '?lang=' + lang + '&_=' + epoch
            response = get_url(api_url, self.configfile, self.dbfile, self.scraper)
            info = json.loads(response)

            is_episode = re.findall(r'.*\.(s\d{1,3}e\d{1,3})\..*', title, re.IGNORECASE)
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

            content = BeautifulSoup(info['html'], 'lxml')
            releases = content.find("small", text=re.compile(season_title, re.IGNORECASE)).parent.parent.parent
            links = releases.findAll("div", {'class': 'row'})[1].findAll('a')
            valid = False
            for link in links:
                if check_hoster(link.text.replace('\n', ''), self.configfile):
                    download_link = get_redirected_url("https://" + self.sf + link['href'], self.configfile,
                                                       self.dbfile, self.scraper)
                    valid = True
                    break
            if not valid and not self.hoster_fallback:
                storage = self.db.retrieve_all(title)
                if 'added' not in storage and 'notdl' not in storage:
                    wrong_hoster = '[SF/Hoster fehlt] - ' + title
                    if 'wrong_hoster' not in storage:
                        print(wrong_hoster)
                        self.db.store(title, 'wrong_hoster')
                        notify([wrong_hoster], self.configfile)
                    else:
                        self.log_debug(wrong_hoster)
            else:
                return self.send_package(title, download_link, language_id, season, episode)
        except:
            print(u"SF hat die Serien-API angepasst. Breche Download-Prüfung ab!")

    # ToDo Refactor to content_shows
    def send_package(self, title, download_link, language_id, season, episode):
        englisch = ""
        if language_id == 2:
            englisch = "/Englisch"
        if self.filename == 'SJ_Serien_Regex':
            link_placeholder = '[Episode/RegEx' + englisch + '] - '
        elif self.filename == 'SJ_Serien':
            link_placeholder = '[Episode' + englisch + '] - '
        elif self.filename == 'SJ_Staffeln_Regex]':
            link_placeholder = '[Staffel/RegEx' + englisch + '] - '
        else:
            link_placeholder = '[Staffel' + englisch + '] - '
        try:
            storage = self.db.retrieve_all(title)
        except Exception as e:
            self.log_debug(
                "Fehler bei Datenbankzugriff: %s, Grund: %s" % (e, title))
            return

        if 'added' in storage or 'notdl' in storage:
            self.log_debug(title + " - Release ignoriert (bereits gefunden)")
        else:
            if season and episode:
                download_link = download_link.replace('&_=',
                                                      '&season=' + str(season) + '&episode=' + str(episode) + '&_=')

            download = add_decrypt(title, download_link, self.sf, self.dbfile)
            if download:
                self.db.store(title, 'added')
                log_entry = link_placeholder + title + ' - [SF]'
                self.log_info(log_entry)
                notify(["[Click'n'Load notwendig] - " + log_entry], self.configfile)
                return log_entry

    # ToDo Refactor to content_shows
    def periodical_task(self):
        if not self.sf:
            return self.device

        if self.filename == 'SJ_Serien_Regex':
            if not self.config.get('regex'):
                self.log_debug("Suche für SF-Regex deaktiviert!")
                return self.device
        elif self.filename == 'SJ_Staffeln_Regex':
            if not self.config.get('regex'):
                self.log_debug("Suche für SF-Regex deaktiviert!")
                return self.device
        elif self.filename == 'MB_Staffeln':
            if not self.config.get('crawlseasons'):
                self.log_debug("Suche für SF-Staffeln deaktiviert!")
                return self.device
        if self.empty_list:
            self.log_debug(
                "Liste ist leer. Stoppe Suche für Serien!" + self.listtype)
            return self.device
        try:
            reject = self.config.get("rejectlist").replace(",", "|").lower() if len(
                self.config.get("rejectlist")) > 0 else r"^unmatchable$"
        except TypeError:
            reject = r"^unmatchable$"

        set_sf = self.settings_hash(False)

        header = False
        response = False

        while self.day < 8:
            if self.last_set_sf == set_sf:
                try:
                    delta = (datetime.datetime.now() - datetime.timedelta(days=self.day)).strftime("%Y-%m-%d")
                    response = get_url_headers('https://' + self.sf + '/updates/' + delta, self.configfile,
                                               self.dbfile, self.headers, self.scraper)
                    self.scraper = response[1]
                    response = response[0]
                    if self.filename == "MB_Staffeln" or self.filename == "SJ_Staffeln_Regex":
                        feed = sf_releases_to_feedparser_dict(response.text, "seasons", 'https://' + self.sf, True)
                    else:
                        feed = sf_releases_to_feedparser_dict(response.text, "episodes", 'https://' + self.sf, True)
                except:
                    print(u"SF hat die Feed-API angepasst. Breche Suche ab!")
                    feed = False

                if response:
                    if response.status_code == 304:
                        self.log_debug(
                            "SF-Feed seit letztem Aufruf nicht aktualisiert - breche  Suche ab!")
                        return self.device
                    header = True
            else:
                try:
                    delta = (datetime.datetime.now() - datetime.timedelta(days=self.day)).strftime("%Y-%m-%d")
                    response = get_url('https://' + self.sf + '/updates/' + delta, self.configfile,
                                       self.dbfile, self.scraper)
                    if self.filename == "MB_Staffeln" or self.filename == "SJ_Staffeln_Regex":
                        feed = sf_releases_to_feedparser_dict(response, "seasons",
                                                              'https://' + self.sf,
                                                              True)
                    else:
                        feed = sf_releases_to_feedparser_dict(response, "episodes",
                                                              'https://' + self.sf,
                                                              True)
                except:
                    print(u"SF hat die Feed-API angepasst. Breche Suche ab!")
                    feed = False

            self.day += 1

            if feed and feed.entries:
                first_post_sf = feed.entries[0]
                concat_sf = first_post_sf.title + first_post_sf.published + str(self.settings) + str(self.pattern)
                sha_sf = hashlib.sha256(concat_sf.encode(
                    'ascii', 'ignore')).hexdigest()
            else:
                self.log_debug(
                    "Feed ist leer - breche  Suche ab!")
                return False

            for post in feed.entries:
                concat = post.title + post.published + \
                         str(self.settings) + str(self.pattern)
                sha = hashlib.sha256(concat.encode(
                    'ascii', 'ignore')).hexdigest()
                if sha == self.last_sha_sf:
                    self.log_debug(
                        "Feed ab hier bereits gecrawlt (" + post.title + ") - breche  Suche ab!")
                    break

                series_url = post.series_url
                title = post.title.replace("-", "-")

                if self.filename == 'SJ_Serien_Regex':
                    if self.config.get("regex"):
                        if '.german.' in title.lower():
                            language_id = 1
                        elif self.rsscrawler.get('english'):
                            language_id = 2
                        else:
                            language_id = 0
                        if language_id:
                            m = re.search(self.pattern, title.lower())
                            if not m and "720p" not in title and "1080p" not in title and "2160p" not in title:
                                m = re.search(self.pattern.replace(
                                    "480p", "."), title.lower())
                                self.quality = "480p"
                            if m:
                                if "720p" in title.lower():
                                    self.quality = "720p"
                                if "1080p" in title.lower():
                                    self.quality = "1080p"
                                if "2160p" in title.lower():
                                    self.quality = "2160p"
                                m = re.search(reject, title.lower())
                                if m:
                                    self.log_debug(
                                        title + " - Release durch Regex gefunden (trotz rejectlist-Einstellung)")
                                title = re.sub(r'\[.*\] ', '', post.title)
                                self.parse_download(series_url, title, language_id)
                        else:
                            self.log_debug(
                                "%s - Englische Releases deaktiviert" % title)

                    else:
                        continue
                elif self.filename == 'SJ_Staffeln_Regex':
                    if self.config.get("regex"):
                        if '.german.' in title.lower():
                            language_id = 1
                        elif self.rsscrawler.get('english'):
                            language_id = 2
                        else:
                            language_id = 0
                        if language_id:
                            m = re.search(self.pattern, title.lower())
                            if not m and "720p" not in title and "1080p" not in title and "2160p" not in title:
                                m = re.search(self.pattern.replace(
                                    "480p", "."), title.lower())
                                self.quality = "480p"
                            if m:
                                if "720p" in title.lower():
                                    self.quality = "720p"
                                if "1080p" in title.lower():
                                    self.quality = "1080p"
                                if "2160p" in title.lower():
                                    self.quality = "2160p"
                                m = re.search(reject, title.lower())
                                if m:
                                    self.log_debug(
                                        title + " - Release durch Regex gefunden (trotz rejectlist-Einstellung)")
                                title = re.sub(r'\[.*\] ', '', post.title)
                                self.parse_download(series_url, title, language_id)
                        else:
                            self.log_debug(
                                "%s - Englische Releases deaktiviert" % title)

                    else:
                        continue
                else:
                    if self.config.get("quality") != '480p':
                        m = re.search(self.pattern, title.lower())
                        if m:
                            if '.german.' in title.lower():
                                language_id = 1
                            elif self.rsscrawler.get('english'):
                                language_id = 2
                            else:
                                language_id = 0
                            if language_id:
                                mm = re.search(self.quality, title.lower())
                                if mm:
                                    mmm = re.search(reject, title.lower())
                                    if mmm:
                                        self.log_debug(
                                            title + " - Release ignoriert (basierend auf rejectlist-Einstellung)")
                                        continue
                                    if self.rsscrawler.get("surround"):
                                        if not re.match(r'.*\.(DTS|DD\+*51|DD\+*71|AC3\.5\.*1)\..*', title):
                                            self.log_debug(
                                                title + " - Release ignoriert (kein Mehrkanalton)")
                                            continue
                                    try:
                                        storage = self.db.retrieve_all(title)
                                    except Exception as e:
                                        self.log_debug(
                                            "Fehler bei Datenbankzugriff: %s, Grund: %s" % (e, title))
                                        return self.device
                                    if 'added' in storage:
                                        self.log_debug(
                                            title + " - Release ignoriert (bereits gefunden)")
                                        continue
                                    self.parse_download(series_url, title, language_id)
                            else:
                                self.log_debug(
                                    "%s - Englische Releases deaktiviert" % title)

                        else:
                            m = re.search(self.pattern, title.lower())
                            if m:
                                if '.german.' in title.lower():
                                    language_id = 1
                                elif self.rsscrawler.get('english'):
                                    language_id = 2
                                else:
                                    language_id = 0
                                if language_id:
                                    if "720p" in title.lower() or "1080p" in title.lower() or "2160p" in title.lower():
                                        continue
                                    mm = re.search(reject, title.lower())
                                    if mm:
                                        self.log_debug(
                                            title + " Release ignoriert (basierend auf rejectlist-Einstellung)")
                                        continue
                                    if self.rsscrawler.get("surround"):
                                        if not re.match(r'.*\.(DTS|DD\+*51|DD\+*71|AC3\.5\.*1)\..*', title):
                                            self.log_debug(
                                                title + " - Release ignoriert (kein Mehrkanalton)")
                                            continue
                                    title = re.sub(r'\[.*\] ', '', post.title)
                                    try:
                                        storage = self.db.retrieve_all(title)
                                    except Exception as e:
                                        self.log_debug(
                                            "Fehler bei Datenbankzugriff: %s, Grund: %s" % (e, title))
                                        return self.device
                                    if 'added' in storage:
                                        self.log_debug(
                                            title + " - Release ignoriert (bereits gefunden)")
                                        continue
                                    self.parse_download(series_url, title, language_id)
                                else:
                                    self.log_debug(
                                        "%s - Englische Releases deaktiviert" % title)

        if set_sf:
            new_set_sf = self.settings_hash(True)
            if set_sf == new_set_sf:
                self.cdc.delete("SFSet-" + self.filename)
                self.cdc.store("SFSet-" + self.filename, set_sf)
                self.cdc.delete("SF-" + self.filename)
                self.cdc.store("SF-" + self.filename, sha_sf)

        if header and response:
            self.cdc.delete("SFHeaders-" + self.filename)
            self.cdc.store("SFHeaders-" + self.filename, response.headers['date'])

        return self.device
