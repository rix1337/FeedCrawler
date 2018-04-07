# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337
# Enthält Code von:
# https://github.com/zapp-brannigan/
# https://github.com/Gutz-Pilz/pyLoad-stuff/blob/master/SJ.py
# Beschreibung:
# RSScrawler erstellt .crawljobs für den JDownloader.

"""RSScrawler.

Usage:
  RSScrawler.py [--testlauf]
                [--ersatzblogs]
                [--docker]
                [--port=<PORT>]
                [--jd-pfad="<JDPATH>"]
                [--log-level=<LOGLEVEL>]

Options:
  --testlauf                Einmalige Ausführung von RSScrawler
  --ersatzblogs             Erweitert die Suche um weitere Blogs um Ausfälle zu überbrücken.
  --docker                  Sperre Pfad und Port auf Docker-Standardwerte (um falsche Einstellungen zu vermeiden)
  --port=<PORT>             Legt den Port des Webservers fest
  --jd-pfad="<JDPFAD>"      Legt den Pfad von JDownloader fest um nicht die RSScrawler.ini direkt bearbeiten zu müssen
  --log-level=<LOGLEVEL>    Legt fest, wie genau geloggt wird (CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET )
"""

import version
version = version.getVersion()

from docopt import docopt
import feedparser
import re
import urllib2
import codecs
from bs4 import BeautifulSoup as bs
import cfscrape
import time
import sys
import signal
import socket
import logging
from logging import handlers
import os
from multiprocessing import Process
from dateutil import parser
from datetime import datetime
import warnings
import traceback

from output import Unbuffered
from output import CutLog
from rssconfig import RssConfig
from rssdb import RssDb
from notifiers import notify
from url import checkURL
from url import getURL
import common
import files
from web import start


def web_server(port, docker, jd, log_level, log_file, log_format):
    start(port, docker, jd, log_level, log_file, log_format)


def crawler(jdpath, rssc, log_level, log_file, log_format):
    global added_items
    added_items = []
    global jdownloaderpath
    jdownloaderpath = jdpath
    global rsscrawler
    rsscrawler = rssc

    sys.stdout = Unbuffered(sys.stdout)

    console = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter(log_format)
    console.setFormatter(CutLog(log_format))

    logfile = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=100000, backupCount=5)
    logfile.setFormatter(formatter)

    logger = logging.getLogger('')
    logger.addHandler(logfile)
    logger.addHandler(console)
    logger.setLevel(log_level)

    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    warnings.simplefilter("ignore", UnicodeWarning)

    log_debug = logging.debug

    search_pool = [
        YT(),
        DD(),
        SJ(filename='SJ_Serien', internal_name='SJ'),
        SJ(filename='SJ_Serien_Regex', internal_name='SJ'),
        SJ(filename='SJ_Staffeln_Regex', internal_name='SJ'),
        SJ(filename='MB_Staffeln', internal_name='MB'),
        MB(filename='MB_Regex'),
        MB(filename='MB_Filme'),
        MB(filename='MB_Staffeln'),
        MB(filename='MB_3D')
    ]
    erweiterter_pool = [
        HW(filename='MB_Regex'),
        HW(filename='MB_Filme'),
        HW(filename='MB_Staffeln'),
        HW(filename='MB_3D'),
        HA(filename='MB_Regex'),
        HA(filename='MB_Filme'),
        HA(filename='MB_Staffeln'),
        HA(filename='MB_3D')
    ]
    arguments = docopt(__doc__, version='RSScrawler')
    if not arguments['--testlauf']:
        while True:
            try:
                checkURL()
                start_time = time.time()
                log_debug("--------Alle Suchfunktion gestartet.--------")
                print(time.strftime("%Y-%m-%d %H:%M:%S") +
                      " - Alle Suchfunktion gestartet.")
                for task in search_pool:
                    task.periodical_task()
                    log_debug("-----------Suchfunktion ausgeführt!-----------")
                if arguments['--ersatzblogs']:
                    for task in erweiterter_pool:
                        task.periodical_task()
                        log_debug(
                            "---------Ersatz-Suchfunktion ausgeführt!---------")
                end_time = time.time()
                total_time = end_time - start_time
                total_unit = " Sekunden"
                if total_time > 60:
                    total_time = total_time / 60
                    total_unit = " Minuten"
                total_time = str(round(total_time, 1)) + total_unit
                notify(added_items)
                log_debug(
                    "-----Alle Suchfunktion ausgeführt (Dauer: " + total_time + ")!-----")
                print(time.strftime("%Y-%m-%d %H:%M:%S") +
                      " - Alle Suchfunktion ausgeführt (Dauer: " + total_time + ")!")
                added_items = []
                time.sleep(int(rsscrawler.get('interval')) * 60)
                log_debug("-------------Wartezeit verstrichen-------------")
            except Exception:
                traceback.print_exc()
    else:
        try:
            checkURL()
            start_time = time.time()
            log_debug("--------Testlauf gestartet.--------")
            print(time.strftime("%Y-%m-%d %H:%M:%S") + " - Testlauf gestartet.")
            for task in search_pool:
                task.periodical_task()
                log_debug("-----------Suchfunktion ausgeführt!-----------")
            for task in erweiterter_pool:
                task.periodical_task()
                log_debug("---------Ersatz-Suchfunktion ausgeführt!---------")
            end_time = time.time()
            total_time = end_time - start_time
            total_unit = " Sekunden"
            if total_time > 60:
                total_time = total_time / 60
                total_unit = " Minuten"
            total_time = str(round(total_time, 1)) + total_unit
            notify(added_items)
            log_debug(
                "---Testlauf ausgeführt (inkl. Ersatz-Suchfunktionen, Dauer: " + total_time + ")!---")
            print(time.strftime("%Y-%m-%d %H:%M:%S") +
                  " - Testlauf ausgeführt (Dauer: " + total_time + ")!")
        except Exception:
            traceback.print_exc()


class YT():
    _INTERNAL_NAME = 'YT'

    def __init__(self):
        self.config = RssConfig(self._INTERNAL_NAME)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.db = RssDb(os.path.join(os.path.dirname(
            sys.argv[0]), "RSScrawler.db"), 'rsscrawler')
        self.youtube = os.path.join(os.path.dirname(
            sys.argv[0]), 'Einstellungen/Listen/YT_Channels.txt')
        self.dictWithNamesAndLinks = {}

    def readInput(self, file):
        if not os.path.isfile(file):
            open(file, "a").close()
            placeholder = open(file, 'w')
            placeholder.write('XXXXXXXXXX')
            placeholder.close()
        try:
            f = codecs.open(file, "rb")
            return f.read().splitlines()
        except:
            self.log_error("Liste nicht gefunden!")

    def periodical_task(self):
        if not self.config.get('youtube'):
            self.log_debug("Suche für YouTube deaktiviert!")
            return
        channels = []
        links = []
        videos = []
        download_link = ""
        self.allInfos = self.readInput(self.youtube)

        for xline in self.allInfos:
            if len(xline) > 0 and not xline.startswith("#"):
                if xline.startswith("XXXXXXXXXX") or self.config.get("youtube") is False:
                    self.log_debug(
                        "Liste enthält Platzhalter. Stoppe Suche für YouTube!")
                    return
                channels.append(xline)

        for channel in channels:
            if 'list=' in channel:
                id_cutter = channel.rfind('list=') + 5
                channel = channel[id_cutter:]
                url = 'https://www.youtube.com/playlist?list=' + channel
                response = getURL(url)
            else:
                url = 'https://www.youtube.com/user/' + channel + '/videos'
                urlc = 'https://www.youtube.com/channel/' + channel + '/videos'
                cnotfound = False
                try:
                    response = getURL(url)
                except urllib2.HTTPError:
                    try:
                        response = getURL(urlc)
                    except urllib2.HTTPError:
                        cnotfound = True
                    if cnotfound:
                        self.log_debug("YouTube-Kanal: " +
                                       channel + " nicht gefunden!")
                        return

            links = re.findall(
                r'VideoRenderer":{"videoId":"(.*?)",".*?simpleText":"(.*?)"}', response)

            maxvideos = int(self.config.get("maxvideos"))
            if maxvideos < 1:
                self.log_debug("Anzahl zu suchender YouTube-Videos (" +
                               str(maxvideos) + ") zu gering. Suche stattdessen 1 Video!")
                maxvideos = 1
            elif maxvideos > 50:
                self.log_debug("Anzahl zu suchender YouTube-Videos (" +
                               str(maxvideos) + ") zu hoch. Suche stattdessen maximal 50 Videos!")
                maxvideos = 50

            for link in links[:maxvideos]:
                if len(link[0]) > 10:
                    videos.append(
                        [link[0].encode('ascii', 'replace'), link[1], channel])

        for video in videos:
            channel = video[2]
            video_title = video[1].replace("&amp;", "&").replace("&gt;", ">").replace(
                "&lt;", "<").replace('&quot;', '"').replace("&#39;", "'").replace("\u0026", "&")
            video = video[0]
            download_link = 'https://www.youtube.com/watch?v=' + video
            if download_link:
                if self.db.retrieve(video) == 'added':
                    self.log_debug(
                        "[%s] - YouTube-Video ignoriert (bereits gefunden)" % video)
                else:
                    ignore = "|".join(["%s" % p for p in self.config.get("ignore").lower().split(
                        ',')]) if self.config.get("ignore") else r"^unmatchable$"
                    ignorevideo = re.search(ignore, video_title.lower())
                    if ignorevideo:
                        self.log_debug(video_title + " (" + channel + ") " +
                                       "[" + video + "] - YouTube-Video ignoriert (basierend auf ignore-Einstellung)")
                        continue
                    common.write_crawljob_file(
                        video,
                        "YouTube/" + channel,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler"
                    )
                    self.db.store(
                        video,
                        'added'
                    )
                    log_entry = '[YouTube] - ' + video_title + ' (' + channel + ') - <a href="' + download_link + '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                        video + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                    self.log_info(log_entry)
                    added_items.append(log_entry)


class DD():
    _INTERNAL_NAME = 'DD'

    def __init__(self):
        self.config = RssConfig(self._INTERNAL_NAME)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.db = RssDb(os.path.join(os.path.dirname(
            sys.argv[0]), "RSScrawler.db"), 'rsscrawler')

    def periodical_task(self):
        feeds = self.config.get("feeds")
        if feeds:
            feeds = feeds.replace(" ", "").split(',')
            for feed in feeds:
                feed = feedparser.parse(feed)
                for post in feed.entries:
                    key = post.title.replace(" ", ".")

                    epoch = datetime(1970, 1, 1)
                    current_epoch = int(time.time())
                    published_format = "%Y-%m-%d %H:%M:%S+00:00"
                    published_timestamp = str(parser.parse(post.published))
                    published_epoch = int((datetime.strptime(
                        published_timestamp, published_format) - epoch).total_seconds())
                    if (current_epoch - 1800) > published_epoch:
                        feed_link = post.link
                        link_pool = post.summary
                        unicode_links = re.findall(r'(http.*)', link_pool)
                        links = []
                        for link in unicode_links:
                            links.append(str(link))
                        if self.db.retrieve(key) == 'added':
                            self.log_debug(
                                "%s - Release ignoriert (bereits gefunden)" % key)
                        else:
                            common.write_crawljob_file(
                                key,
                                key,
                                links,
                                jdownloaderpath + "/folderwatch",
                                "RSScrawler"
                            )
                            self.db.store(
                                key,
                                'added'
                            )
                            log_entry = '[DD.tv/<b>Englisch</b>] ' + key + ' - <a href="' + feed_link + \
                                '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                                key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                            self.log_info(log_entry)
                            added_items.append(log_entry)
                    else:
                        self.log_debug(
                            "%s - Release ist jünger als 30 Minuten und wird ignoriert." % key)


