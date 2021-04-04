# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337

import datetime
import hashlib
import re

from feedcrawler.common import add_decrypt
from feedcrawler.db import ListDb
from feedcrawler.notifiers import notify
from feedcrawler.sites.shared.internal_feed import dw_mirror
from feedcrawler.url import get_url
from feedcrawler.url import get_url_headers


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
        if self._INTERNAL_NAME == "DJ":
            settings = ["quality", "rejectlist", "regex", "hoster_fallback"]
        else:
            settings = ["quality", "rejectlist", "regex", "hevc_retail", "retail_only", "hoster_fallback"]
        self.settings = []
        self.settings.append(self.rsscrawler.get("english"))
        self.settings.append(self.rsscrawler.get("surround"))
        self.settings.append(self.rsscrawler.get("prefer_dw_mirror"))
        self.settings.append(self.hosters)
        for s in settings:
            self.settings.append(self.config.get(s))
        self.pattern = r'^(' + "|".join(get_series_list(self)).lower() + ')'
    current_set = str(self.settings) + str(self.pattern)
    return hashlib.sha256(current_set.encode('ascii', 'ignore')).hexdigest()


def feed_url(self):
    if self._INTERNAL_NAME == "SJ" or self._INTERNAL_NAME == "DJ":
        url = 'https://' + self.url + '/api/releases/latest/' + str(self.day)
        return url
    elif self._INTERNAL_NAME == "SF":
        delta = (datetime.datetime.now() - datetime.timedelta(days=self.day)).strftime("%Y-%m-%d")
        url = 'https://' + self.url + '/updates/' + delta
        return url
    elif self._INTERNAL_NAME == "DWs":
        url = 'https://' + self.url + "/downloads/hauptkategorie/serien/order/zeit/sort/D/seite/" + str(
            self.day + 1) + "/"
        return url
    else:
        return False


def send_package(self, title, link, language_id, season, episode, site):
    englisch = ''
    if language_id == 2:
        englisch = '/Englisch'
    if self.filename == 'SJ_Serien':
        link_placeholder = '[Episode' + englisch + '] - '
    elif self.filename == 'SJ_Serien_Regex':
        link_placeholder = '[Episode/RegEx' + englisch + '] - '
    elif self.filename == 'SJ_Staffeln_Regex':
        link_placeholder = '[Staffel/RegEx' + englisch + '] - '
    elif self.filename == 'MB_Staffeln':
        link_placeholder = '[Staffel' + englisch + '] - '
    elif self.filename == 'DJ_Dokus':
        link_placeholder = '[Doku] - ' + englisch
    elif self.filename == 'DJ_Dokus_Regex':
        link_placeholder = '[Doku/RegEx] - ' + englisch
    else:
        return
    try:
        storage = self.db.retrieve_all(title)
    except Exception as e:
        self.log_debug(
            "Fehler bei Datenbankzugriff: %s, Grund: %s" % (e, title))

    if 'added' in storage or 'notdl' in storage:
        self.log_debug(title + " - Release ignoriert (bereits gefunden)")
    else:
        if season and episode:
            link = link.replace('&_=', '&season=' + str(season) + '&episode=' + str(episode) + '&_=')
        download = add_decrypt(title, link, self.url, self.dbfile)
        if download:
            self.db.store(title, 'added')
            log_entry = link_placeholder + title + ' - [' + site + ']'
            self.log_info(log_entry)
            notify(["[Click'n'Load notwendig] - " + log_entry], self.configfile)
            return log_entry


