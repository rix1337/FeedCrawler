# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import hashlib
import re

from rsscrawler.common import add_decrypt
from rsscrawler.db import ListDb
from rsscrawler.notifiers import notify
from rsscrawler.url import get_url
from rsscrawler.url import get_url_headers


def get_series_list(self):
    cont = ListDb(self.dbfile, self.filename).retrieve()
    titles = []
    if cont:
        for title in cont:
            if title:
                title = title.replace(" ", ".")
                titles.append(title)
    return titles


def settings_hash(self, refresh):
    if refresh:
        self.settings = []
        self.settings.append(self.rsscrawler.get("english"))
        self.settings.append(self.rsscrawler.get("surround"))
        self.settings.append(self.hosters)
        for s in self.settings_array:
            self.settings.append(self.config.get(s))
        self.pattern = r'^(' + "|".join(get_series_list(self)).lower() + ')'
    set = str(self.settings) + str(self.pattern)
    return hashlib.sha256(set.encode('ascii', 'ignore')).hexdigest()


def send_package(self, title, series_url, language_id):
    englisch = ""
    if language_id == 2:
        englisch = "/Englisch"
    if self.filename == 'SJ_Serien_Regex':
        link_placeholder = '[Episode/RegEx' + englisch + '] - '
    elif self.filename == 'SJ_Serien':
        link_placeholder = '[Episode' + englisch + '] - '
    elif self.filename == 'SJ_Staffeln_Regex]':
        link_placeholder = '[Staffel/RegEx' + englisch + '] - '
    elif self.filename == 'MB_Staffeln':
        link_placeholder = '[Staffel' + englisch + '] - '
    elif self.filename == 'DJ_Dokus_Regex':
        link_placeholder = '[Doku/RegEx' + englisch + '] - '
    elif self.filename == 'DJ_Dokus':
        link_placeholder = '[Doku' + englisch + '] - '
    try:
        storage = self.db.retrieve_all(title)
    except Exception as e:
        self.log_debug(
            "Fehler bei Datenbankzugriff: %s, Grund: %s" % (e, title))
        return

    if 'added' in storage or 'notdl' in storage:
        self.log_debug(title + " - Release ignoriert (bereits gefunden)")
    else:
        download = add_decrypt(title, series_url, self.j, self.dbfile)
        if download:
            self.db.store(title, 'added')
            log_entry = link_placeholder + title + ' - [' + self._INTERNAL_NAME + ']'
            self.log_info(log_entry)
            notify(["[Click'n'Load notwendig] - " + log_entry], self.configfile)
            return log_entry


def periodical_task(self):
    if not self.j:
        return self.device

    if self.filename == 'SJ_Serien_Regex':
        if not self.config.get('regex'):
            self.log_debug("Suche für " + self._INTERNAL_NAME + "-Regex deaktiviert!")
            return self.device
    elif self.filename == 'SJ_Staffeln_Regex':
        if not self.config.get('regex'):
            self.log_debug("Suche für " + self._INTERNAL_NAME + "-Regex deaktiviert!")
            return self.device
    elif self.filename == 'MB_Staffeln':
        if not self.config.get('crawlseasons'):
            self.log_debug("Suche für " + self._INTERNAL_NAME + "-Staffeln deaktiviert!")
            return self.device
    elif self.filename == 'DJ_Dokus_Regex':
        if not self.config.get('regex'):
            self.log_debug("Suche für DJ-Regex deaktiviert!")
            return self.device

    if self.empty_list:
        self.log_debug(
            "Liste ist leer. Stoppe Suche für " + self.mediatype + "!" + self.listtype)
        return self.device
    try:
        reject = self.config.get("rejectlist").replace(",", "|").lower() if len(
            self.config.get("rejectlist")) > 0 else r"^unmatchable$"
    except TypeError:
        reject = r"^unmatchable$"

    set = settings_hash(self, False)

    header = False
    response = False

    while self.day < 8:
        if self.last_set == set:
            try:
                response = get_url_headers('https://' + self.j + '/api/releases/latest/' + str(self.day),
                                           self.configfile,
                                           self.dbfile, self.headers, self.scraper)
                self.scraper = response[1]
                response = response[0]
                if self.filename == "MB_Staffeln" or self.filename == "SJ_Staffeln_Regex":
                    feed = self.get_feed_method(response.text, "seasons", 'https://' + self.j, True)
                else:
                    feed = self.get_feed_method(response.text, "episodes", 'https://' + self.j, True)
            except:
                print(self._INTERNAL_NAME + u" hat die Feed-API angepasst. Breche Suche ab!")
                feed = False

            if response:
                if response.status_code == 304:
                    self.log_debug(
                        self._INTERNAL_NAME + "-Feed seit letztem Aufruf nicht aktualisiert - breche  Suche ab!")
                    return self.device
                header = True
        else:
            try:
                response = get_url('https://' + self.j + '/api/releases/latest/' + str(self.day), self.configfile,
                                   self.dbfile, self.scraper)
                if self.filename == "MB_Staffeln" or self.filename == "SJ_Staffeln_Regex":
                    feed = self.get_feed_method(response, "seasons",
                                                'https://' + self.j,
                                                True)
                else:
                    feed = self.get_feed_method(response, "episodes",
                                                'https://' + self.j,
                                                True)
            except:
                print(u"DJ hat die Feed-API angepasst. Breche Suche ab!")
                feed = False

        self.day += 1

        if feed and feed.entries:
            first_post_j = feed.entries[0]
            concat_j = first_post_j.title + first_post_j.published + str(self.settings) + str(self.pattern)
            sha_j = hashlib.sha256(concat_j.encode(
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
            if sha == self.last_sha_j:
                self.log_debug(
                    "Feed ab hier bereits gecrawlt (" + post.title + ") - breche  Suche ab!")
                break

            series_url = post.series_url
            title = post.title.replace("-", "-")

            if self.filename == 'SJ_Serien_Regex' or self.filename == 'DJ_Dokus_Regex':
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
                            to_download = self.parse_download_method(self, series_url, title, language_id)
                            if to_download:
                                send_package(self, to_download[0], to_download[1], to_download[2])
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
                            to_download = self.parse_download_method(self, series_url, title, language_id)
                            if to_download:
                                send_package(self, to_download[0], to_download[1], to_download[2])
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
                                to_download = self.parse_download_method(self, series_url, title, language_id)
                                if to_download:
                                    send_package(self, to_download[0], to_download[1], to_download[2])
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
                                to_download = self.parse_download_method(self, series_url, title, language_id)
                                if to_download:
                                    send_package(self, to_download[0], to_download[1], to_download[2])
                            else:
                                self.log_debug(
                                    "%s - Englische Releases deaktiviert" % title)

    if set:
        new_set = settings_hash(self, True)
        if set == new_set:
            self.cdc.delete(self._INTERNAL_NAME + "Set-" + self.filename)
            self.cdc.store(self._INTERNAL_NAME + "Set-" + self.filename, set)
            self.cdc.delete(self._INTERNAL_NAME + "-" + self.filename)
            self.cdc.store(self._INTERNAL_NAME + "-" + self.filename, sha_j)

    if header and response:
        self.cdc.delete(self._INTERNAL_NAME + "Headers-" + self.filename)
        self.cdc.store(self._INTERNAL_NAME + "Headers-" + self.filename, response.headers['date'])

    return self.device