class SJ():
    def __init__(self, filename, internal_name):
        self._INTERNAL_NAME = internal_name
        self.config = RssConfig(self._INTERNAL_NAME)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.filename = filename
        self.db = RssDb(os.path.join(os.path.dirname(
            sys.argv[0]), "RSScrawler.db"), 'rsscrawler')
        self.search_list = os.path.join(os.path.dirname(
            sys.argv[0]), 'Einstellungen/Listen/{}.txt'.format(self.filename))
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

    def periodical_task(self):
        if self.filename == "MB_Staffeln" or self.filename == "SJ_Staffeln_Regex":
            feed = feedparser.parse(
                'aHR0cDovL3Nlcmllbmp1bmtpZXMub3JnL3htbC9mZWVkcy9zdGFmZmVsbi54bWw='.decode('base64'))
        else:
            feed = feedparser.parse(
                'aHR0cDovL3Nlcmllbmp1bmtpZXMub3JnL3htbC9mZWVkcy9lcGlzb2Rlbi54bWw='.decode('base64'))

        self.pattern = "|".join(self.getSeriesList(
            self.search_list, self.level)).lower()

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
        self.quality = self.config.get("quality")
        self.hoster = rsscrawler.get("hoster")

        for post in feed.entries:
            if not post.link:
                continue

            link = post.link
            title = post.title

            if self.filename == 'SJ_Serien_Regex':
                if self.config.get("regex"):
                    if '[DEUTSCH]' in title:
                        language_ok = 1
                    elif rsscrawler.get('english'):
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
                    elif rsscrawler.get('english'):
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
                        elif rsscrawler.get('english'):
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
                                if rsscrawler.get("surround"):
                                    if not re.match(r'.*\.(DTS|DD\+*51|DD\+*71|AC3\.5\.*1)\..*', title):
                                        self.log_debug(
                                            title + " - Release ignoriert (kein Mehrkanalton)")
                                        continue
                                title = re.sub(r'\[.*\] ', '', post.title)
                                self.range_checkr(link, title, language_ok)
                        else:
                            self.log_debug(
                                "%s - Englische Releases deaktiviert" % title)

                    else:
                        m = re.search(self.pattern, title.lower())
                        if m:
                            if '[DEUTSCH]' in title:
                                language_ok = 1
                            elif rsscrawler.get('english'):
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
                                if rsscrawler.get("surround"):
                                    if not re.match(r'.*\.(DTS|DD\+*51|DD\+*71|AC3\.5\.*1)\..*', title):
                                        self.log_debug(
                                            title + " - Release ignoriert (kein Mehrkanalton)")
                                        continue
                                title = re.sub(r'\[.*\] ', '', post.title)
                                self.range_checkr(link, title, language_ok)
                            else:
                                self.log_debug(
                                    "%s - Englische Releases deaktiviert" % title)

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
            r".*S\d{1,2}E\d{1,2}-(?:S\d{1,2}E|E)\d{1,2}.*", title)
        if pattern:
            range0 = re.sub(
                r".*S\d{1,2}E(\d{1,2}-(?:S\d{1,2}E|E)\d{1,2}).*", r"\1", title)
            number1 = re.sub(
                r"(\d{1,2})-(?:S\d{1,2}E|E)\d{1,2}", r"\1", range0)
            number2 = re.sub(
                r"\d{1,2}-(?:S\d{1,2}E|E)(\d{1,2})", r"\1", range0)
            title_cut = re.findall(
                r"(.*S\d{1,2}E)(\d{1,2}-(?:S\d{1,2}E|E)\d{1,2})(.*)", title)
            check = title_cut[0][1]
            if "E" in check:
                check = re.sub(r"(S\d{1,2}E|E)", "", check)
                title_cut = [(title_cut[0][0], check, title_cut[0][2])]
            try:
                for count in range(int(number1), (int(number2) + 1)):
                    NR = re.match(r"\d{1,2}", str(count))
                    if NR:
                        title1 = title_cut[0][0] + \
                            str(count) + ".*" + title_cut[0][-1]
                        self.range_parse(link, title1, englisch)
                    else:
                        title1 = title_cut[0][0] + "0" + \
                            str(count) + ".*" + title_cut[0][-1]
                        self.range_parse(link, title1, englisch)
            except ValueError as e:
                logging.error("Fehler in Variablenwert: %s" % e.message)
        else:
            self.parse_download(link, title, englisch)

    def range_parse(self, series_url, search_title, englisch):
        req_page = getURL(series_url)
        soup = bs(req_page, 'lxml')
        try:
            titles = soup.findAll(text=re.compile(search_title))
            for title in titles:
                if self.quality != '480p' and self.quality in title:
                    self.parse_download(series_url, title, englisch)
                if self.quality == '480p' and not (('.720p.' in title) or ('.1080p.' in title) or ('.2160p.' in title)):
                    self.parse_download(series_url, title, englisch)
        except re.error as e:
            self.log_error('Konstantenfehler: %s' % e)

    def parse_download(self, series_url, search_title, englisch):
        req_page = getURL(series_url)
        soup = bs(req_page, 'lxml')
        escape_brackets = search_title.replace(
            "(", ".*").replace(")", ".*").replace("+", ".*")
        title = soup.find(text=re.compile(escape_brackets))
        if title:
            valid = False
            if self.filename == 'MB_Staffeln':
                valid = re.search(self.seasonssource, title.lower())
            else:
                valid = True
            if valid:
                url_hosters = re.findall(
                    r'<a href="([^"\'>]*)".+?\| (.+?)<', str(title.parent.parent))
                for url_hoster in url_hosters:
                    if self.hoster.lower() in url_hoster[1]:
                        self.send_package(title, url_hoster[0], englisch)
            else:
                self.log_debug(title + " - Release hat falsche Quelle")

    def send_package(self, title, link, englisch_info):
        englisch = ""
        if englisch_info:
            englisch = "/Englisch"
        if self.filename == 'SJ_Serien_Regex':
            link_placeholder = '[Episode/RegEx' + englisch + '] - '
        elif self.filename == 'SJ_Serien':
            link_placeholder = '[Episode' + englisch + '] - '
        elif self.filename == 'SJ_Staffeln_Regex':
            link_placeholder = '[Staffel/RegEx' + englisch + '] - '
        else:
            link_placeholder = '[Staffel' + englisch + '] - '
        try:
            storage = self.db.retrieve(title)
        except Exception as e:
            self.log_debug(
                "Fehler bei Datenbankzugriff: %s, Grund: %s" % (e, title))
        if storage == 'added':
            self.log_debug(title + " - Release ignoriert (bereits gefunden)")
        else:
            common.write_crawljob_file(
                title, title, link, jdownloaderpath + "/folderwatch", "RSScrawler")
            self.db.store(title, 'added')
            log_entry = link_placeholder + title + ' - <a href="' + link + \
                '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                title + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
            self.log_info(log_entry)
            added_items.append(log_entry)

    def getSeriesList(self, file, type):
        loginfo = ""
        if type == 1:
            loginfo = " (RegEx)"
        elif type == 2:
            loginfo = " (Staffeln)"
        elif type == 3:
            loginfo = " (Staffeln/RegEx)"

        if not os.path.isfile(file):
            open(file, "a").close()
            placeholder = open(file, 'w')
            placeholder.write('XXXXXXXXXX')
            placeholder.close()
        try:
            titles = []
            f = codecs.open(file, "rb", "utf-8")
            for title in f.read().splitlines():
                if len(title) == 0:
                    continue
                title = title.replace(" ", ".")
                titles.append(title)
            f.close()
            if titles[0] == "XXXXXXXXXX":
                self.log_debug(
                    "Liste enthält Platzhalter. Stoppe Suche für Serien!" + loginfo)
                if type == 1:
                    self.empty_list = True
                elif type == 2:
                    self.empty_list = True
                else:
                    self.empty_list = True
            return titles
        except UnicodeError:
            self.log_error(
                "ANGEHALTEN, ungültiges Zeichen in Serien" + loginfo + "Liste!")
        except IOError:
            self.log_error("ANGEHALTEN, Serien" + loginfo +
                           "-Liste nicht gefunden!")
        except Exception, e:
            self.log_error("Unbekannter Fehler: %s" % e)