def periodical_task(self):
    if not self.url:
        return self.device

    if self.filename == 'SJ_Serien_Regex':
        if not self.config.get('regex'):
            self.log_debug("Suche für " + self._SITE + "-Regex deaktiviert!")
            return self.device
    elif self.filename == 'SJ_Staffeln_Regex':
        if not self.config.get('regex'):
            self.log_debug("Suche für " + self._SITE + "-Regex deaktiviert!")
            return self.device
    elif self.filename == 'MB_Staffeln':
        if not self.config.get('crawlseasons'):
            self.log_debug("Suche für " + self._SITE + "-Staffeln deaktiviert!")
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

    current_set = settings_hash(self, False)
    sha = False

    header = False
    response = False

    while self.day < 8:
        if self.last_set == current_set:
            try:
                url = feed_url(self)
                if url:
                    response = get_url_headers(url, self.configfile, self.dbfile, self.headers, self.scraper)
                    self.scraper = response[1]
                    response = response[0]
                    if self.filename == "MB_Staffeln" or self.filename == "SJ_Staffeln_Regex":
                        feed = self.get_feed_method(response.text, "seasons", 'https://' + self.url, True)
                    else:
                        feed = self.get_feed_method(response.text, "episodes", 'https://' + self.url, True)
                else:
                    feed = False
            except:
                print(self._SITE + u" hat die Feed-API angepasst. Breche Suche ab!")
                feed = False

            if response:
                if response.status_code == 304:
                    self.log_debug(
                        self._SITE + "-Feed seit letztem Aufruf nicht aktualisiert - breche  Suche ab!")
                    return self.device
                header = True
        else:
            try:
                url = feed_url(self)
                if url:
                    response = get_url(url, self.configfile, self.dbfile, self.scraper)
                    if self.filename == "MB_Staffeln" or self.filename == "SJ_Staffeln_Regex":
                        feed = self.get_feed_method(response, "seasons", 'https://' + self.url, True)
                    else:
                        feed = self.get_feed_method(response, "episodes", 'https://' + self.url, True)
                else:
                    feed = False
            except:
                print(self._SITE + u" hat die Feed-API angepasst. Breche Suche ab!")
                feed = False

        self.day += 1

        if feed and feed.entries:
            first_post = feed.entries[0]
            concat = first_post.title + first_post.published + str(self.settings) + str(self.pattern)
            sha = hashlib.sha256(concat.encode(
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
            if sha == self.last_sha:
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
                            package = self.parse_download_method(self, series_url, title, language_id)
                            if package:
                                title = package[0]
                                site = self._SITE
                                download_link = False
                                if self.prefer_dw_mirror and "DW" not in site:
                                    download_links = dw_mirror(self, title)
                                    if download_links:
                                        download_link = download_links[0]
                                        site = "DW/" + site
                                if not download_link:
                                    download_link = package[1]
                                language_id = package[2]
                                season = package[3]
                                episode = package[4]
                                send_package(self, title, download_link, language_id, season, episode, site)
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
                            package = self.parse_download_method(self, series_url, title, language_id)
                            if package:
                                title = package[0]
                                site = self._SITE
                                download_link = False
                                if self.prefer_dw_mirror and "DW" not in site:
                                    download_links = dw_mirror(self, title)
                                    if download_links:
                                        download_link = download_links[0]
                                        site = "DW/" + site
                                if not download_link:
                                    download_link = package[1]
                                language_id = package[2]
                                season = package[3]
                                episode = package[4]
                                send_package(self, title, download_link, language_id, season, episode, site)
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
                                package = self.parse_download_method(self, series_url, title, language_id)
                                if package:
                                    title = package[0]
                                    site = self._SITE
                                    download_link = False
                                    if self.prefer_dw_mirror and "DW" not in site:
                                        download_links = dw_mirror(self, title)
                                        if download_links:
                                            download_link = download_links[0]
                                            site = "DW/" + site
                                    if not download_link:
                                        download_link = package[1]
                                    language_id = package[2]
                                    season = package[3]
                                    episode = package[4]
                                    send_package(self, title, download_link, language_id, season, episode, site)
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
                                package = self.parse_download_method(self, series_url, title, language_id)
                                if package:
                                    title = package[0]
                                    site = self._SITE
                                    download_link = False
                                    if self.prefer_dw_mirror and "DW" not in site:
                                        download_links = dw_mirror(self, title)
                                        if download_links:
                                            download_link = download_links[0]
                                            site = "DW/" + site
                                    if not download_link:
                                        download_link = package[1]
                                    language_id = package[2]
                                    season = package[3]
                                    episode = package[4]
                                    send_package(self, title, download_link, language_id, season, episode, site)
                            else:
                                self.log_debug(
                                    "%s - Englische Releases deaktiviert" % title)

    if current_set and sha:
        new_set = settings_hash(self, True)
        if current_set == new_set:
            self.cdc.delete(self._INTERNAL_NAME + "Set-" + self.filename)
            self.cdc.store(self._INTERNAL_NAME + "Set-" + self.filename, current_set)
            self.cdc.delete(self._INTERNAL_NAME + "-" + self.filename)
            self.cdc.store(self._INTERNAL_NAME + "-" + self.filename, sha)

    if header and response:
        self.cdc.delete(self._INTERNAL_NAME + "Headers-" + self.filename)
        self.cdc.store(self._INTERNAL_NAME + "Headers-" + self.filename, response.headers['date'])

    return self.device
