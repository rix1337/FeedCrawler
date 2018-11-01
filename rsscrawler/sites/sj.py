# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337
# Enthält Code von:
# https://github.com/Gutz-Pilz/pyLoad-stuff/blob/master/SJ.py

import hashlib
import re

import feedparser
from bs4 import BeautifulSoup

from rsscrawler.common import decode_base64
from rsscrawler.myjd import myjd_download
from rsscrawler.notifiers import notify
from rsscrawler.rssconfig import RssConfig
from rsscrawler.rssdb import ListDb
from rsscrawler.rssdb import RssDb
from rsscrawler.url import get_url
from rsscrawler.url import get_url_headers


class SJ:
    def __init__(self, configfile, dbfile, device, logging, filename, internal_name):
        self._INTERNAL_NAME = internal_name
        self.configfile = configfile
        self.dbfile = dbfile
        self.device = device
        self.config = RssConfig(self._INTERNAL_NAME, self.configfile)
        self.device = device
        self.rsscrawler = RssConfig("RSScrawler", self.configfile)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.filename = filename
        self.db = RssDb(self.dbfile, 'rsscrawler')
        self.quality = self.config.get("quality")
        self.hoster = re.compile(self.config.get("hoster"))
        self.cdc = RssDb(self.dbfile, 'cdc')
        self.last_set_sj = self.cdc.retrieve("SJSet-" + self.filename)
        self.last_sha_sj = self.cdc.retrieve("SJ-" + self.filename)
        self.headers = {'If-Modified-Since': str(self.cdc.retrieve("SJHeaders-" + self.filename))}
        settings = ["quality", "rejectlist", "regex", "hoster"]
        self.settings = []
        self.settings.append(self.rsscrawler.get("english"))
        self.settings.append(self.rsscrawler.get("surround"))
        for s in settings:
            self.settings.append(self.config.get(s))

        self.empty_list = False
        if self.filename == 'SJ_Staffeln_Regex':
            self.level = 3
        elif self.filename == 'MB_Staffeln':
            self.seasonssource = self.config.get('seasonssource').lower()
            self.level = 2
        elif self.filename == 'SJ_Serien_Regex':
            self.level = 1
        else:
            self.level = 0

        self.pattern = r'^\[.*\] (' + "|".join(self.get_series_list(self.filename, self.level)).lower() + ')'

    def get_series_list(self, liste, series_type):
        loginfo = ""
        if series_type == 1:
            loginfo = " (RegEx)"
        elif series_type == 2:
            loginfo = " (Staffeln)"
        elif series_type == 3:
            loginfo = " (Staffeln/RegEx)"
        cont = ListDb(self.dbfile, liste).retrieve()
        titles = []
        if cont:
            for title in cont:
                if title:
                    title = title.replace(" ", ".")
                    titles.append(title)
        if not titles:
            self.log_debug(
                "Liste ist leer. Stoppe Suche für Serien!" + loginfo)
            if series_type == 1:
                self.empty_list = True
            elif series_type == 2:
                self.empty_list = True
            else:
                self.empty_list = True
        return titles

    def range_checkr(self, link, title, language_ok):
        englisch = False
        if language_ok == 2:
            englisch = True
        if self.filename == 'MB_Staffeln':
            season = re.search(r"\.s\d", title.lower())
            if not season:
                self.log_debug(title + " - Release ist keine Staffel")
                return
            if not self.config.get("seasonpacks"):
                staffelpack = re.search(r"s\d.*(-|\.).*s\d", title.lower())
                if staffelpack:
                    self.log_debug(
                        "%s - Release ignoriert (Staffelpaket)" % title)
                    return
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
                        added_items.append(self.range_parse(link, title1, englisch, title))
                    else:
                        title1 = title_cut[0][0] + "0" + \
                                 str(count) + ".*" + title_cut[0][-1].replace(
                            "(", ".*").replace(")", ".*").replace("+", ".*")
                        added_items.append(self.range_parse(link, title1, englisch, title))
                return added_items
            except ValueError as e:
                self.log_error("Fehler in Variablenwert: " + str(e))
        return self.parse_download(link, title, englisch)

    def range_parse(self, series_url, search_title, englisch, fallback_title):
        req_page = get_url(series_url, self.configfile, self.dbfile)
        soup = BeautifulSoup(req_page, 'lxml')
        try:
            titles = soup.findAll(text=re.compile(search_title))
            added_items = []
            if not titles:
                titles = soup.findAll(text=re.compile(fallback_title))
            for title in titles:
                if self.quality != '480p' and self.quality in title:
                    added_items.append(self.parse_download(series_url, title, englisch))
                if self.quality == '480p' and not (('.720p.' in title) or ('.1080p.' in title) or ('.2160p.' in title)):
                    added_items.append(self.parse_download(series_url, title, englisch))
            return added_items
        except re.error as e:
            self.log_error('Konstantenfehler: %s' % e)

    def parse_download(self, series_url, search_title, englisch):
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
            if self.filename == 'MB_Staffeln':
                valid = re.search(self.seasonssource, search_title.lower())
            else:
                valid = True
            if valid:
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
                    return self.send_package(search_title, links, englisch)
            else:
                self.log_debug(search_title + " - Release hat falsche Quelle")

    def send_package(self, title, links, englisch_info):
        englisch = ""
        if englisch_info:
            englisch = "Englisch - "
        if self.filename == 'SJ_Serien_Regex':
            link_placeholder = '[Episode/RegEx] - ' + englisch
        elif self.filename == 'SJ_Serien':
            link_placeholder = '[Episode] - ' + englisch
        elif self.filename == 'SJ_Staffeln_Regex]':
            link_placeholder = '[Staffel/RegEx] - ' + englisch
        else:
            link_placeholder = '[Staffel] - ' + englisch
        try:
            storage = self.db.retrieve(title)
        except Exception as e:
            self.log_debug(
                "Fehler bei Datenbankzugriff: %s, Grund: %s" % (e, title))
            return
        if storage == 'added':
            self.log_debug(title + " - Release ignoriert (bereits gefunden)")
        else:
            if myjd_download(self.configfile, self.device, title, "RSScrawler", links,
                             decode_base64("c2VyaWVuanVua2llcy5vcmc=")):
                self.db.store(title, 'added')
                log_entry = link_placeholder + title
                self.log_info(log_entry)
                notify([log_entry], self.configfile)
                return log_entry

    def periodical_task(self):

        if self.filename == 'SJ_Serien_Regex':
            if not self.config.get('regex'):
                self.log_debug("Suche für SJ-Regex deaktiviert!")
                return
        elif self.filename == 'SJ_Staffeln_Regex':
            if not self.config.get('regex'):
                self.log_debug("Suche für SJ-Regex deaktiviert!")
                return
        elif self.filename == 'MB_Staffeln':
            if not self.config.get('crawlseasons'):
                self.log_debug("Suche für SJ-Staffeln deaktiviert!")
                return
        if self.empty_list:
            return
        try:
            reject = self.config.get("rejectlist").replace(",", "|").lower() if len(
                self.config.get("rejectlist")) > 0 else r"^unmatchable$"
        except TypeError:
            reject = r"^unmatchable$"

        set_sj = str(self.settings) + str(self.pattern)
        set_sj = hashlib.sha256(set_sj.encode(
            'ascii', 'ignore')).hexdigest()

        header = False
        if self.last_set_sj == set_sj:
            if self.filename == "MB_Staffeln" or self.filename == "SJ_Staffeln_Regex":
                try:
                    response = get_url_headers(
                        decode_base64('aHR0cDovL3Nlcmllbmp1bmtpZXMub3JnL3htbC9mZWVkcy9zdGFmZmVsbi54bWw='),
                        self.configfile,
                        self.dbfile,
                        self.headers)
                    feed = feedparser.parse(response.content)
                except:
                    response = False
            else:
                try:
                    response = get_url_headers(
                        decode_base64('aHR0cDovL3Nlcmllbmp1bmtpZXMub3JnL3htbC9mZWVkcy9lcGlzb2Rlbi54bWw='),
                        self.configfile,
                        self.dbfile,
                        self.headers)
                    feed = feedparser.parse(response.content)
                except:
                    response = False
            if response:
                if response.status_code == 304:
                    self.log_debug(
                        "SJ-Feed seit letztem Aufruf nicht aktualisiert - breche  Suche ab!")
                    return
                header = True
        else:
            if self.filename == "MB_Staffeln" or self.filename == "SJ_Staffeln_Regex":
                feed = feedparser.parse(get_url(
                    decode_base64('aHR0cDovL3Nlcmllbmp1bmtpZXMub3JnL3htbC9mZWVkcy9zdGFmZmVsbi54bWw='), self.configfile,
                    self.dbfile))
            else:
                feed = feedparser.parse(get_url(
                    decode_base64('aHR0cDovL3Nlcmllbmp1bmtpZXMub3JnL3htbC9mZWVkcy9lcGlzb2Rlbi54bWw='), self.configfile,
                    self.dbfile))
            response = False

        first_post_sj = feed.entries[0]
        concat_sj = first_post_sj.title + first_post_sj.published + \
                    str(self.settings) + str(self.pattern)
        sha_sj = hashlib.sha256(concat_sj.encode(
            'ascii', 'ignore')).hexdigest()

        for post in feed.entries:
            if not post.link:
                continue

            concat = post.title + post.published + \
                     str(self.settings) + str(self.pattern)
            sha = hashlib.sha256(concat.encode(
                'ascii', 'ignore')).hexdigest()
            if sha == self.last_sha_sj:
                self.log_debug(
                    "Feed ab hier bereits gecrawlt (" + post.title + ") - breche  Suche ab!")
                break

            link = post.link
            title = post.title

            if self.filename == 'SJ_Serien_Regex':
                if self.config.get("regex"):
                    if '[DEUTSCH]' in title or '[TV-FILM]' in title:
                        language_ok = 1
                    elif self.rsscrawler.get('english'):
                        language_ok = 2
                    else:
                        language_ok = 0
                    if language_ok:
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
                            self.range_checkr(link, title, language_ok)
                    else:
                        self.log_debug(
                            "%s - Englische Releases deaktiviert" % title)

                else:
                    continue
            elif self.filename == 'SJ_Staffeln_Regex':
                if self.config.get("regex"):
                    if '[DEUTSCH]' in title:
                        language_ok = 1
                    elif self.rsscrawler.get('english'):
                        language_ok = 2
                    else:
                        language_ok = 0
                    if language_ok:
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
                            self.range_checkr(link, title, language_ok)
                    else:
                        self.log_debug(
                            "%s - Englische Releases deaktiviert" % title)

                else:
                    continue
            else:
                if self.config.get("quality") != '480p':
                    m = re.search(self.pattern, title.lower())
                    if m:
                        if '[DEUTSCH]' in title:
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
                                    return
                                if storage == 'added':
                                    self.log_debug(
                                        title + " - Release ignoriert (bereits gefunden)")
                                    continue
                                self.range_checkr(link, title, language_ok)
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
                                    return
                                if storage == 'added':
                                    self.log_debug(
                                        title + " - Release ignoriert (bereits gefunden)")
                                    continue
                                self.range_checkr(link, title, language_ok)
                            else:
                                self.log_debug(
                                    "%s - Englische Releases deaktiviert" % title)

        self.cdc.delete("SJSet-" + self.filename)
        self.cdc.store("SJSet-" + self.filename, set_sj)
        self.cdc.delete("SJ-" + self.filename)
        self.cdc.store("SJ-" + self.filename, sha_sj)
        if header and response:
            self.cdc.delete("SJHeaders-" + self.filename)
            self.cdc.store("SJHeaders-" + self.filename, response.headers['Last-Modified'])