class MB():
    _INTERNAL_NAME = 'MB'
    FEED_URL = "aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZy9mZWVkLw==".decode('base64')
    SUBSTITUTE = r"[&#\s/]"

    def __init__(self, filename):
        rsscrawler = RssConfig('RSScrawler')
        self.config = RssConfig(self._INTERNAL_NAME)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.filename = filename
        self.db = RssDb(os.path.join(os.path.dirname(
            sys.argv[0]), "RSScrawler.db"), 'rsscrawler')
        self.search_list = os.path.join(os.path.dirname(
            sys.argv[0]), 'Einstellungen/Listen/{}.txt'.format(self.filename))
        self.hoster = rsscrawler.get("hoster")
        self.dictWithNamesAndLinks = {}
        self.empty_list = False

    def readInput(self, file):
        if not os.path.isfile(file):
            open(file, "a").close()
            placeholder = open(file, 'w')
            placeholder.write('XXXXXXXXXX')
            placeholder.close()
        try:
            f = codecs.open(file, "rb")
            return f.read().splitlines()
        except:
            self.log_error("Liste nicht gefunden!")

    def getPatterns(self, patterns, **kwargs):
        if patterns == ["XXXXXXXXXX"]:
            self.log_debug(
                "Liste enthält Platzhalter. Stoppe Suche für Filme!")
            self.empty_list = True
        if kwargs:
            return {line: (kwargs['quality'], kwargs['rg'], kwargs['sf']) for line in patterns}
        return {x: (x) for x in patterns}

    def searchLinks(self, feed):
        if self.empty_list:
            return
        ignore = "|".join(
            [r"\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if self.config.get("ignore") else r"^unmatchable$"

        for key in self.allInfos:
            s = re.sub(self.SUBSTITUTE, ".", "^" + key).lower()
            for post in feed.entries:
                found = re.search(s, post.title.lower())
                if found:
                    found = re.search(ignore, post.title.lower())
                    if found:
                        self.log_debug(
                            "%s - Release ignoriert (basierend auf ignore-Einstellung)" % post.title)
                        continue
                    if rsscrawler.get("surround"):
                        if not re.match(r'.*\.(DTS|DD\+*51|DD\+*71|AC3\.5\.*1)\..*', post.title):
                            self.log_debug(
                                post.title + " - Release ignoriert (kein Mehrkanalton)")
                            continue
                    ss = self.allInfos[key][0].lower()
                    if self.filename == 'MB_Filme':
                        if ss == "480p":
                            if "720p" in post.title.lower() or "1080p" in post.title.lower() or "1080i" in post.title.lower() or "2160p" in post.title.lower():
                                continue
                            found = True
                        else:
                            found = re.search(ss, post.title.lower())
                        if found:
                            sss = r"[\.-]+" + self.allInfos[key][1].lower()
                            found = re.search(sss, post.title.lower())
                            if self.allInfos[key][2]:
                                found = all([word in post.title.lower()
                                             for word in self.allInfos[key][2]])
                            if found:
                                episode = re.search(
                                    r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', post.title.lower())
                                if episode:
                                    self.log_debug(
                                        "%s - Release ignoriert (Serienepisode)" % post.title)
                                    continue
                                yield (post.title, [post.link], key)
                    elif self.filename == 'MB_3D':
                        if '.3d.' in post.title.lower():
                            if self.config.get('crawl3d') and (
                                    "1080p" in post.title.lower() or "1080i" in post.title.lower()):
                                if not self.config.get("crawl3dtype"):
                                    c3d_type = "hsbs"
                                else:
                                    c3d_type = self.config.get("crawl3dtype")
                                if c3d_type == "hsbs":
                                    if re.match(r'.*\.(H-OU|HOU)\..*', post.title):
                                        self.log_debug(
                                            "%s - Release ignoriert (Falsches 3D-Format)" % post.title)
                                        continue
                                elif c3d_type == "hou":
                                    if not re.match(r'.*\.(H-OU|HOU)\..*', post.title):
                                        self.log_debug(
                                            "%s - Release ignoriert (Falsches 3D-Format)" % post.title)
                                        continue
                                found = True
                            else:
                                continue
                        if found:
                            sss = r"[\.-]+" + self.allInfos[key][1].lower()
                            found = re.search(sss, post.title.lower())
                            if self.allInfos[key][2]:
                                found = all([word in post.title.lower()
                                             for word in self.allInfos[key][2]])
                            if found:
                                episode = re.search(
                                    r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', post.title.lower())
                                if episode:
                                    self.log_debug(
                                        "%s - Release ignoriert (Serienepisode)" % post.title)
                                    continue
                                yield (post.title, [post.link], key)

                    elif self.filename == 'MB_Staffeln':
                        validsource = re.search(self.config.get(
                            "seasonssource"), post.title.lower())
                        if not validsource:
                            self.log_debug(
                                post.title + " - Release hat falsche Quelle")
                            continue
                        if not ".complete." in post.title.lower():
                            self.log_debug(
                                post.title + " - Staffel noch nicht komplett")
                            continue
                        season = re.search(r"\.s\d", post.title.lower())
                        if not season:
                            self.log_debug(
                                post.title + " - Release ist keine Staffel")
                            continue
                        if not self.config.get("seasonpacks"):
                            staffelpack = re.search(
                                r"s\d.*(-|\.).*s\d", post.title.lower())
                            if staffelpack:
                                self.log_debug(
                                    "%s - Release ignoriert (Staffelpaket)" % post.title)
                                continue
                        ss = self.allInfos[key][0].lower()

                        if ss == "480p":
                            if "720p" in post.title.lower() or "1080p" in post.title.lower() or "1080i" in post.title.lower() or "2160p" in post.title.lower():
                                continue
                            found = True
                        else:
                            found = re.search(ss, post.title.lower())
                        if found:
                            sss = r"[\.-]+" + self.allInfos[key][1].lower()
                            found = re.search(sss, post.title.lower())

                            if self.allInfos[key][2]:
                                found = all([word in post.title.lower()
                                             for word in self.allInfos[key][2]])
                            if found:
                                episode = re.search(
                                    r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', post.title.lower())
                                if episode:
                                    self.log_debug(
                                        "%s - Release ignoriert (Serienepisode)" % post.title)
                                    continue
                                yield (post.title, [post.link], key)
                    else:
                        yield (post.title, [post.link], key)

    def download_dl(self, title):
        search_title = title.replace(".German.720p.", ".German.DL.1080p.").replace(".German.DTS.720p.", ".German.DTS.DL.1080p.").replace(".German.AC3.720p.", ".German.AC3.DL.1080p.").replace(
            ".German.AC3LD.720p.", ".German.AC3LD.DL.1080p.").replace(".German.AC3.Dubbed.720p.", ".German.AC3.Dubbed.DL.1080p.").split('.x264-', 1)[0].split('.h264-', 1)[0].replace(".", " ").replace(" ", "+")
        search_url = "aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZy9zZWFyY2gv".decode(
            'base64') + search_title + "/feed/rss2/"
        feedsearch_title = title.replace(".German.720p.", ".German.DL.1080p.").replace(".German.DTS.720p.", ".German.DTS.DL.1080p.").replace(".German.AC3.720p.", ".German.AC3.DL.1080p.").replace(
            ".German.AC3LD.720p.", ".German.AC3LD.DL.1080p.").replace(".German.AC3.Dubbed.720p.", ".German.AC3.Dubbed.DL.1080p.").split('.x264-', 1)[0].split('.h264-', 1)[0]
        if not '.dl.' in feedsearch_title.lower():
            self.log_debug(
                "%s - Release ignoriert (nicht zweisprachig, da wahrscheinlich nicht Retail)" % feedsearch_title)
            return False
        for (key, value, pattern) in self.dl_search(feedparser.parse(search_url), feedsearch_title):
            download_link = self._get_download_links(value[0])
            if download_link:
                if "aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZy8yMDEw".decode("base64") in download_link:
                    self.log_debug("Fake-Link erkannt!")
                    return False
                if str(self.db.retrieve(key)) == 'added' or str(self.db.retrieve(key)) == 'dl':
                    self.log_debug(
                        "%s - zweisprachiges Release ignoriert (bereits gefunden)" % key)
                    return True
                elif self.filename == 'MB_Filme':
                    retail = False
                    if self.config.get('cutoff'):
                        if self.config.get('enforcedl'):
                            if common.cutoff(key, '1'):
                                retail = True
                        else:
                            if common.cutoff(key, '0'):
                                retail = True
                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler/Remux"
                    )
                    self.db.store(
                        key,
                        'dl' if self.config.get(
                            'enforcedl') and '.dl.' in key.lower() else 'added'
                    )
                    log_entry = '[Film] - <b>' + ('Retail/' if retail else "") + 'Zweisprachig</b> - ' + key + ' - <a href="' + download_link + \
                        '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                        key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                    self.log_info(log_entry)
                    added_items.append(log_entry)
                    return True
                elif self.filename == 'MB_3D':
                    retail = False
                    if self.config.get('cutoff'):
                        if common.cutoff(key, '2'):
                            retail = True
                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler/3Dcrawler"
                    )
                    self.db.store(
                        key,
                        'dl' if self.config.get(
                            'enforcedl') and '.dl.' in key.lower() else 'added'
                    )
                    log_entry = '[Film] - <b>' + ('Retail/' if retail else "") + '3D/Zweisprachig</b> - ' + key + ' - <a href="' + download_link + \
                        '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                        key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                    self.log_info(log_entry)
                    added_items.append(log_entry)
                    return True
                elif self.filename == 'MB_Regex':
                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler"
                    )
                    self.db.store(
                        key,
                        'dl' if self.config.get(
                            'enforcedl') and '.dl.' in key.lower() else 'added'
                    )
                    log_entry = '[Film/Serie/RegEx] - <b>Zweisprachig</b> - ' + key + ' - <a href="' + download_link + \
                        '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                        key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                    self.log_info(log_entry)
                    added_items.append(log_entry)
                    return True
                else:
                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler/Remux"
                    )
                    self.db.store(
                        key,
                        'dl' if self.config.get(
                            'enforcedl') and '.dl.' in key.lower() else 'added'
                    )
                    log_entry = '[Staffel] - <b>Zweisprachig</b> - ' + key + ' - <a href="' + download_link + \
                        '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                        key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                    self.log_info(log_entry)
                    added_items.append(log_entry)
                    return True

    def dl_search(self, feed, title):
        ignore = "|".join(
            [r"\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if self.config.get("ignore") else r"^unmatchable$"

        s = re.sub(self.SUBSTITUTE, ".", title).lower()
        for post in feed.entries:
            found = re.search(s, post.title.lower())
            if found:
                found = re.search(ignore, post.title.lower())
                if found:
                    self.log_debug(
                        "%s - zweisprachiges Release ignoriert (basierend auf ignore-Einstellung)" % post.title)
                    continue
                yield (post.title, [post.link], title)

    def imdb_search(self, imdb):
        imdbchecked = re.findall(
            r'<title>(.*?)<\/title>\n.*?<link>(.*)<\/link>(?:(?:.*?\n){1,25}).*?[mM][kK][vV].*?(?:|href=.?http(?:|s):\/\/(?:|www\.)imdb\.com\/title\/(tt[0-9]{7,9}).*?)[iI][mM][dD][bB].*?(\d(?:\.|\,)\d)(?:.|.*?)<\/a>', getURL(self.FEED_URL))
        for item in imdbchecked:
            download_title = item[0]
            ignore = "|".join(
                [r"\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if self.config.get("ignore") else r"^unmatchable$"
            found = re.search(ignore, download_title.lower())
            if found:
                self.log_debug(
                    "%s - Release ignoriert (basierend auf ignore-Einstellung)" % download_title)
                continue
            if rsscrawler.get("surround"):
                if not re.match(r'.*\.(DTS|DD\+*51|DD\+*71|AC3\.5\.*1)\..*', download_title):
                    self.log_debug(
                        download_title + " - Release ignoriert (kein Mehrkanalton)")
                    continue
            season = re.search(r'\.S(\d{1,3})(\.|-|E)', download_title)
            if season:
                self.log_debug(
                    "%s - Release ignoriert (IMDB sucht nur Filme)" % download_title)
                continue

            year_in_title = re.findall(r"\.((?:19|20)\d{2})\.", download_title)
            years_in_title = len(year_in_title)
            if years_in_title > 0:
                title_year = year_in_title[years_in_title - 1]
            else:
                title_year = ""

            download_page = self._get_download_links(item[1])

            if len(item[2]) > 0:
                download_imdb = "http://www.imdb.com/title/" + item[2]
            else:
                try:
                    search_title = re.findall(r"(.*?)(?:\.(?:(?:19|20)\d{2})|\.German|\.\d{3,4}p|\.S(?:\d{1,3})\.)", download_title)[0].replace(
                        ".", "+").replace("ae", "ä").replace("oe", "ö").replace("ue", "ü").replace("Ae", "Ä").replace("Oe", "Ö").replace("Ue", "Ü")
                except:
                    break
                search_url = "http://www.imdb.com/find?q=" + search_title
                search_page = getURL(search_url)
                search_results = re.findall(
                    r'<td class="result_text"> <a href="\/title\/(tt[0-9]{7,9})\/\?ref_=fn_al_tt_\d" >(.*?)<\/a>.*? \((\d{4})\)..(.{9})', search_page)
                no_series = False
                total_results = len(search_results)
                if total_results == 0:
                    download_imdb = ""
                else:
                    while total_results > 0:
                        attempt = 0
                        for result in search_results:
                            if result[3] == "TV Series":
                                no_series = False
                                total_results -= 1
                                attempt += 1
                            else:
                                no_series = True
                                download_imdb = "http://www.imdb.com/title/" + \
                                    search_results[attempt][0]
                                title_year = search_results[attempt][2]
                                total_results = 0
                                break
                    if no_series is False:
                        self.log_debug(
                            "%s - Keine passende Film-IMDB-Seite gefunden" % download_title)

            download_score = float(item[3].replace(",", "."))
            score = str(download_score)

            details = ""
            min_year = self.config.get("imdbyear")
            if min_year:
                if len(title_year) > 0:
                    if title_year < min_year:
                        self.log_debug(
                            "%s - Release ignoriert (Film zu alt)" % download_title)
                        continue
                elif len(download_imdb) > 0:
                    details = getURL(download_imdb)
                    if not details:
                        self.log_debug(
                            "%s - Fehler bei Aufruf der IMDB-Seite" % download_title)
                        continue
                    title_year = re.findall(
                        r"<title>(?:.*) \(((?:19|20)\d{2})\) - IMDb<\/title>", details)
                    if not title_year:
                        self.log_debug(
                            "%s - Erscheinungsjahr nicht ermittelbar" % download_title)
                        continue
                    else:
                        title_year = title_year[0]
                    if title_year < min_year:
                        self.log_debug(
                            "%s - Release ignoriert (Film zu alt)" % download_title)
                        continue

            if len(download_imdb) > 0:
                if len(details) == 0:
                    details = getURL(download_imdb)
                if not details:
                    self.log_debug(
                        "%s - Release ignoriert (Film zu alt)" % download_title)
                    continue
                vote_count = re.findall(r'ratingCount">(.*?)<\/span>', details)
                if not vote_count:
                    self.log_debug(
                        "%s - Wertungsanzahl nicht ermittelbar" % download_title)
                    continue
                else:
                    vote_count = vote_count[0].replace(
                        ".", "").replace(",", "")
                if int(vote_count) < 1500:
                    self.log_debug(
                        download_title + " - Release ignoriert (Weniger als 1500 IMDB-Votes: " + vote_count + ")")
                    continue

            if download_score > imdb:
                ss = self.config.get('quality')
                if '.3d.' not in download_title.lower():
                    if ss == "480p":
                        if "720p" in download_title.lower() or "1080p" in download_title.lower() or "1080i" in download_title.lower() or "2160p" in download_title.lower():
                            continue
                        found = True
                    else:
                        found = re.search(ss, download_title.lower())
                    if found:
                        episode = re.search(
                            r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', download_title.lower())
                        if episode:
                            self.log_debug(
                                "%s - Release ignoriert (Serienepisode)" % download_title)
                            continue
                        self.download_imdb(
                            download_title, download_page, score, download_imdb, details)
                    else:
                        self.log_debug(
                            "%s - Release ignoriert (falsche Aufloesung)" % download_title)
                else:
                    if not self.config.get('crawl3d'):
                        self.log_debug(
                            "%s - Release ignoriert (3D-Suche deaktiviert)" % download_title)
                        return
                    if self.config.get('crawl3d') and ("1080p" in download_title.lower() or "1080i" in download_title.lower()):
                        if not self.config.get("crawl3dtype"):
                            c3d_type = "hsbs"
                        else:
                            c3d_type = self.config.get("crawl3dtype")
                        if c3d_type == "hsbs":
                            if re.match(r'.*\.(H-OU|HOU)\..*', download_title):
                                self.log_debug(
                                    "%s - Release ignoriert (Falsches 3D-Format)" % download_title)
                                continue
                        elif c3d_type == "hou":
                            if not re.match(r'.*\.(H-OU|HOU)\..*', download_title):
                                self.log_debug(
                                    "%s - Release ignoriert (Falsches 3D-Format)" % download_title)
                                continue
                        found = True
                    else:
                        continue
                    if found:
                        episode = re.search(
                            r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', download_title.lower())
                        if episode:
                            self.log_debug(
                                "%s - Release ignoriert (Serienepisode)" % download_title)
                            continue
                        self.download_imdb(
                            download_title, download_page, score, download_imdb, details)

    def download_imdb(self, key, download_link, score, download_imdb, details):
        if download_link:
            if "bW92aWUtYmxvZy5vcmcvMjAxMC8=".decode("base64") in download_link:
                self.log_debug("Fake-Link erkannt!")
                return
            else:
                englisch = False
                if "*englisch*" in key.lower():
                    key = key.replace(
                        '*ENGLISCH*', '').replace("*Englisch*", "")
                    englisch = True
                    if not rsscrawler.get('english'):
                        self.log_debug(
                            "%s - Englische Releases deaktiviert" % key)
                        return
                if self.config.get('enforcedl') and '.dl.' not in key.lower():
                    original_language = ""
                    if len(details) > 0:
                        original_language = re.findall(
                            r"Language:<\/h4>\n.*?\n.*?url'>(.*?)<\/a>", details)
                        if original_language:
                            original_language = original_language[0]
                        else:
                            self.log_debug(
                                "%s - Originalsprache nicht ermittelbar" % key)
                    elif len(download_imdb) > 0:
                        details = getURL(download_imdb)
                        if not details:
                            self.log_debug(
                                "%s - Originalsprache nicht ermittelbar" % key)
                        original_language = re.findall(
                            r"Language:<\/h4>\n.*?\n.*?url'>(.*?)<\/a>", details)
                        if original_language:
                            original_language = original_language[0]
                        else:
                            self.log_debug(
                                "%s - Originalsprache nicht ermittelbar" % key)

                    if original_language == "German":
                        self.log_debug(
                            "%s - Originalsprache ist Deutsch. Breche Suche nach zweisprachigem Release ab!" % key)
                    else:
                        if not self.download_dl(key) and not englisch:
                            self.log_debug(
                                "%s - Kein zweisprachiges Release gefunden!" % key)
                            return

                if str(self.db.retrieve(key)) == 'added' or str(self.db.retrieve(key)) == 'notdl' or str(self.db.retrieve(key.replace(".COMPLETE", "").replace(".Complete", ""))) == 'added':
                    self.log_debug(
                        "%s - Release ignoriert (bereits gefunden)" % key)
                elif '.3d.' not in key.lower():
                    retail = False
                    if (self.config.get('enforcedl') and '.dl.' in key.lower()) or not self.config.get(
                            'enforcedl'):
                        if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                            if self.config.get('enforcedl'):
                                if common.cutoff(key, '1'):
                                    retail = True
                            else:
                                if common.cutoff(key, '0'):
                                    retail = True
                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler"
                    )
                    self.db.store(
                        key,
                        'notdl' if self.config.get(
                            'enforcedl') and '.dl.' not in key.lower() else 'added'
                    )
                    log_entry = '[IMDB ' + score + '/Film] - ' + ('<b>Englisch</b> - ' if englisch and not retail else "") + ('<b>Englisch/Retail</b> - ' if englisch and retail else "") + ('<b>Retail</b> - ' if not englisch and retail else "") + key + ' - <a href="' + \
                        download_link + \
                        '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                        key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                    self.log_info(log_entry)
                    added_items.append(log_entry)
                else:
                    retail = False
                    if (self.config.get('enforcedl') and '.dl.' in key.lower()) or not self.config.get(
                            'enforcedl'):
                        if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                            if self.config.get('enforcedl'):
                                if common.cutoff(key, '2'):
                                    retail = True
                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler/3Dcrawler"
                    )
                    self.db.store(
                        key,
                        'notdl' if self.config.get(
                            'enforcedl') and '.dl.' not in key.lower() else 'added'
                    )
                    log_entry = '[IMDB ' + score + '/Film] - <b>' + ('Retail/' if retail else "") + '3D</b> - ' + key + ' - <a href="' + download_link + \
                        '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                        key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                    self.log_info(log_entry)
                    added_items.append(log_entry)

    def _get_download_links(self, url):
        req_page = getURL(url)
        soup = bs(req_page, 'lxml')
        download = soup.find("div", {"id": "content"})
        url_hosters = re.findall(r'href="([^"\'>]*)".+?(.+?)<', str(download))
        for url_hoster in url_hosters:
            if not "bW92aWUtYmxvZy5vcmcv".decode("base64") in url_hoster[0]:
                if self.hoster.lower() in url_hoster[1].lower():
                    return url_hoster[0]

    def periodical_task(self):
        if self.filename == 'MB_Filme':
            try:
                imdb = float(self.config.get('imdb'))
            except:
                imdb = 0.0
            if imdb > 0:
                self.imdb_search(imdb)

        if self.empty_list:
            return
        urls = []
        if self.filename == 'MB_Staffeln':
            if not self.config.get('crawlseasons'):
                return
            self.allInfos = dict(
                set({key: value for (key, value) in self.getPatterns(
                    self.readInput(self.search_list),
                    quality=self.config.get('seasonsquality'), rg='.*', sf=('.complete.')
                ).items()}.items()
                )
            )
        elif self.filename == 'MB_Regex':
            if not self.config.get('regex'):
                return
            self.allInfos = dict(
                set({key: value for (key, value) in self.getPatterns(
                    self.readInput(self.search_list)
                ).items()}.items()
                ) if self.config.get('regex') else []
            )
        else:
            if self.filename == 'MB_3D':
                if not self.config.get('crawl3d'):
                    return
            self.allInfos = dict(
                set({key: value for (key, value) in self.getPatterns(
                    self.readInput(self.search_list), quality=self.config.get('quality'), rg='.*', sf=None
                ).items()}.items()
                )
            )
        if self.filename != 'MB_Regex':
            if self.config.get("historical"):
                for xline in self.allInfos.keys():
                    if len(xline) > 0 and not xline.startswith("#"):
                        xn = xline.split(",")[0].replace(
                            ".", " ").replace(" ", "+")
                        urls.append('aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZw=='.decode(
                            'base64') + '/search/%s/feed/rss2/' % xn)
            else:
                urls.append(self.FEED_URL)
        else:
            urls.append(self.FEED_URL)
        for url in urls:
            for (key, value, pattern) in self.searchLinks(feedparser.parse(url)):
                download_link = self._get_download_links(value[0])
                if download_link:
                    if "bW92aWUtYmxvZy5vcmcvMjAxMC8=".decode("base64") in download_link:
                        self.log_debug("Fake-Link erkannt!")
                        break
                    englisch = False
                    if "*englisch*" in key.lower():
                        key = key.replace(
                            '*ENGLISCH*', '').replace("*Englisch*", "")
                        englisch = True
                        if not rsscrawler.get('english'):
                            self.log_debug(
                                "%s - Englische Releases deaktiviert" % key)
                            return
                    if self.config.get('enforcedl') and '.dl.' not in key.lower():
                        original_language = ""
                        fail = False
                        get_imdb_url = getURL(url)
                        key_regex = r'<title>' + \
                            re.escape(
                                key) + r'.*?<\/title>\n.*?<link>(?:(?:.*?\n){1,25}).*?[mM][kK][vV].*?(?:|href=.?http(?:|s):\/\/(?:|www\.)imdb\.com\/title\/(tt[0-9]{7,9}).*?)[iI][mM][dD][bB].*?(?!\d(?:\.|\,)\d)(?:.|.*?)<\/a>'
                        imdb_id = re.findall(key_regex, get_imdb_url)
                        if len(imdb_id) > 0:
                            if not imdb_id[0]:
                                fail = True
                            else:
                                imdb_id = imdb_id[0]
                        else:
                            fail = True
                        if fail:
                            search_title = re.findall(
                                r"(.*?)(?:\.(?:(?:19|20)\d{2})|\.German|\.\d{3,4}p|\.S(?:\d{1,3})\.)", key)[0].replace(".", "+")
                            search_url = "http://www.imdb.com/find?q=" + search_title
                            search_page = getURL(search_url)
                            search_results = re.findall(
                                r'<td class="result_text"> <a href="\/title\/(tt[0-9]{7,9})\/\?ref_=fn_al_tt_\d" >(.*?)<\/a>.*? \((\d{4})\)..(.{9})', search_page)
                            total_results = len(search_results)
                            if total_results == 0:
                                download_imdb = ""
                            elif self.filename == 'MB_Staffeln':
                                imdb_id = search_results[0][0]
                            else:
                                no_series = False
                                while total_results > 0:
                                    attempt = 0
                                    for result in search_results:
                                        if result[3] == "TV Series":
                                            no_series = False
                                            total_results -= 1
                                            attempt += 1
                                        else:
                                            no_series = True
                                            imdb_id = search_results[attempt][0]
                                            total_results = 0
                                            break
                                if no_series is False:
                                    self.log_debug(
                                        "%s - Keine passende Film-IMDB-Seite gefunden" % key)
                        if not imdb_id:
                            if not self.download_dl(key):
                                self.log_debug(
                                    "%s - Kein zweisprachiges Release gefunden." % key)
                        else:
                            if isinstance(imdb_id, list):
                                imdb_id = imdb_id.pop()
                            imdb_url = "http://www.imdb.com/title/" + imdb_id
                            details = getURL(imdb_url)
                            if not details:
                                self.log_debug(
                                    "%s - Originalsprache nicht ermittelbar" % key)
                            original_language = re.findall(
                                r"Language:<\/h4>\n.*?\n.*?url'>(.*?)<\/a>", details)
                            if original_language:
                                original_language = original_language[0]
                            if original_language == "German":
                                self.log_debug(
                                    "%s - Originalsprache ist Deutsch. Breche Suche nach zweisprachigem Release ab!" % key)
                            else:
                                if not self.download_dl(key) and not englisch:
                                    self.log_debug(
                                        "%s - Kein zweisprachiges Release gefunden! Breche ab." % key)
                                    break
                    if str(self.db.retrieve(key)) == 'added' or str(self.db.retrieve(key)) == 'notdl' or str(self.db.retrieve(key.replace(".COMPLETE", "").replace(".Complete", ""))) == 'added':
                        self.log_debug(
                            "%s - Release ignoriert (bereits gefunden)" % key)
                    elif self.filename == 'MB_Filme':
                        retail = False
                        if (self.config.get('enforcedl') and '.dl.' in key.lower()) or not self.config.get(
                                'enforcedl'):
                            if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                                if self.config.get('enforcedl'):
                                    if common.cutoff(key, '1'):
                                        retail = True
                                else:
                                    if common.cutoff(key, '0'):
                                        retail = True
                        common.write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler"
                        )
                        self.db.store(
                            key,
                            'notdl' if self.config.get(
                                'enforcedl') and '.dl.' not in key.lower() else 'added'
                        )
                        log_entry = '[Film] - ' + ('<b>Englisch</b> - ' if englisch and not retail else "") + ('<b>Englisch/Retail</b> - ' if englisch and retail else "") + ('<b>Retail</b> - ' if not englisch and retail else "") + key + ' - <a href="' + download_link + \
                            '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                            key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                        self.log_info(log_entry)
                        added_items.append(log_entry)
                    elif self.filename == 'MB_3D':
                        retail = False
                        if (self.config.get('enforcedl') and '.dl.' in key.lower()) or not self.config.get(
                                'enforcedl'):
                            if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                                if self.config.get('enforcedl'):
                                    if common.cutoff(key, '2'):
                                        retail = True
                        common.write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler/3Dcrawler"
                        )
                        self.db.store(
                            key,
                            'notdl' if self.config.get(
                                'enforcedl') and '.dl.' not in key.lower() else 'added'
                        )
                        log_entry = '[Film] - <b>' + ('Retail/' if retail else "") + '3D</b> - ' + key + ' - <a href="' + download_link + '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                            key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                        self.log_info(log_entry)
                        added_items.append(log_entry)
                    elif self.filename == 'MB_Staffeln':
                        common.write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler"
                        )
                        self.db.store(
                            key.replace(".COMPLETE", "").replace(
                                ".Complete", ""),
                            'notdl' if self.config.get(
                                'enforcedl') and '.dl.' not in key.lower() else 'added'
                        )
                        log_entry = '[Staffel] - ' + key.replace(".COMPLETE", "").replace(
                            ".Complete", "") + ' - [<a href="' + download_link + '" target="_blank">Link</a>]'
                        self.log_info(log_entry)
                        added_items.append(log_entry)
                    else:
                        common.write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler"
                        )
                        self.db.store(
                            key,
                            'notdl' if self.config.get(
                                'enforcedl') and '.dl.' not in key.lower() else 'added'
                        )
                        log_entry = '[Film/Serie/RegEx] - ' + key + ' - <a href="' + download_link + \
                            '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                            key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                        self.log_info(log_entry)
                        added_items.append(log_entry)


class HW():
    _INTERNAL_NAME = 'MB'
    FEED_URL = "aHR0cDovL3d3dy5oZC13b3JsZC5vcmcvZmVlZC8=".decode('base64')
    SUBSTITUTE = r"[&#\s/]"

    def __init__(self, filename):
        rsscrawler = RssConfig('RSScrawler')
        self.config = RssConfig(self._INTERNAL_NAME)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.filename = filename
        self.db = RssDb(os.path.join(os.path.dirname(
            sys.argv[0]), "RSScrawler.db"), 'rsscrawler')
        self.search_list = os.path.join(os.path.dirname(
            sys.argv[0]), 'Einstellungen/Listen/{}.txt'.format(self.filename))
        self.hoster = rsscrawler.get("hoster")
        self.dictWithNamesAndLinks = {}
        self.empty_list = False

    def readInput(self, file):
        if not os.path.isfile(file):
            open(file, "a").close()
            placeholder = open(file, 'w')
            placeholder.write('XXXXXXXXXX')
            placeholder.close()
        try:
            f = codecs.open(file, "rb")
            return f.read().splitlines()
        except:
            self.log_error("Liste nicht gefunden!")

    def getPatterns(self, patterns, **kwargs):
        if patterns == ["XXXXXXXXXX"]:
            self.log_debug(
                "Liste enthält Platzhalter. Stoppe Suche für Filme!")
            self.empty_list = True
        if kwargs:
            return {line: (kwargs['quality'], kwargs['rg'], kwargs['sf']) for line in patterns}
        return {x: (x) for x in patterns}

    def searchLinks(self, feed):
        if self.empty_list:
            return
        ignore = "|".join(
            [r"\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if self.config.get("ignore") else r"^unmatchable$"

        for key in self.allInfos:
            s = re.sub(self.SUBSTITUTE, ".", "^" + key).lower()
            for post in feed.entries:
                found = re.search(s, post.title.lower())
                if found:
                    found = re.search(ignore, post.title.lower())
                    if found:
                        self.log_debug(
                            "%s - Release ignoriert (basierend auf ignore-Einstellung)" % post.title)
                        continue
                    if rsscrawler.get("surround"):
                        if not re.match(r'.*\.(DTS|DD\+*51|DD\+*71|AC3\.5\.*1)\..*', post.title):
                            self.log_debug(
                                post.title + " - Release ignoriert (kein Mehrkanalton)")
                            continue
                    ss = self.allInfos[key][0].lower()
                    if self.filename == 'MB_Filme':
                        if ss == "480p":
                            if "720p" in post.title.lower() or "1080p" in post.title.lower() or "1080i" in post.title.lower() or "2160p" in post.title.lower():
                                continue
                            found = True
                        else:
                            found = re.search(ss, post.title.lower())
                        if found:
                            sss = r"[\.-]+" + self.allInfos[key][1].lower()
                            found = re.search(sss, post.title.lower())
                            if self.allInfos[key][2]:
                                found = all([word in post.title.lower()
                                             for word in self.allInfos[key][2]])
                            if found:
                                episode = re.search(
                                    r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', post.title.lower())
                                if episode:
                                    self.log_debug(
                                        "%s - Release ignoriert (Serienepisode)" % post.title)
                                    continue
                                yield (post.title, [post.link], key)
                    elif self.filename == 'MB_3D':
                        if '.3d.' in post.title.lower():
                            if self.config.get('crawl3d') and (
                                    "1080p" in post.title.lower() or "1080i" in post.title.lower()):
                                if not self.config.get("crawl3dtype"):
                                    c3d_type = "hsbs"
                                else:
                                    c3d_type = self.config.get("crawl3dtype")
                                if c3d_type == "hsbs":
                                    if re.match(r'.*\.(H-OU|HOU)\..*', post.title):
                                        self.log_debug(
                                            "%s - Release ignoriert (Falsches 3D-Format)" % post.title)
                                        continue
                                elif c3d_type == "hou":
                                    if not re.match(r'.*\.(H-OU|HOU)\..*', post.title):
                                        self.log_debug(
                                            "%s - Release ignoriert (Falsches 3D-Format)" % post.title)
                                        continue
                                found = True
                            else:
                                continue
                        if found:
                            sss = r"[\.-]+" + self.allInfos[key][1].lower()
                            found = re.search(sss, post.title.lower())
                            if self.allInfos[key][2]:
                                found = all([word in post.title.lower()
                                             for word in self.allInfos[key][2]])
                            if found:
                                episode = re.search(
                                    r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', post.title.lower())
                                if episode:
                                    self.log_debug(
                                        "%s - Release ignoriert (Serienepisode)" % post.title)
                                    continue
                                yield (post.title, [post.link], key)

                    elif self.filename == 'MB_Staffeln':
                        validsource = re.search(self.config.get(
                            "seasonssource"), post.title.lower())
                        if not validsource:
                            self.log_debug(
                                post.title + " - Release hat falsche Quelle")
                            continue
                        if not ".complete." in post.title.lower():
                            self.log_debug(
                                post.title + " - Staffel noch nicht komplett")
                            continue
                        season = re.search(r"\.s\d", post.title.lower())
                        if not season:
                            self.log_debug(
                                post.title + " - Release ist keine Staffel")
                            continue
                        if not self.config.get("seasonpacks"):
                            staffelpack = re.search(
                                r"s\d.*(-|\.).*s\d", post.title.lower())
                            if staffelpack:
                                self.log_debug(
                                    "%s - Release ignoriert (Staffelpaket)" % post.title)
                                continue
                        ss = self.allInfos[key][0].lower()

                        if ss == "480p":
                            if "720p" in post.title.lower() or "1080p" in post.title.lower() or "1080i" in post.title.lower() or "2160p" in post.title.lower():
                                continue
                            found = True
                        else:
                            found = re.search(ss, post.title.lower())
                        if found:
                            sss = r"[\.-]+" + self.allInfos[key][1].lower()
                            found = re.search(sss, post.title.lower())

                            if self.allInfos[key][2]:
                                found = all([word in post.title.lower()
                                             for word in self.allInfos[key][2]])
                            if found:
                                episode = re.search(
                                    r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', post.title.lower())
                                if episode:
                                    self.log_debug(
                                        "%s - Release ignoriert (Serienepisode)" % post.title)
                                    continue
                                yield (post.title, [post.link], key)
                    else:
                        yield (post.title, [post.link], key)

    def download_dl(self, title):
        search_title = title.replace(".German.720p.", ".German.DL.1080p.").replace(".German.DTS.720p.", ".German.DTS.DL.1080p.").replace(".German.AC3.720p.", ".German.AC3.DL.1080p.").replace(
            ".German.AC3LD.720p.", ".German.AC3LD.DL.1080p.").replace(".German.AC3.Dubbed.720p.", ".German.AC3.Dubbed.DL.1080p.").split('.x264-', 1)[0].split('.h264-', 1)[0].replace(".", " ").replace(" ", "+")
        search_url = "aHR0cDovL2hkLXdvcmxkLm9yZy9zZWFyY2gv".decode(
            'base64') + search_title + "/feed/rss2/"
        feedsearch_title = title.replace(".German.720p.", ".German.DL.1080p.").replace(".German.DTS.720p.", ".German.DTS.DL.1080p.").replace(".German.AC3.720p.", ".German.AC3.DL.1080p.").replace(
            ".German.AC3LD.720p.", ".German.AC3LD.DL.1080p.").replace(".German.AC3.Dubbed.720p.", ".German.AC3.Dubbed.DL.1080p.").split('.x264-', 1)[0].split('.h264-', 1)[0]
        if not '.dl.' in feedsearch_title.lower():
            self.log_debug(
                "%s - Release ignoriert (nicht zweisprachig, da wahrscheinlich nicht Retail)" % feedsearch_title)
            return False
        for (key, value, pattern) in self.dl_search(feedparser.parse(search_url), feedsearch_title):
            download_link = self._get_download_links(value[0])
            if download_link:
                if str(self.db.retrieve(key)) == 'added' or str(self.db.retrieve(key)) == 'dl':
                    self.log_debug(
                        "%s - zweisprachiges Release ignoriert (bereits gefunden)" % key)
                    return True
                elif self.filename == 'MB_Filme':
                    retail = False
                    if self.config.get('cutoff'):
                        if self.config.get('enforcedl'):
                            if common.cutoff(key, '1'):
                                retail = True
                        else:
                            if common.cutoff(key, '0'):
                                retail = True
                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler/Remux"
                    )
                    self.db.store(
                        key,
                        'dl' if self.config.get(
                            'enforcedl') and '.dl.' in key.lower() else 'added'
                    )
                    log_entry = '[Film] - <b>' + ('Retail/' if retail else "") + 'Zweisprachig</b> - ' + key + ' - <a href="' + download_link + \
                        '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                        key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                    self.log_info(log_entry)
                    added_items.append(log_entry)
                    return True
                elif self.filename == 'MB_3D':
                    retail = False
                    if self.config.get('cutoff'):
                        if common.cutoff(key, '2'):
                            retail = True
                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler/3Dcrawler"
                    )
                    self.db.store(
                        key,
                        'dl' if self.config.get(
                            'enforcedl') and '.dl.' in key.lower() else 'added'
                    )
                    log_entry = '[Film] - <b>' + ('Retail/' if retail else "") + '3D/Zweisprachig</b> - ' + key + ' - <a href="' + download_link + \
                        '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                        key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                    self.log_info(log_entry)
                    added_items.append(log_entry)
                    return True
                elif self.filename == 'MB_Regex':
                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler"
                    )
                    self.db.store(
                        key,
                        'dl' if self.config.get(
                            'enforcedl') and '.dl.' in key.lower() else 'added'
                    )
                    log_entry = '[Film/Serie/RegEx] - <b>Zweisprachig</b> - ' + key + ' - <a href="' + download_link + \
                        '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                        key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                    self.log_info(log_entry)
                    added_items.append(log_entry)
                    return True
                else:
                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler/Remux"
                    )
                    self.db.store(
                        key,
                        'dl' if self.config.get(
                            'enforcedl') and '.dl.' in key.lower() else 'added'
                    )
                    log_entry = '[Staffel] - <b>Zweisprachig</b> - ' + key + ' - <a href="' + download_link + \
                        '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                        key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                    self.log_info(log_entry)
                    added_items.append(log_entry)
                    return True

    def dl_search(self, feed, title):
        ignore = "|".join(
            [r"\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if self.config.get("ignore") else r"^unmatchable$"

        s = re.sub(self.SUBSTITUTE, ".", title).lower()
        for post in feed.entries:
            found = re.search(s, post.title.lower())
            if found:
                found = re.search(ignore, post.title.lower())
                if found:
                    self.log_debug(
                        "%s - zweisprachiges Release ignoriert (basierend auf ignore-Einstellung)" % post.title)
                    continue
                yield (post.title, [post.link], title)

    def imdb_search(self, imdb):
        imdbchecked = re.findall(
            r'<title>(.*?)<\/title>\n.*?<link>(.*)<\/link>(?:(?:.*?\n){1,25}).*?[mM][kK][vV].*?(?:|href=.?http(?:|s):\/\/(?:|www\.)imdb\.com\/title\/(tt[0-9]{7,9}).*?)[iI][mM][dD][bB].*?(\d(?:\.|\,)\d)(?:.|.*?)<\/a>', getURL(self.FEED_URL))
        for item in imdbchecked:
            download_title = item[0]
            ignore = "|".join(
                [r"\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if self.config.get("ignore") else r"^unmatchable$"
            found = re.search(ignore, download_title.lower())
            if found:
                self.log_debug(
                    "%s - Release ignoriert (basierend auf ignore-Einstellung)" % download_title)
                continue
            if rsscrawler.get("surround"):
                if not re.match(r'.*\.(DTS|DD\+*51|DD\+*71|AC3\.5\.*1)\..*', download_title):
                    self.log_debug(
                        download_title + " - Release ignoriert (kein Mehrkanalton)")
                    continue
            season = re.search(r'\.S(\d{1,3})(\.|-|E)', download_title)
            if season:
                self.log_debug(
                    "%s - Release ignoriert (IMDB sucht nur Filme)" % download_title)
                continue

            year_in_title = re.findall(r"\.((?:19|20)\d{2})\.", download_title)
            years_in_title = len(year_in_title)
            if years_in_title > 0:
                title_year = year_in_title[years_in_title - 1]
            else:
                title_year = ""

            download_page = self._get_download_links(item[1])

            if len(item[2]) > 0:
                download_imdb = "http://www.imdb.com/title/" + item[2]
            else:
                try:
                    search_title = re.findall(r"(.*?)(?:\.(?:(?:19|20)\d{2})|\.German|\.\d{3,4}p|\.S(?:\d{1,3})\.)", download_title)[0].replace(
                        ".", "+").replace("ae", "ä").replace("oe", "ö").replace("ue", "ü").replace("Ae", "Ä").replace("Oe", "Ö").replace("Ue", "Ü")
                except:
                    break
                search_url = "http://www.imdb.com/find?q=" + search_title
                search_page = getURL(search_url)
                search_results = re.findall(
                    r'<td class="result_text"> <a href="\/title\/(tt[0-9]{7,9})\/\?ref_=fn_al_tt_\d" >(.*?)<\/a>.*? \((\d{4})\)..(.{9})', search_page)
                no_series = False
                total_results = len(search_results)
                if total_results == 0:
                    download_imdb = ""
                else:
                    while total_results > 0:
                        attempt = 0
                        for result in search_results:
                            if result[3] == "TV Series":
                                no_series = False
                                total_results -= 1
                                attempt += 1
                            else:
                                no_series = True
                                download_imdb = "http://www.imdb.com/title/" + \
                                    search_results[attempt][0]
                                title_year = search_results[attempt][2]
                                total_results = 0
                                break
                    if no_series is False:
                        self.log_debug(
                            "%s - Keine passende Film-IMDB-Seite gefunden" % download_title)

            download_score = float(item[3].replace(",", "."))
            score = str(download_score)

            details = ""
            min_year = self.config.get("imdbyear")
            if min_year:
                if len(title_year) > 0:
                    if title_year < min_year:
                        self.log_debug(
                            "%s - Release ignoriert (Film zu alt)" % download_title)
                        continue
                elif len(download_imdb) > 0:
                    details = getURL(download_imdb)
                    if not details:
                        self.log_debug(
                            "%s - Fehler bei Aufruf der IMDB-Seite" % download_title)
                        continue
                    title_year = re.findall(
                        r"<title>(?:.*) \(((?:19|20)\d{2})\) - IMDb<\/title>", details)
                    if not title_year:
                        self.log_debug(
                            "%s - Erscheinungsjahr nicht ermittelbar" % download_title)
                        continue
                    else:
                        title_year = title_year[0]
                    if title_year < min_year:
                        self.log_debug(
                            "%s - Release ignoriert (Film zu alt)" % download_title)
                        continue

            if len(download_imdb) > 0:
                if len(details) == 0:
                    details = getURL(download_imdb)
                if not details:
                    self.log_debug(
                        "%s - Release ignoriert (Film zu alt)" % download_title)
                    continue
                vote_count = re.findall(r'ratingCount">(.*?)<\/span>', details)
                if not vote_count:
                    self.log_debug(
                        "%s - Wertungsanzahl nicht ermittelbar" % download_title)
                    continue
                else:
                    vote_count = vote_count[0].replace(
                        ".", "").replace(",", "")
                if int(vote_count) < 1500:
                    self.log_debug(
                        download_title + " - Release ignoriert (Weniger als 1500 IMDB-Votes: " + vote_count + ")")
                    continue

            if download_score > imdb:
                ss = self.config.get('quality')
                if '.3d.' not in download_title.lower():
                    if ss == "480p":
                        if "720p" in download_title.lower() or "1080p" in download_title.lower() or "1080i" in download_title.lower() or "2160p" in download_title.lower():
                            continue
                        found = True
                    else:
                        found = re.search(ss, download_title.lower())
                    if found:
                        episode = re.search(
                            r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', download_title.lower())
                        if episode:
                            self.log_debug(
                                "%s - Release ignoriert (Serienepisode)" % download_title)
                            continue
                        self.download_imdb(
                            download_title, download_page, score, download_imdb, details)
                    else:
                        self.log_debug(
                            "%s - Release ignoriert (falsche Aufloesung)" % download_title)
                else:
                    if not self.config.get('crawl3d'):
                        self.log_debug(
                            "%s - Release ignoriert (3D-Suche deaktiviert)" % download_title)
                        return
                    if self.config.get('crawl3d') and ("1080p" in download_title.lower() or "1080i" in download_title.lower()):
                        if not self.config.get("crawl3dtype"):
                            c3d_type = "hsbs"
                        else:
                            c3d_type = self.config.get("crawl3dtype")
                        if c3d_type == "hsbs":
                            if re.match(r'.*\.(H-OU|HOU)\..*', download_title):
                                self.log_debug(
                                    "%s - Release ignoriert (Falsches 3D-Format)" % download_title)
                                continue
                        elif c3d_type == "hou":
                            if not re.match(r'.*\.(H-OU|HOU)\..*', download_title):
                                self.log_debug(
                                    "%s - Release ignoriert (Falsches 3D-Format)" % download_title)
                                continue
                        found = True
                    else:
                        continue
                    if found:
                        episode = re.search(
                            r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', download_title.lower())
                        if episode:
                            self.log_debug(
                                "%s - Release ignoriert (Serienepisode)" % download_title)
                            continue
                        self.download_imdb(
                            download_title, download_page, score, download_imdb, details)

    def download_imdb(self, key, download_link, score, download_imdb, details):
        if download_link:
            if "bW92aWUtYmxvZy5vcmcvMjAxMC8=".decode("base64") in download_link:
                self.log_debug("Fake-Link erkannt!")
                return
            else:
                englisch = False
                if "*englisch*" in key.lower():
                    key = key.replace(
                        '*ENGLISCH*', '').replace("*Englisch*", "")
                    englisch = True
                    if not rsscrawler.get('english'):
                        self.log_debug(
                            "%s - Englische Releases deaktiviert" % key)
                        return
                if self.config.get('enforcedl') and '.dl.' not in key.lower():
                    original_language = ""
                    if len(details) > 0:
                        original_language = re.findall(
                            r"Language:<\/h4>\n.*?\n.*?url'>(.*?)<\/a>", details)
                        if original_language:
                            original_language = original_language[0]
                        else:
                            self.log_debug(
                                "%s - Originalsprache nicht ermittelbar" % key)
                    elif len(download_imdb) > 0:
                        details = getURL(download_imdb)
                        if not details:
                            self.log_debug(
                                "%s - Originalsprache nicht ermittelbar" % key)
                        original_language = re.findall(
                            r"Language:<\/h4>\n.*?\n.*?url'>(.*?)<\/a>", details)
                        if original_language:
                            original_language = original_language[0]
                        else:
                            self.log_debug(
                                "%s - Originalsprache nicht ermittelbar" % key)

                    if original_language == "German":
                        self.log_debug(
                            "%s - Originalsprache ist Deutsch. Breche Suche nach zweisprachigem Release ab!" % key)
                    else:
                        if not self.download_dl(key) and not englisch:
                            self.log_debug(
                                "%s - Kein zweisprachiges Release gefunden!" % key)
                            return

                if str(self.db.retrieve(key)) == 'added' or str(self.db.retrieve(key)) == 'notdl' or str(self.db.retrieve(key.replace(".COMPLETE", "").replace(".Complete", ""))) == 'added':
                    self.log_debug(
                        "%s - Release ignoriert (bereits gefunden)" % key)
                elif '.3d.' not in key.lower():
                    retail = False
                    if (self.config.get('enforcedl') and '.dl.' in key.lower()) or not self.config.get(
                            'enforcedl'):
                        if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                            if self.config.get('enforcedl'):
                                if common.cutoff(key, '1'):
                                    retail = True
                            else:
                                if common.cutoff(key, '0'):
                                    retail = True
                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler"
                    )
                    self.db.store(
                        key,
                        'notdl' if self.config.get(
                            'enforcedl') and '.dl.' not in key.lower() else 'added'
                    )
                    log_entry = '[IMDB ' + score + '/Film] - ' + ('<b>Englisch</b> - ' if englisch and not retail else "") + ('<b>Englisch/Retail</b> - ' if englisch and retail else "") + ('<b>Retail</b> - ' if not englisch and retail else "") + key + ' - <a href="' + \
                        download_link + \
                        '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                        key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                    self.log_info(log_entry)
                    added_items.append(log_entry)
                else:
                    retail = False
                    if (self.config.get('enforcedl') and '.dl.' in key.lower()) or not self.config.get(
                            'enforcedl'):
                        if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                            if self.config.get('enforcedl'):
                                if common.cutoff(key, '2'):
                                    retail = True
                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler/3Dcrawler"
                    )
                    self.db.store(
                        key,
                        'notdl' if self.config.get(
                            'enforcedl') and '.dl.' not in key.lower() else 'added'
                    )
                    log_entry = '[IMDB ' + score + '/Film] - <b>' + ('Retail/' if retail else "") + '3D</b> - ' + key + ' - <a href="' + download_link + \
                        '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                        key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                    self.log_info(log_entry)
                    added_items.append(log_entry)

    def _get_download_links(self, url):
        req_page = getURL(url)
        soup = bs(req_page, 'lxml')
        download = soup.find("div", {"id": "content"})
        url_hosters = re.findall(r'href="([^"\'>]*)".+?(.+?)<', str(download))
        for url_hoster in url_hosters:
            if self.hoster.lower() in url_hoster[1].lower():
                return url_hoster[0]

    def periodical_task(self):
        if self.filename == 'MB_Filme':
            try:
                imdb = float(self.config.get('imdb'))
            except:
                imdb = 0.0
            if imdb > 0:
                self.imdb_search(imdb)

        if self.empty_list:
            return
        urls = []
        if self.filename == 'MB_Staffeln':
            if not self.config.get('crawlseasons'):
                return
            self.allInfos = dict(
                set({key: value for (key, value) in self.getPatterns(
                    self.readInput(self.search_list),
                    quality=self.config.get('seasonsquality'), rg='.*', sf=('.complete.')
                ).items()}.items()
                )
            )
        elif self.filename == 'MB_Regex':
            if not self.config.get('regex'):
                return
            self.allInfos = dict(
                set({key: value for (key, value) in self.getPatterns(
                    self.readInput(self.search_list)
                ).items()}.items()
                ) if self.config.get('regex') else []
            )
        else:
            if self.filename == 'MB_3D':
                if not self.config.get('crawl3d'):
                    return
            self.allInfos = dict(
                set({key: value for (key, value) in self.getPatterns(
                    self.readInput(self.search_list), quality=self.config.get('quality'), rg='.*', sf=None
                ).items()}.items()
                )
            )
        if self.filename != 'MB_Regex':
            if self.config.get("historical"):
                for xline in self.allInfos.keys():
                    if len(xline) > 0 and not xline.startswith("#"):
                        xn = xline.split(",")[0].replace(
                            ".", " ").replace(" ", "+")
                        urls.append('aHR0cDovL2hkLXdvcmxkLm9yZw=='.decode(
                            'base64') + '/search/%s/feed/rss2/' % xn)
            else:
                urls.append(self.FEED_URL)
        else:
            urls.append(self.FEED_URL)
        for url in urls:
            for (key, value, pattern) in self.searchLinks(feedparser.parse(url)):
                download_link = self._get_download_links(value[0])
                if download_link:
                    englisch = False
                    if "*englisch*" in key.lower():
                        key = key.replace(
                            '*ENGLISCH*', '').replace("*Englisch*", "")
                        englisch = True
                        if not rsscrawler.get('english'):
                            self.log_debug(
                                "%s - Englische Releases deaktiviert" % key)
                            return
                    if self.config.get('enforcedl') and '.dl.' not in key.lower():
                        original_language = ""
                        fail = False
                        get_imdb_url = getURL(url)
                        key_regex = r'<title>' + \
                            re.escape(
                                key) + r'.*?<\/title>\n.*?<link>(?:(?:.*?\n){1,25}).*?[mM][kK][vV].*?(?:|href=.?http(?:|s):\/\/(?:|www\.)imdb\.com\/title\/(tt[0-9]{7,9}).*?)[iI][mM][dD][bB].*?(?!\d(?:\.|\,)\d)(?:.|.*?)<\/a>'
                        imdb_id = re.findall(key_regex, get_imdb_url)
                        if len(imdb_id) > 0:
                            if not imdb_id[0]:
                                fail = True
                            else:
                                imdb_id = imdb_id[0]
                        else:
                            fail = True
                        if fail:
                            search_title = re.findall(
                                r"(.*?)(?:\.(?:(?:19|20)\d{2})|\.German|\.\d{3,4}p|\.S(?:\d{1,3})\.)", key)[0].replace(".", "+")
                            search_url = "http://www.imdb.com/find?q=" + search_title
                            search_page = getURL(search_url)
                            search_results = re.findall(
                                r'<td class="result_text"> <a href="\/title\/(tt[0-9]{7,9})\/\?ref_=fn_al_tt_\d" >(.*?)<\/a>.*? \((\d{4})\)..(.{9})', search_page)
                            total_results = len(search_results)
                            if total_results == 0:
                                download_imdb = ""
                            elif self.filename == 'MB_Staffeln':
                                imdb_id = search_results[0][0]
                            else:
                                no_series = False
                                while total_results > 0:
                                    attempt = 0
                                    for result in search_results:
                                        if result[3] == "TV Series":
                                            no_series = False
                                            total_results -= 1
                                            attempt += 1
                                        else:
                                            no_series = True
                                            imdb_id = search_results[attempt][0]
                                            total_results = 0
                                            break
                                if no_series is False:
                                    self.log_debug(
                                        "%s - Keine passende Film-IMDB-Seite gefunden" % key)
                        if not imdb_id:
                            if not self.download_dl(key):
                                self.log_debug(
                                    "%s - Kein zweisprachiges Release gefunden." % key)
                        else:
                            if isinstance(imdb_id, list):
                                imdb_id = imdb_id.pop()
                            imdb_url = "http://www.imdb.com/title/" + imdb_id
                            details = getURL(imdb_url)
                            if not details:
                                self.log_debug(
                                    "%s - Originalsprache nicht ermittelbar" % key)
                            original_language = re.findall(
                                r"Language:<\/h4>\n.*?\n.*?url'>(.*?)<\/a>", details)
                            if original_language:
                                original_language = original_language[0]
                            if original_language == "German":
                                self.log_debug(
                                    "%s - Originalsprache ist Deutsch. Breche Suche nach zweisprachigem Release ab!" % key)
                            else:
                                if not self.download_dl(key) and not englisch:
                                    self.log_debug(
                                        "%s - Kein zweisprachiges Release gefunden! Breche ab." % key)
                                    break
                    if str(self.db.retrieve(key)) == 'added' or str(self.db.retrieve(key)) == 'notdl' or str(self.db.retrieve(key.replace(".COMPLETE", "").replace(".Complete", ""))) == 'added':
                        self.log_debug(
                            "%s - Release ignoriert (bereits gefunden)" % key)
                    elif self.filename == 'MB_Filme':
                        retail = False
                        if (self.config.get('enforcedl') and '.dl.' in key.lower()) or not self.config.get(
                                'enforcedl'):
                            if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                                if self.config.get('enforcedl'):
                                    if common.cutoff(key, '1'):
                                        retail = True
                                else:
                                    if common.cutoff(key, '0'):
                                        retail = True
                        common.write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler"
                        )
                        self.db.store(
                            key,
                            'notdl' if self.config.get(
                                'enforcedl') and '.dl.' not in key.lower() else 'added'
                        )
                        log_entry = '[Film] - ' + ('<b>Englisch</b> - ' if englisch and not retail else "") + ('<b>Englisch/Retail</b> - ' if englisch and retail else "") + ('<b>Retail</b> - ' if not englisch and retail else "") + key + ' - <a href="' + download_link + \
                            '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                            key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                        self.log_info(log_entry)
                        added_items.append(log_entry)
                    elif self.filename == 'MB_3D':
                        retail = False
                        if (self.config.get('enforcedl') and '.dl.' in key.lower()) or not self.config.get(
                                'enforcedl'):
                            if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                                if self.config.get('enforcedl'):
                                    if common.cutoff(key, '2'):
                                        retail = True
                        common.write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler/3Dcrawler"
                        )
                        self.db.store(
                            key,
                            'notdl' if self.config.get(
                                'enforcedl') and '.dl.' not in key.lower() else 'added'
                        )
                        log_entry = '[Film] - <b>' + ('Retail/' if retail else "") + '3D</b> - ' + key + ' - <a href="' + download_link + '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                            key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                        self.log_info(log_entry)
                        added_items.append(log_entry)
                    elif self.filename == 'MB_Staffeln':
                        common.write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler"
                        )
                        self.db.store(
                            key.replace(".COMPLETE", "").replace(
                                ".Complete", ""),
                            'notdl' if self.config.get(
                                'enforcedl') and '.dl.' not in key.lower() else 'added'
                        )
                        log_entry = '[Staffel] - ' + key.replace(
                            ".COMPLETE.", ".") + ' - [<a href="' + download_link + '" target="_blank">Link</a>]'
                        self.log_info(log_entry)
                        added_items.append(log_entry)
                    else:
                        common.write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler"
                        )
                        self.db.store(
                            key,
                            'notdl' if self.config.get(
                                'enforcedl') and '.dl.' not in key.lower() else 'added'
                        )
                        log_entry = '[Film/Serie/RegEx] - ' + key + ' - <a href="' + download_link + \
                            '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                            key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                        self.log_info(log_entry)
                        added_items.append(log_entry)


class HA():
    _INTERNAL_NAME = 'MB'
    FEED_URL = "aHR0cDovL3d3dy5oZC1hcmVhLm9yZy9pbmRleC5waHA=".decode('base64')
    SUBSTITUTE = r"[&#\s/]"

    def __init__(self, filename):
        rsscrawler = RssConfig('RSScrawler')
        self.config = RssConfig(self._INTERNAL_NAME)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.filename = filename
        self.db = RssDb(os.path.join(os.path.dirname(
            sys.argv[0]), "RSScrawler.db"), 'rsscrawler')
        self.search_list = os.path.join(os.path.dirname(
            sys.argv[0]), 'Einstellungen/Listen/{}.txt'.format(self.filename))
        self._hosters_pattern = rsscrawler.get('hoster').replace(',', '|')
        self.dictWithNamesAndLinks = {}
        self.empty_list = False

    def readInput(self, file):
        if not os.path.isfile(file):
            open(file, "a").close()
            placeholder = open(file, 'w')
            placeholder.write('XXXXXXXXXX')
            placeholder.close()
        try:
            f = codecs.open(file, "rb")
            return f.read().splitlines()
        except:
            self.log_error("Liste nicht gefunden!")

    def getPatterns(self, patterns, **kwargs):
        if patterns == ["XXXXXXXXXX"]:
            self.log_debug(
                "Liste enthält Platzhalter. Stoppe Suche für Filme!")
            self.empty_list = True
        if kwargs:
            return {line: (kwargs['quality'], kwargs['rg'], kwargs['sf']) for line in patterns}
        return {x: (x) for x in patterns}

    def searchLinks(self, feed):
        if self.empty_list:
            return
        ignore = "|".join(
            [r"\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if self.config.get("ignore") else r"^unmatchable$"

        for key in self.allInfos:
            if not key.replace(" ", "+") in feed and not self.filename == 'MB_Regex':
                continue
            req_page = getURL(feed)
            if not req_page:
                self.log_debug("Ungueltiger Link bei Seitenaufruf")
                continue
            soup = bs(req_page, 'lxml')
            content = soup.find("div", {"id": "content"})
            if "index.php" in feed.lower():
                titles = content.findAll("div", {"id": "title"})
            else:
                titles = content.findAll("a")
            for title in titles:
                try:
                    hda = re.findall(
                        r'href="(.*?)" title="(.*?)">', str(title))[0]
                except:
                    self.log_debug("Ungueltiger Link bei Suche nach Titel")
                url = hda[0]
                title = hda[1]
                s = re.sub(self.SUBSTITUTE, ".", "^" + key).lower()
                found = re.search(s, title.lower())
                if found:
                    found = re.search(ignore, title.lower())
                    if found:
                        self.log_debug(
                            "%s - Release ignoriert (basierend auf ignore-Einstellung)" % title)
                        continue
                    if rsscrawler.get("surround"):
                        if not re.match(r'.*\.(DTS|DD\+*51|DD\+*71|AC3\.5\.*1)\..*', title):
                            self.log_debug(
                                title + " - Release ignoriert (kein Mehrkanalton)")
                            continue
                    ss = self.allInfos[key][0].lower()
                    if self.filename == 'MB_Filme':
                        if ss == "480p":
                            if "720p" in title.lower() or "1080p" in title.lower() or "1080i" in title.lower():
                                continue
                            found = True
                        else:
                            found = re.search(ss, title.lower())
                        if found:
                            sss = r"[\.-]+" + self.allInfos[key][1].lower()
                            found = re.search(sss, title.lower())
                            if self.allInfos[key][2]:
                                found = all([word in title.lower()
                                             for word in self.allInfos[key][2]])
                            if found:
                                episode = re.search(
                                    r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', title.lower())
                                if episode:
                                    self.log_debug(
                                        "%s - Release ignoriert (Serienepisode)" % title)
                                    continue
                                link = self._get_download_links(url)
                                yield (title, link, key)
                    elif self.filename == 'MB_3D':
                        if '.3d.' in title.lower():
                            if self.config.get('crawl3d') and (
                                    "1080p" in title.lower() or "1080i" in title.lower()):
                                if not self.config.get("crawl3dtype"):
                                    c3d_type = "hsbs"
                                else:
                                    c3d_type = self.config.get("crawl3dtype")
                                if c3d_type == "hsbs":
                                    if re.match(r'.*\.(H-OU|HOU)\..*', title):
                                        self.log_debug(
                                            "%s - Release ignoriert (Falsches 3D-Format)" % title)
                                        continue
                                elif c3d_type == "hou":
                                    if not re.match(r'.*\.(H-OU|HOU)\..*', title):
                                        self.log_debug(
                                            "%s - Release ignoriert (Falsches 3D-Format)" % title)
                                        continue
                                found = True
                            else:
                                continue
                        if found:
                            sss = r"[\.-]+" + self.allInfos[key][1].lower()
                            found = re.search(sss, title.lower())
                            if self.allInfos[key][2]:
                                found = all([word in title.lower()
                                             for word in self.allInfos[key][2]])
                            if found:
                                episode = re.search(
                                    r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', title.lower())
                                if episode:
                                    self.log_debug(
                                        "%s - Release ignoriert (Serienepisode)" % title)
                                    continue
                                link = self._get_download_links(url)
                                yield (title, link, key)

                    elif self.filename == 'MB_Staffeln':
                        validsource = re.search(self.config.get(
                            "seasonssource"), title.lower())
                        if not validsource:
                            self.log_debug(
                                title + " - Release hat falsche Quelle")
                            continue
                        if not ".complete." in title.lower():
                            self.log_debug(
                                title + " - Staffel noch nicht komplett")
                            continue
                        season = re.search(r"\.s\d", title.lower())
                        if not season:
                            self.log_debug(
                                title + " - Release ist keine Staffel")
                            continue
                        if not self.config.get("seasonpacks"):
                            staffelpack = re.search(
                                r"s\d.*(-|\.).*s\d", title.lower())
                            if staffelpack:
                                self.log_debug(
                                    "%s - Release ignoriert (Staffelpaket)" % title)
                                continue
                        ss = self.allInfos[key][0].lower()

                        if ss == "480p":
                            if "720p" in title.lower() or "1080p" in title.lower() or "1080i" in title.lower():
                                continue
                            found = True
                        else:
                            found = re.search(ss, title.lower())
                        if found:
                            sss = r"[\.-]+" + self.allInfos[key][1].lower()
                            found = re.search(sss, title.lower())

                            if self.allInfos[key][2]:
                                found = all([word in title.lower()
                                             for word in self.allInfos[key][2]])
                            if found:
                                episode = re.search(
                                    r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', title.lower())
                                if episode:
                                    self.log_debug(
                                        "%s - Release ignoriert (Serienepisode)" % title)
                                    continue
                                link = self._get_download_links(url)
                                yield (title, link, key)
                    else:
                        link = self._get_download_links(url)
                        yield (title, link, key)

    def download_dl(self, title):
        search_title = title.replace(".German.720p.", ".German.DL.1080p.").replace(".German.DTS.720p.", ".German.DTS.DL.1080p.").replace(".German.AC3.720p.", ".German.AC3.DL.1080p.").replace(
            ".German.AC3LD.720p.", ".German.AC3LD.DL.1080p.").replace(".German.AC3.Dubbed.720p.", ".German.AC3.Dubbed.DL.1080p.").split('.x264-', 1)[0].split('.h264-', 1)[0].replace(".", " ").replace(" ", "+")
        search_url = "aHR0cDovL3d3dy5oZC1hcmVhLm9yZy8/cz1zZWFyY2gmcT0=".decode(
            'base64') + search_title
        feedsearch_title = title.replace(".German.720p.", ".German.DL.1080p.").replace(".German.DTS.720p.", ".German.DTS.DL.1080p.").replace(".German.AC3.720p.", ".German.AC3.DL.1080p.").replace(
            ".German.AC3LD.720p.", ".German.AC3LD.DL.1080p.").replace(".German.AC3.Dubbed.720p.", ".German.AC3.Dubbed.DL.1080p.").split('.x264-', 1)[0].split('.h264-', 1)[0]
        if not '.dl.' in feedsearch_title.lower():
            self.log_debug(
                "%s - Release ignoriert (nicht zweisprachig, da wahrscheinlich nicht Retail)" % feedsearch_title)
            return False
        for (key, download_link, pattern) in self.dl_search(search_url, feedsearch_title):
            if download_link:
                if str(self.db.retrieve(key)) == 'added' or str(self.db.retrieve(key)) == 'dl':
                    self.log_debug(
                        "%s - zweisprachiges Release ignoriert (bereits gefunden)" % key)
                    return True
                elif self.filename == 'MB_Filme':
                    retail = False
                    if self.config.get('cutoff'):
                        if self.config.get('enforcedl'):
                            if common.cutoff(key, '1'):
                                retail = True
                        else:
                            if common.cutoff(key, '0'):
                                retail = True
                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler/Remux"
                    )
                    self.db.store(
                        key,
                        'dl' if self.config.get(
                            'enforcedl') and '.dl.' in key.lower() else 'added'
                    )
                    log_entry = '[Film] - <b>' + ('Retail/' if retail else "") + 'Zweisprachig</b> - ' + key + ' - <a href="' + download_link + \
                        '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                        key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                    self.log_info(log_entry)
                    added_items.append(log_entry)
                    return True
                elif self.filename == 'MB_3D':
                    retail = False
                    if self.config.get('cutoff'):
                        if common.cutoff(key, '2'):
                            retail = True
                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler/3Dcrawler"
                    )
                    self.db.store(
                        key,
                        'dl' if self.config.get(
                            'enforcedl') and '.dl.' in key.lower() else 'added'
                    )
                    log_entry = '[Film] - <b>' + ('Retail/' if retail else "") + '3D/Zweisprachig</b> - ' + key + ' - <a href="' + download_link + \
                        '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                        key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                    self.log_info(log_entry)
                    added_items.append(log_entry)
                    return True
                elif self.filename == 'MB_Regex':
                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler"
                    )
                    self.db.store(
                        key,
                        'dl' if self.config.get(
                            'enforcedl') and '.dl.' in key.lower() else 'added'
                    )
                    log_entry = '[Film/Serie/RegEx] - <b>Zweisprachig</b> - ' + key + ' - <a href="' + download_link + \
                        '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                        key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                    self.log_info(log_entry)
                    added_items.append(log_entry)
                    return True
                else:
                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler/Remux"
                    )
                    self.db.store(
                        key,
                        'dl' if self.config.get(
                            'enforcedl') and '.dl.' in key.lower() else 'added'
                    )
                    log_entry = '[Staffel] - <b>Zweisprachig</b> - ' + key + ' - <a href="' + download_link + \
                        '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                        key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                    self.log_info(log_entry)
                    added_items.append(log_entry)
                    return True

    def dl_search(self, feed, title):
        ignore = "|".join(
            [r"\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if self.config.get("ignore") else r"^unmatchable$"
        req_page = getURL(feed)
        soup = bs(req_page, 'lxml')
        content = soup.find("div", {"id": "content"})
        try:
            found = content.findAll("a")[0]
        except:
            return
        hda = re.findall(r'href="(.*?)" title="(.*?)">', str(found))[0]
        url = hda[0]
        title = hda[1]
        link = getURL(url)
        dl_soup = bs(link, 'lxml')
        dl_links = re.findall(
            r'href="(http:\/\/filecrypt.cc.*?|https:\/\/www.filecrypt.cc.*?)" target="_blank">(.*?)<\/a>', str(dl_soup))
        for link in dl_links:
            url = link[0]
            if self._hosters_pattern.lower().replace(" ", "-") in link[1].lower().replace(" ", "-"):
                s = re.sub(self.SUBSTITUTE, ".", title).lower()
                found = re.search(s, title.lower())
                if found:
                    found = re.search(ignore, title.lower())
                    if found:
                        self.log_debug(
                            "%s - zweisprachiges Release ignoriert (basierend auf ignore-Einstellung)" % title)
                        continue
                    yield (title, url, title)

    def _get_download_links(self, url):
        link = getURL(url)
        dl_soup = bs(link, 'lxml')
        dl_links = re.findall(
            r'inline.*?display:inline;"><a href="(.*?)" target="_blank">(.*?)<\/a>', str(dl_soup))
        for link in dl_links:
            url = link[0]
            if self._hosters_pattern.lower().replace(" ", "-") in link[1].lower().replace(" ", "-"):
                return url

    def periodical_task(self):
        urls = []
        if self.filename == 'MB_Staffeln':
            if not self.config.get('crawlseasons'):
                return
            self.allInfos = dict(
                set({key: value for (key, value) in self.getPatterns(
                    self.readInput(self.search_list),
                    quality=self.config.get('seasonsquality'), rg='.*', sf=('.complete.')
                ).items()}.items()
                )
            )
        elif self.filename == 'MB_Regex':
            if not self.config.get('regex'):
                return
            self.allInfos = dict(
                set({key: value for (key, value) in self.getPatterns(
                    self.readInput(self.search_list)
                ).items()}.items()
                ) if self.config.get('regex') else []
            )
        else:
            if self.filename == 'MB_3D':
                if not self.config.get('crawl3d'):
                    return
            self.allInfos = dict(
                set({key: value for (key, value) in self.getPatterns(
                    self.readInput(self.search_list), quality=self.config.get('quality'), rg='.*', sf=None
                ).items()}.items()
                )
            )
        if self.filename != 'MB_Regex':
            if self.config.get("historical"):
                for xline in self.allInfos.keys():
                    if len(xline) > 0 and not xline.startswith("#"):
                        title = xline.split(",")[0].replace(" ", ".")
                        search_title = title.replace(
                            ".", " ").replace(" ", "+")
                        urls.append(
                            "aHR0cDovL3d3dy5oZC1hcmVhLm9yZy8/cz1zZWFyY2gmcT0=".decode('base64') + search_title)
            else:
                urls.append(self.FEED_URL)
        else:
            urls.append(self.FEED_URL)

        for url in urls:
            for (key, download_link, pattern) in self.searchLinks(url):
                if download_link:
                    englisch = False
                    if "*englisch*" in key.lower():
                        key = key.replace(
                            '*ENGLISCH*', '').replace("*Englisch*", "")
                        englisch = True
                        if not rsscrawler.get('english'):
                            self.log_debug(
                                "%s - Englische Releases deaktiviert" % key)
                            return
                    if self.config.get('enforcedl') and '.dl.' not in key.lower():
                        if not self.download_dl(key):
                            self.log_debug(
                                "%s - Kein zweisprachiges Release gefunden" % key)
                    if str(self.db.retrieve(key)) == 'added' or str(self.db.retrieve(key)) == 'notdl' or str(self.db.retrieve(key.replace(".COMPLETE", "").replace(".Complete", ""))) == 'added':
                        self.log_debug(
                            "%s - Release ignoriert (bereits gefunden)" % key)
                    elif self.filename == 'MB_Filme':
                        retail = False
                        if (self.config.get('enforcedl') and '.dl.' in key.lower()) or not self.config.get(
                                'enforcedl'):
                            if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                                if self.config.get('enforcedl'):
                                    if common.cutoff(key, '1'):
                                        retail = True
                                else:
                                    if common.cutoff(key, '0'):
                                        retail = True
                        common.write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler"
                        )
                        self.db.store(
                            key,
                            'notdl' if self.config.get(
                                'enforcedl') and '.dl.' not in key.lower() else 'added'
                        )
                        log_entry = '[Film] - ' + ('<b>Englisch</b> - ' if englisch and not retail else "") + ('<b>Englisch/Retail</b> - ' if englisch and retail else "") + ('<b>Retail</b> - ' if not englisch and retail else "") + key + ' - <a href="' + download_link + \
                            '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                            key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                        self.log_info(log_entry)
                        added_items.append(log_entry)
                    elif self.filename == 'MB_3D':
                        retail = False
                        if (self.config.get('enforcedl') and '.dl.' in key.lower()) or not self.config.get(
                                'enforcedl'):
                            if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                                if self.config.get('enforcedl'):
                                    if common.cutoff(key, '2'):
                                        retail = True
                        common.write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler"
                        )
                        self.db.store(
                            key,
                            'notdl' if self.config.get(
                                'enforcedl') and '.dl.' not in key.lower() else 'added'
                        )
                        log_entry = '[Film] - <b>' + ('Retail/' if retail else "") + '3D</b> - ' + key + ' - <a href="' + download_link + '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                            key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                        self.log_info(log_entry)
                        added_items.append(log_entry)
                    elif self.filename == 'MB_Staffeln':
                        common.write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler"
                        )
                        self.db.store(
                            key.replace(".COMPLETE", "").replace(
                                ".Complete", ""),
                            'notdl' if self.config.get(
                                'enforcedl') and '.dl.' not in key.lower() else 'added'
                        )
                        log_entry = '[Staffel] - ' + key.replace(
                            ".COMPLETE.", ".") + ' - [<a href="' + download_link + '" target="_blank">Link</a>]'
                        self.log_info(log_entry)
                        added_items.append(log_entry)
                    else:
                        common.write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler"
                        )
                        self.db.store(
                            key,
                            'notdl' if self.config.get(
                                'enforcedl') and '.dl.' not in key.lower() else 'added'
                        )
                        log_entry = '[Film/Serie/RegEx] - ' + key + ' - <a href="' + download_link + \
                            '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                            key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                        self.log_info(log_entry)
                        added_items.append(log_entry)


if __name__ == "__main__":
    arguments = docopt(__doc__, version='RSScrawler')

    log_level = logging.__dict__[
        arguments['--log-level']] if arguments['--log-level'] in logging.__dict__ else logging.INFO
    log_file = os.path.join(os.path.dirname(sys.argv[0]), 'RSScrawler.log')
    log_format = '%(asctime)s - %(message)s'

    print("┌────────────────────────────────────────────────────────┐")
    print("  Programminfo:    RSScrawler " + version + " von RiX")
    print("  Projektseite:    https://github.com/rix1337/RSScrawler")
    print("└────────────────────────────────────────────────────────┘")

    if not os.path.exists(os.path.join(os.path.dirname(sys.argv[0]), 'RSScrawler.ini')):
        if not arguments['--jd-pfad']:
            if arguments['--port']:
                files.startup(
                    "Muss unbedingt vergeben werden!", arguments['--port'])
            else:
                files.startup("Muss unbedingt vergeben werden!", "9090")
                print('Der Ordner "Einstellungen" wurde erstellt.')
                print(
                    'Der Pfad des JDownloaders muss jetzt unbedingt in der RSScrawler.ini hinterlegt werden.')
                print(
                    'Die Einstellungen und Listen sind beim nächsten Start im Webinterface anpassbar.')
                print('Viel Spass! Beende RSScrawler!')
                sys.exit(0)
        else:
            if arguments['--port']:
                files.startup(arguments['--jd-pfad'], arguments['--port'])
            else:
                files.startup(arguments['--jd-pfad'], "9090")
                print('Der Ordner "Einstellungen" wurde erstellt.')
                print('Die Einstellungen und Listen sind jetzt im Webinterface anpassbar.')
    elif arguments['--jd-pfad'] and arguments['--port']:
        files.startup(arguments['--jd-pfad'], arguments['--port'])
    elif arguments['--jd-pfad']:
        files.startup(arguments['--jd-pfad'], None)
    elif arguments['--port']:
        files.startup(None, arguments['--port'])

    rsscrawler = RssConfig('RSScrawler')

    if arguments['--jd-pfad']:
        jdownloaderpath = arguments['--jd-pfad']
    else:
        jdownloaderpath = rsscrawler.get("jdownloader")
    if arguments['--docker']:
        jdownloaderpath = '/jd2'
    jdownloaderpath = jdownloaderpath.replace("\\", "/")
    jdownloaderpath = jdownloaderpath[:-
                                      1] if jdownloaderpath.endswith('/') else jdownloaderpath

    if arguments['--docker']:
        print('Docker-Modus: JDownloader-Pfad und Port können nur per Docker-Run angepasst werden!')

    if jdownloaderpath == 'Muss unbedingt vergeben werden!':
        print('Der Pfad des JDownloaders muss unbedingt in der RSScrawler.ini hinterlegt werden.')
        print('Weiterhin sollten die Listen entsprechend der README.md gefüllt werden!')
        print('Beende RSScrawler...')
        sys.exit(0)

    print('Nutze das "folderwatch" Unterverzeichnis von "' +
          jdownloaderpath + '" für Crawljobs')

    if not os.path.exists(jdownloaderpath):
        print('Der Pfad des JDownloaders existiert nicht.')
        print('Beende RSScrawler...')
        sys.exit(0)

    if not os.path.exists(jdownloaderpath + "/folderwatch"):
        print('Der Pfad des JDownloaders enthält nicht das "folderwatch" Unterverzeichnis. Sicher, dass der Pfad stimmt?')
        print('Beende RSScrawler...')
        sys.exit(0)

    if arguments['--port']:
        port = int(arguments['--port'])
    else:
        port = port = int(rsscrawler.get("port"))
    docker = False
    if arguments['--docker']:
        port = int('9090')
        docker = True

    if rsscrawler.get("prefix"):
        prefix = '/' + rsscrawler.get("prefix")
    else:
        prefix = ''
    if not arguments['--docker']:
        print('Der Webserver ist erreichbar unter http://' +
              common.checkIp() + ':' + str(port) + prefix)

    p = Process(target=web_server, args=(
        port, docker, jdownloaderpath, log_level, log_file, log_format))
    p.start()

    if not arguments['--testlauf']:
        c = Process(target=crawler, args=(jdownloaderpath,
                                          rsscrawler, log_level, log_file, log_format,))
        c.start()

        print('Drücke [Strg] + [C] zum Beenden')

        def signal_handler(signal, frame):
            print('Beende RSScrawler...')
            p.terminate()
            c.terminate()
            sys.exit(0)
        signal.signal(signal.SIGINT, signal_handler)

        try:
            while True:
                signal.pause()
        except AttributeError:
            while True:
                time.sleep(1)
    else:
        crawler(jdownloaderpath, rsscrawler, log_level, log_file, log_format)
        p.terminate()
        sys.exit(0)
