# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import hashlib
import json
import re

from rsscrawler.fakefeed import j_releases_to_feedparser_dict
from rsscrawler.notifiers import notify
from rsscrawler.rsscommon import add_decrypt
from rsscrawler.rsscommon import check_hoster
from rsscrawler.rsscommon import check_valid_release
from rsscrawler.rssconfig import RssConfig
from rsscrawler.rssdb import ListDb
from rsscrawler.rssdb import RssDb
from rsscrawler.url import get_url
from rsscrawler.url import get_url_headers


class DJ:
    def __init__(self, configfile, dbfile, device, logging, scraper, filename, internal_name):
        self._INTERNAL_NAME = internal_name
        self.configfile = configfile
        self.dbfile = dbfile
        self.device = device

        self.hostnames = RssConfig('Hostnames', self.configfile)
        self.dj = self.hostnames.get('dj')

        self.config = RssConfig(self._INTERNAL_NAME, self.configfile)
        self.rsscrawler = RssConfig("RSScrawler", self.configfile)
        self.hosters = RssConfig("Hosters", configfile).get_section()
        self.hoster_fallback = self.config.get("hoster_fallback")
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.scraper = scraper
        self.filename = filename
        self.db = RssDb(self.dbfile, 'rsscrawler')
        self.quality = self.config.get("quality")
        self.cdc = RssDb(self.dbfile, 'cdc')
        self.last_set_dj = self.cdc.retrieve("DJSet-" + self.filename)
        self.last_sha_dj = self.cdc.retrieve("DJ-" + self.filename)
        self.headers = {'If-Modified-Since': str(self.cdc.retrieve("DJHeaders-" + self.filename))}
        settings = ["quality", "rejectlist", "regex", "hoster_fallback"]
        self.settings = []
        self.settings.append(self.rsscrawler.get("english"))
        self.settings.append(self.rsscrawler.get("surround"))
        self.settings.append(self.hosters)
        for s in settings:
            self.settings.append(self.config.get(s))

        self.empty_list = False
        if self.filename == 'DJ_Dokus_Regex':
            self.level = 1
        else:
            self.level = 0

        self.pattern = r'^(' + "|".join(self.get_series_list(self.filename, self.level)).lower() + ')'
        self.listtype = ""

        self.day = 0

    def settings_hash(self, refresh):
        if refresh:
            settings = ["quality", "rejectlist", "regex", "hoster_fallback"]
            self.settings = []
            self.settings.append(self.rsscrawler.get("english"))
            self.settings.append(self.rsscrawler.get("surround"))
            self.settings.append(self.hosters)
            for s in settings:
                self.settings.append(self.config.get(s))
            self.pattern = r'^\[.*\] (' + "|".join(self.get_series_list(self.filename, self.level)).lower() + ')'
        set_dj = str(self.settings) + str(self.pattern)
        return hashlib.sha256(set_dj.encode('ascii', 'ignore')).hexdigest()

    def get_series_list(self, liste, series_type):
        if series_type == 1:
            self.listtype = " (RegEx)"
        cont = ListDb(self.dbfile, liste).retrieve()
        titles = []
        if cont:
            for title in cont:
                if title:
                    title = title.replace(" ", ".")
                    titles.append(title)
        if not titles:
            self.empty_list = True
        return titles

    def parse_download(self, series_url, title, language_id):
        if not check_valid_release(title, False, False, self.dbfile):
            self.log_debug(title + u" - Release ignoriert (Gleiche oder bessere Quelle bereits vorhanden)")
            return
        try:
            series_info = get_url(series_url, self.configfile, self.dbfile)
            series_id = re.findall(r'data-mediaid="(.*?)"', series_info)[0]
            api_url = 'https://' + self.dj + '/api/media/' + series_id + '/releases'

            response = get_url(api_url, self.configfile, self.dbfile, self.scraper)
            seasons = json.loads(response)
            for season in seasons:
                season = seasons[season]
                for item in season['items']:
                    if item['name'] == title:
                        valid = False
                        for hoster in item['hoster']:
                            if check_hoster(hoster, self.configfile):
                                valid = True
                        if not valid and not self.hoster_fallback:
                            storage = self.db.retrieve_all(title)
                            if 'added' not in storage and 'notdl' not in storage:
                                wrong_hoster = '[DJ/Hoster fehlt] - ' + title
                                if 'wrong_hoster' not in storage:
                                    self.log_info(wrong_hoster)
                                    self.db.store(title, 'wrong_hoster')
                                    notify([wrong_hoster], self.configfile)
                                else:
                                    self.log_debug(wrong_hoster)
                        else:
                            return self.send_package(title, series_url, language_id)
        except:
            print(u"DJ hat die Doku-API angepasst. Breche Download-Prüfung ab!")

    def send_package(self, title, series_url, language_id):
        englisch = ""
        if language_id == 2:
            englisch = "Englisch - "
        if self.filename == 'DJ_Dokus_Regex':
            link_placeholder = '[Doku/RegEx] - ' + englisch
        else:
            link_placeholder = '[Doku] - ' + englisch
        try:
            storage = self.db.retrieve_all(title)
        except Exception as e:
            self.log_debug(
                "Fehler bei Datenbankzugriff: %s, Grund: %s" % (e, title))
            return

        if 'added' in storage or 'notdl' in storage:
            self.log_debug(title + " - Release ignoriert (bereits gefunden)")
        else:
            download = add_decrypt(title, series_url, self.dj, self.dbfile)
            if download:
                self.db.store(title, 'added')
                log_entry = link_placeholder + title + ' - [DJ]'
                self.log_info(log_entry)
                notify(["[Click'n'Load notwendig] - " + log_entry], self.configfile)
                return log_entry

    def periodical_task(self):
        if not self.dj:
            return self.device

        if self.filename == 'DJ_Dokus_Regex':
            if not self.config.get('regex'):
                self.log_debug("Suche für DJ-Regex deaktiviert!")
                return self.device
        if self.empty_list:
            self.log_debug(
                "Liste ist leer. Stoppe Suche für Dokus!" + self.listtype)
            return self.device
        try:
            reject = self.config.get("rejectlist").replace(",", "|").lower() if len(
                self.config.get("rejectlist")) > 0 else r"^unmatchable$"
        except TypeError:
            reject = r"^unmatchable$"

        set_dj = self.settings_hash(False)

        header = False
        response = False

        while self.day < 8:
            if self.last_set_dj == set_dj:
                try:
                    response = get_url_headers('https://' + self.dj + '/api/releases/latest/' + str(self.day),
                                               self.configfile, self.dbfile, self.headers, self.scraper)
                    self.scraper = response[1]
                    response = response[0]
                    feed = j_releases_to_feedparser_dict(response.text, "episodes", 'https://' + self.dj, False)
                except:
                    print(u"DJ hat die Feed-API angepasst. Breche Suche ab!")
                    feed = False

                if response:
                    if response.status_code == 304:
                        self.log_debug(
                            "DJ-Feed seit letztem Aufruf nicht aktualisiert - breche  Suche ab!")
                        return self.device
                    header = True
            else:
                try:
                    response = get_url('https://' + self.dj + '/api/releases/latest/' + str(self.day),
                                       self.configfile, self.dbfile, self.scraper)
                    feed = j_releases_to_feedparser_dict(response, "episodes", 'https://' + self.dj, False)
                except:
                    print(u"DJ hat die Feed-API angepasst. Breche Suche ab!")
                    feed = False

            self.day += 1

            if feed and feed.entries:
                first_post_dj = feed.entries[0]
                concat_dj = first_post_dj.title + first_post_dj.published + str(self.settings) + str(self.pattern)
                sha_dj = hashlib.sha256(concat_dj.encode(
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
                if sha == self.last_sha_dj:
                    self.log_debug(
                        "Feed ab hier bereits gecrawlt (" + post.title + ") - breche  Suche ab!")
                    break

                series_url = post.series_url
                title = post.title.replace("-", "-")

                if self.filename == 'DJ_Dokus_Regex':
                    if self.config.get("regex"):
                        if '.german.' in title.lower():
                            language_id = 1
                        elif self.rsscrawler.get('english'):
                            language_id = 2
                        else:
                            language_id = 0
                        if language_id:
                            m = re.search(self.pattern, title.lower())
                            if not m and not "720p" in title and not "1080p" in title and not "2160p" in title:
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

        if set_dj:
            new_set_dj = self.settings_hash(True)
            if set_dj == new_set_dj:
                self.cdc.delete("DJSet-" + self.filename)
                self.cdc.store("DJSet-" + self.filename, set_dj)
                self.cdc.delete("DJ-" + self.filename)
                self.cdc.store("DJ-" + self.filename, sha_dj)
        if header and response:
            self.cdc.delete("DJHeaders-" + self.filename)
            self.cdc.store("DJHeaders-" + self.filename, response.headers['Last-Modified'])

        return self.device
