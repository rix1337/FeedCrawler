# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337
# Enthält Code von:
# https://github.com/Gutz-Pilz/pyLoad-stuff/blob/master/SJ.py

import hashlib
import re

from bs4 import BeautifulSoup

from rsscrawler.common import decode_base64
from rsscrawler.fakefeed import dj_content_to_soup
from rsscrawler.myjd import myjd_download
from rsscrawler.notifiers import notify
from rsscrawler.rssconfig import RssConfig
from rsscrawler.rssdb import ListDb
from rsscrawler.rssdb import RssDb
from rsscrawler.url import get_url
from rsscrawler.url import get_url_headers


class DJ:
    def __init__(self, configfile, dbfile, device, logging, filename, internal_name):
        self._INTERNAL_NAME = internal_name
        self.configfile = configfile
        self.dbfile = dbfile
        self.device = device
        self.config = RssConfig(self._INTERNAL_NAME, self.configfile)
        self.rsscrawler = RssConfig("RSScrawler", self.configfile)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.filename = filename
        self.db = RssDb(self.dbfile, 'rsscrawler')
        self.quality = self.config.get("quality")
        self.hoster = re.compile(self.config.get("hoster"))
        self.cdc = RssDb(self.dbfile, 'cdc')
        self.last_set_dj = self.cdc.retrieve("DJSet-" + self.filename)
        self.last_sha_dj = self.cdc.retrieve("DJ-" + self.filename)
        self.headers = {'If-Modified-Since': str(self.cdc.retrieve("DJHeaders-" + self.filename))}
        settings = ["quality", "rejectlist", "regex", "hoster"]
        self.settings = []
        self.settings.append(self.rsscrawler.get("english"))
        self.settings.append(self.rsscrawler.get("surround"))
        for s in settings:
            self.settings.append(self.config.get(s))

        self.empty_list = False
        if self.filename == 'DJ_Dokus_Regex':
            self.level = 1
        else:
            self.level = 0

        self.pattern = r'^(' + "|".join(self.get_series_list(self.filename, self.level)).lower() + ')'
        self.listtype = ""

    def settings_hash(self, refresh):
        if refresh:
            settings = ["quality", "rejectlist", "regex", "hoster"]
            self.settings = []
            self.settings.append(self.rsscrawler.get("english"))
            self.settings.append(self.rsscrawler.get("surround"))
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

    def range_checkr(self, link, title, language_ok, genre):
        englisch = False
        if language_ok == 2:
            englisch = True
        pattern = re.match(
            r".*S\d{1,2}E\d{1,2}-(?:S\d{1,2}E|E|)\d{1,2}.*", title)
        if pattern:
            added_items = []
            range0 = re.sub(
                r".*S\d{1,2}E(\d{1,2}-(?:S\d{1,2}E|E|)\d{1,2}).*", r"\1", title)
            number1 = re.sub(
                r"(\d{1,2})-(?:S\d{1,2}E|E|)\d{1,2}", r"\1", range0)
            number2 = re.sub(
                r"\d{1,2}-(?:S\d{1,2}E|E|)(\d{1,2})", r"\1", range0)
            title_cut = re.findall(
                r"(.*S\d{1,2}E)(\d{1,2}-(?:S\d{1,2}E|E|)\d{1,2})(.*)", title)
            check = title_cut[0][1]
            if "E" in check:
                check = re.sub(r"(S\d{1,2}E|E)", "", check)
                title_cut = [(title_cut[0][0], check, title_cut[0][2])]
            title = title.replace("(", ".*").replace(")",
                                                     ".*").replace("+", ".*")
            try:
                for count in range(int(number1), (int(number2) + 1)):
                    nr = re.match(r"E\d{1,2}", str(count))
                    if nr:
                        title1 = title_cut[0][0] + \
                                 str(count) + ".*" + title_cut[0][-1].replace(
                            "(", ".*").replace(")", ".*").replace("+", ".*")
                        added_items.append(self.range_parse(link, title1, englisch, title, genre))
                    else:
                        title1 = title_cut[0][0] + "0" + \
                                 str(count) + ".*" + title_cut[0][-1].replace(
                            "(", ".*").replace(")", ".*").replace("+", ".*")
                        added_items.append(self.range_parse(link, title1, englisch, title, genre))
                return added_items
            except ValueError as e:
                self.log_error("Fehler in Variablenwert: " + str(e))
        return self.parse_download(link, title, englisch, genre)

    def range_parse(self, series_url, search_title, englisch, fallback_title, genre):
        req_page = get_url(series_url, self.configfile, self.dbfile)
        soup = BeautifulSoup(req_page, 'lxml')
        try:
            titles = soup.findAll(text=re.compile(search_title))
            added_items = []
            if not titles:
                titles = soup.findAll(text=re.compile(fallback_title))
            for title in titles:
                if self.quality != '480p' and self.quality in title:
                    added_items.append(self.parse_download(series_url, title, englisch, genre))
                if self.quality == '480p' and not (('.720p.' in title) or ('.1080p.' in title) or ('.2160p.' in title)):
                    added_items.append(self.parse_download(series_url, title, englisch, genre))
            return added_items
        except re.error as e:
            self.log_error('Konstantenfehler: %s' % e)

    def parse_download(self, series_url, search_title, englisch, genre):
        req_page = get_url(series_url, self.configfile, self.dbfile)

        soup = BeautifulSoup(req_page, 'lxml')
        escape_brackets = search_title.replace(
            "(", ".*").replace(")", ".*").replace("+", ".*")
        title = soup.find(text=re.compile(escape_brackets))
        if not title:
            try:
                episode = re.findall(r'\.S\d{1,3}(E\d{1,3}.*)\.German', escape_brackets).pop()
                escape_brackets_pack = escape_brackets.replace(episode, "")
                title = soup.find(text=re.compile(escape_brackets_pack))
            except:
                title = False
                self.log_debug(search_title + " - Kein Link gefunden")
        if title:
            url_hosters = re.findall(
                r'<a href="([^"\'>]*)".+?\| (.+?)<', str(title.parent.parent))
            links = []
            for url_hoster in url_hosters:
                if re.match(self.hoster, url_hoster[1]):
                    links.append(url_hoster[0])
            if not links:
                self.log_debug(
                    "%s - Release ignoriert (kein passender Link gefunden)" % search_title)
            else:
                return self.send_package(search_title, links, englisch, genre)

    def send_package(self, title, links, englisch_info, genre):
        if genre == "Doku":
            genre = ""
        else:
            genre = "/" + genre
        englisch = ""
        if englisch_info:
            englisch = "Englisch - "
        if self.filename == 'DJ_Dokus_Regex':
            link_placeholder = '[Doku' + genre + '/RegEx] - ' + englisch
        else:
            link_placeholder = '[Doku' + genre + '] - ' + englisch
        try:
            storage = self.db.retrieve(title)
        except Exception as e:
            self.log_debug(
                "Fehler bei Datenbankzugriff: %s, Grund: %s" % (e, title))
            return
        if storage == 'added':
            self.log_debug(title + " - Release ignoriert (bereits gefunden)")
        else:
            self.device = myjd_download(self.configfile, self.device, title, "RSScrawler", links,
                                        decode_base64("ZG9rdWp1bmtpZXMub3Jn"))
            if self.device:
                self.db.store(title, 'added')
                log_entry = link_placeholder + title
                self.log_info(log_entry)
                notify([log_entry], self.configfile)
                return log_entry

    def periodical_task(self):
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
        if self.last_set_dj == set_dj:
            try:
                response = get_url_headers(
                    decode_base64('aHR0cDovL2Rva3VqdW5raWVzLm9yZy8='),
                    self.configfile,
                    self.dbfile,
                    self.headers)
                feed = dj_content_to_soup(response.content)
            except:
                response = False
                feed = False
            if response:
                if response.status_code == 304:
                    self.log_debug(
                        "DJ-Feed seit letztem Aufruf nicht aktualisiert - breche  Suche ab!")
                    return self.device
                header = True
        else:
            feed = dj_content_to_soup(
                get_url(decode_base64('aHR0cDovL2Rva3VqdW5raWVzLm9yZy8='), self.configfile, self.dbfile))
            response = False

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
            if not post.link:
                continue

            concat = post.title + post.published + str(self.settings) + str(self.pattern)
            sha = hashlib.sha256(concat.encode(
                'ascii', 'ignore')).hexdigest()
            if sha == self.last_sha_dj:
                self.log_debug(
                    "Feed ab hier bereits gecrawlt (" + post.title + ") - breche  Suche ab!")
                break

            link = post.link
            title = post.title
            genre = post.genre

            if self.filename == 'DJ_Dokus_Regex':
                if self.config.get("regex"):
                    if '[DEUTSCH]' in title or '[TV-FILM]' in title:
                        language_ok = 1
                    elif self.rsscrawler.get('english'):
                        language_ok = 2
                    else:
                        language_ok = 0
                    if language_ok:
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
                            self.range_checkr(link, title, language_ok, genre)
                    else:
                        self.log_debug(
                            "%s - Englische Releases deaktiviert" % title)

                else:
                    continue
            else:
                if self.config.get("quality") != '480p':
                    m = re.search(self.pattern, title.lower())
                    if m:
                        if 'german' in title.lower():
                            language_ok = 1
                        elif self.rsscrawler.get('english'):
                            language_ok = 2
                        else:
                            language_ok = 0
                        if language_ok:
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
                                title = re.sub(r'\[.*\] ', '', post.title)
                                try:
                                    storage = self.db.retrieve(title)
                                except Exception as e:
                                    self.log_debug(
                                        "Fehler bei Datenbankzugriff: %s, Grund: %s" % (e, title))
                                    return self.device
                                if storage == 'added':
                                    self.log_debug(
                                        title + " - Release ignoriert (bereits gefunden)")
                                    continue
                                self.range_checkr(link, title, language_ok, genre)
                        else:
                            self.log_debug(
                                "%s - Englische Releases deaktiviert" % title)

                    else:
                        m = re.search(self.pattern, title.lower())
                        if m:
                            if '[DEUTSCH]' in title:
                                language_ok = 1
                            elif self.rsscrawler.get('english'):
                                language_ok = 2
                            else:
                                language_ok = 0
                            if language_ok:
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
                                    storage = self.db.retrieve(title)
                                except Exception as e:
                                    self.log_debug(
                                        "Fehler bei Datenbankzugriff: %s, Grund: %s" % (e, title))
                                    return self.device
                                if storage == 'added':
                                    self.log_debug(
                                        title + " - Release ignoriert (bereits gefunden)")
                                    continue
                                self.range_checkr(link, title, language_ok, genre)
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
