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
  RSScrawler.py [--config="<CFGPFAD>"]
                [--testlauf]
                [--docker]
                [--port=<PORT>]
                [--jd-pfad="<JDPATH>"]
                [--cdc-reset]
                [--log-level=<LOGLEVEL>]

Options:
  --config="<CFGPFAD>"      Legt den Ablageort für Einstellungen und Logs fest
  --testlauf                Einmalige Ausführung von RSScrawler
  --docker                  Sperre Pfad und Port auf Docker-Standardwerte (um falsche Einstellungen zu vermeiden)
  --port=<PORT>             Legt den Port des Webservers fest
  --jd-pfad="<JDPFAD>"      Legt den Pfad von JDownloader fest um nicht die RSScrawler.ini direkt bearbeiten zu müssen
  --cdc-reset               Leert die CDC-Tabelle (Feed ab hier bereits gecrawlt) vor dem ersten Suchlauf
  --log-level=<LOGLEVEL>    Legt fest, wie genau geloggt wird (CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET )
"""

import hashlib
import logging
import os
import random
import re
import signal
import sys
import time
import traceback
import warnings
from datetime import datetime
from logging import handlers
from multiprocessing import Process

import feedparser
import six
from bs4 import BeautifulSoup
from dateutil import parser
from docopt import docopt
from six.moves.urllib.error import HTTPError

from rsscrawler import common
from rsscrawler import files
from rsscrawler import version
from rsscrawler.common import decode_base64
from rsscrawler.common import fullhd_title
from rsscrawler.myjd import get_device
from rsscrawler.myjd import get_if_one_device
from rsscrawler.notifiers import notify
from rsscrawler.ombi import ombi
from rsscrawler.output import CutLog
from rsscrawler.output import Unbuffered
from rsscrawler.rssconfig import RssConfig
from rsscrawler.rssdb import ListDb
from rsscrawler.rssdb import RssDb
from rsscrawler.url import check_url
from rsscrawler.url import get_url
from rsscrawler.url import get_url_headers
from rsscrawler.web import start

version = version.get_version()


def web_server(port, docker, jd, cfg, db, log_level, log_file, log_format, device):
    start(port, docker, jd, cfg, db, log_level, log_file, log_format, device)


def crawler(jdpath, cfgfile, dfile, rssc, log_level, log_file, log_format, device):
    global added_items
    added_items = []
    global jdownloaderpath
    jdownloaderpath = jdpath
    global rsscrawler
    rsscrawler = rssc
    global configfile
    configfile = cfgfile
    global dbfile
    dbfile = dfile

    sys.stdout = Unbuffered(sys.stdout)

    logger = logging.getLogger('')
    logger.setLevel(log_level)

    console = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter(log_format)
    console.setFormatter(CutLog(log_format))
    console.setLevel(log_level)

    logfile = logging.handlers.RotatingFileHandler(log_file)
    logfile.setFormatter(formatter)
    logfile.setLevel(logging.INFO)

    logger.addHandler(logfile)
    logger.addHandler(console)

    if log_level == 10:
        logfile_debug = logging.handlers.RotatingFileHandler(
            log_file.replace("RSScrawler.log", "RSScrawler_DEBUG.log"), maxBytes=100000, backupCount=5)
        logfile_debug.setFormatter(formatter)
        logfile_debug.setLevel(10)
        logger.addHandler(logfile_debug)

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
        BL(filename='MB_Regex'),
        BL(filename='IMDB'),
        BL(filename='MB_Filme'),
        BL(filename='MB_Staffeln'),
        BL(filename='MB_3D')
    ]
    arguments = docopt(__doc__, version='RSScrawler')
    if not arguments['--testlauf']:
        while True:
            try:
                check_url(configfile, dbfile)
                start_time = time.time()
                log_debug("--------Alle Suchfunktion gestartet.--------")
                ombi(configfile, dbfile, jdownloaderpath, log_debug)
                for task in search_pool:
                    task.periodical_task()
                    log_debug("-----------Suchfunktion ausgeführt!-----------")
                end_time = time.time()
                total_time = end_time - start_time
                total_unit = " Sekunden"
                if total_time > 60:
                    total_time = total_time / 60
                    total_unit = " Minuten"
                total_time = str(round(total_time, 1)) + total_unit
                notify(added_items, configfile)
                added_items = []
                interval = int(rsscrawler.get('interval')) * 60
                random_range = random.randrange(0, interval // 4)
                wait = interval + random_range
                log_debug(
                    "-----Alle Suchfunktion ausgeführt (Dauer: " + total_time + ")! Warte " + str(wait) + " Sekunden.")
                print(time.strftime("%Y-%m-%d %H:%M:%S") +
                      u" - Alle Suchfunktion ausgeführt (Dauer: " + total_time + ")! Warte " + str(wait) + " Sekunden.")
                time.sleep(wait)
                log_debug("-------------Wartezeit verstrichen-------------")
            except Exception:
                traceback.print_exc()
    else:
        try:
            check_url(configfile, dbfile)
            start_time = time.time()
            log_debug("--------Testlauf gestartet.--------")
            ombi(configfile, dbfile, jdownloaderpath, log_debug)
            for task in search_pool:
                task.periodical_task()
                log_debug("-----------Suchfunktion ausgeführt!-----------")
            end_time = time.time()
            total_time = end_time - start_time
            total_unit = " Sekunden"
            if total_time > 60:
                total_time = total_time / 60
                total_unit = " Minuten"
            total_time = str(round(total_time, 1)) + total_unit
            notify(added_items, configfile)
            log_debug(
                "---Testlauf ausgeführt (Dauer: " + total_time + ")!---")
            print(time.strftime("%Y-%m-%d %H:%M:%S") +
                  u" - Testlauf ausgeführt (Dauer: " + total_time + ")!")
        except Exception:
            traceback.print_exc()


class YT:
    _INTERNAL_NAME = 'YT'

    def __init__(self):
        self.config = RssConfig(self._INTERNAL_NAME, configfile)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.db = RssDb(dbfile, 'rsscrawler')
        self.youtube = 'YT_Channels'
        self.dictWithNamesAndLinks = {}

    def read_input(self, liste):
        cont = ListDb(dbfile, liste).retrieve()
        return cont if cont else ""

    def periodical_task(self):
        if not self.config.get('youtube'):
            self.log_debug("Suche für YouTube deaktiviert!")
            return
        channels = []
        videos = []
        self.allInfos = self.read_input(self.youtube)

        for item in self.allInfos:
            if len(item) > 0:
                if self.config.get("youtube") is False:
                    self.log_debug(
                        "Liste ist leer. Stoppe Suche für YouTube!")
                    return
                channels.append(item)

        for channel in channels:
            if 'list=' in channel:
                id_cutter = channel.rfind('list=') + 5
                channel = channel[id_cutter:]
                url = 'https://www.youtube.com/playlist?list=' + channel
                response = get_url(url, configfile, dbfile)
            else:
                url = 'https://www.youtube.com/user/' + channel + '/videos'
                urlc = 'https://www.youtube.com/channel/' + channel + '/videos'
                cnotfound = False
                try:
                    response = get_url(url, configfile, dbfile)
                except HTTPError:
                    try:
                        response = get_url(urlc, configfile, dbfile)
                    except HTTPError:
                        cnotfound = True
                    if cnotfound:
                        self.log_debug("YouTube-Kanal: " +
                                       channel + " nicht gefunden!")
                        return

            links = re.findall(
                r'VideoRenderer":{"videoId":"(.*?)",".*?[Tt]ext":"(.*?)"}', response)

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
                        [link[0], link[1], channel])

        for video in videos:
            channel = video[2]
            title = video[1]
            if "[private" in title.lower() and "video]" in title.lower():
                self.log_debug(
                    "[%s] - YouTube-Video ignoriert (Privates Video)" % video)
                continue
            video_title = title.replace("&amp;", "&").replace("&gt;", ">").replace(
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
                        "RSScrawler",
                        configfile
                    )
                    self.db.store(
                        video,
                        'added'
                    )
                    log_entry = '[YouTube] - ' + video_title + ' (' + channel + ') - <a href="' + download_link + '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                                video + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                    self.log_info(log_entry)
                    added_items.append(log_entry)


class DD:
    _INTERNAL_NAME = 'DD'

    def __init__(self):
        self.config = RssConfig(self._INTERNAL_NAME, configfile)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.db = RssDb(dbfile, 'rsscrawler')

    def periodical_task(self):
        feeds = self.config.get("feeds")
        if feeds:
            feeds = feeds.replace(" ", "").split(',')
            hoster = re.compile(self.config.get("hoster"))
            for feed in feeds:
                feed = feedparser.parse(get_url(feed, configfile, dbfile))
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
                            if re.match(hoster, link):
                                links.append(str(link))
                        if not links:
                            self.log_debug(
                                "%s - Release ignoriert (kein passender Link gefunden)" % key)
                        elif self.db.retrieve(key) == 'added':
                            self.log_debug(
                                "%s - Release ignoriert (bereits gefunden)" % key)
                        else:
                            common.write_crawljob_file(
                                key,
                                key,
                                links,
                                jdownloaderpath + "/folderwatch",
                                "RSScrawler",
                                configfile
                            )
                            self.db.store(
                                key,
                                'added'
                            )
                            log_entry = '[DD] - <b>Englisch</b> - ' + key + ' - <a href="' + feed_link + \
                                        '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                                        key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                            self.log_info(log_entry)
                            added_items.append(log_entry)
                    else:
                        self.log_debug(
                            "%s - Releasezeitpunkt weniger als 30 Minuten in der Vergangenheit - wird ignoriert." % key)


class SJ:
    def __init__(self, filename, internal_name):
        self._INTERNAL_NAME = internal_name
        self.config = RssConfig(self._INTERNAL_NAME, configfile)
        self.rsscrawler = RssConfig("RSScrawler", configfile)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.filename = filename
        self.db = RssDb(dbfile, 'rsscrawler')

        self.cdc = RssDb(dbfile, 'cdc')
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

    def periodical_task(self):
        self.pattern = "|".join(self.get_series_list(
            self.filename, self.level)).lower()

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
        self.hoster = re.compile(self.config.get("hoster"))
        set_sj = str(self.settings) + str(self.pattern)
        set_sj = hashlib.sha256(set_sj.encode(
            'ascii', 'ignore')).hexdigest()

        if self.last_set_sj == set_sj:
            if self.filename == "MB_Staffeln" or self.filename == "SJ_Staffeln_Regex":
                response = get_url_headers(
                    decode_base64('aHR0cDovL3Nlcmllbmp1bmtpZXMub3JnL3htbC9mZWVkcy9zdGFmZmVsbi54bWw='), configfile,
                    dbfile,
                    self.headers)
                feed = feedparser.parse(response.content)
            else:
                response = get_url_headers(
                    decode_base64('aHR0cDovL3Nlcmllbmp1bmtpZXMub3JnL3htbC9mZWVkcy9lcGlzb2Rlbi54bWw='), configfile,
                    dbfile,
                    self.headers)
                feed = feedparser.parse(response.content)
            if response.status_code == 304:
                self.log_debug(
                    "SJ-Feed seit letztem Aufruf nicht aktualisiert - breche  Suche ab!")
                return
            header = True
        else:
            if self.filename == "MB_Staffeln" or self.filename == "SJ_Staffeln_Regex":
                feed = feedparser.parse(get_url(
                    decode_base64('aHR0cDovL3Nlcmllbmp1bmtpZXMub3JnL3htbC9mZWVkcy9zdGFmZmVsbi54bWw='), configfile,
                    dbfile))
            else:
                feed = feedparser.parse(get_url(
                    decode_base64('aHR0cDovL3Nlcmllbmp1bmtpZXMub3JnL3htbC9mZWVkcy9lcGlzb2Rlbi54bWw='), configfile,
                    dbfile))
            header = False

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
                                try:
                                    storage = self.db.retrieve(title)
                                except Exception as e:
                                    self.log_debug(
                                        "Fehler bei Datenbankzugriff: %s, Grund: %s" % (e, title))
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
                                try:
                                    storage = self.db.retrieve(title)
                                except Exception as e:
                                    self.log_debug(
                                        "Fehler bei Datenbankzugriff: %s, Grund: %s" % (e, title))
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
        if header:
            self.cdc.delete("SJHeaders-" + self.filename)
            self.cdc.store("SJHeaders-" + self.filename, response.headers['Last-Modified'])

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
                        self.range_parse(link, title1, englisch, title)
                    else:
                        title1 = title_cut[0][0] + "0" + \
                                 str(count) + ".*" + title_cut[0][-1].replace(
                            "(", ".*").replace(")", ".*").replace("+", ".*")
                        self.range_parse(link, title1, englisch, title)
            except ValueError as e:
                logging.error("Fehler in Variablenwert: " + e)
        self.parse_download(link, title, englisch)

    def range_parse(self, series_url, search_title, englisch, fallback_title):
        req_page = get_url(series_url, configfile, dbfile)
        soup = BeautifulSoup(req_page, 'lxml')
        try:
            titles = soup.findAll(text=re.compile(search_title))
            if not titles:
                titles = soup.findAll(text=re.compile(fallback_title))
            for title in titles:
                if self.quality != '480p' and self.quality in title:
                    self.parse_download(series_url, title, englisch)
                if self.quality == '480p' and not (('.720p.' in title) or ('.1080p.' in title) or ('.2160p.' in title)):
                    self.parse_download(series_url, title, englisch)
        except re.error as e:
            self.log_error('Konstantenfehler: %s' % e)

    def parse_download(self, series_url, search_title, englisch):
        req_page = get_url(series_url, configfile, dbfile)
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
                    self.send_package(search_title, links, englisch)
            else:
                self.log_debug(search_title + " - Release hat falsche Quelle")

    def send_package(self, title, links, englisch_info):
        link = links[0]
        englisch = ""
        if englisch_info:
            englisch = "<b>Englisch</b> - "
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
        if storage == 'added':
            self.log_debug(title + " - Release ignoriert (bereits gefunden)")
        else:
            common.write_crawljob_file(
                title, title, links, jdownloaderpath + "/folderwatch", "RSScrawler", configfile)
            self.db.store(title, 'added')
            log_entry = link_placeholder + title + ' - <a href="' + link + \
                        '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                        title + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
            self.log_info(log_entry)
            added_items.append(log_entry)

    def get_series_list(self, liste, series_type):
        loginfo = ""
        if series_type == 1:
            loginfo = " (RegEx)"
        elif series_type == 2:
            loginfo = " (Staffeln)"
        elif series_type == 3:
            loginfo = " (Staffeln/RegEx)"
        cont = ListDb(dbfile, liste).retrieve()
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


class BL:
    _INTERNAL_NAME = 'MB'
    MB_URL = decode_base64("aHR0cDovL21vdmllLWJsb2cudG8vZmVlZC8=")
    MB_FEED_URLS = [MB_URL]
    HW_URL = decode_base64("aHR0cDovL2hkLXdvcmxkLm9yZy9mZWVkLw==")
    HW_FEED_URLS = [HW_URL]
    SUBSTITUTE = r"[&#\s/]"

    def __init__(self, filename):
        self.config = RssConfig(self._INTERNAL_NAME, configfile)
        self.rsscrawler = RssConfig("RSScrawler", configfile)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.filename = filename
        self.db = RssDb(dbfile, 'rsscrawler')
        self.db_retail = RssDb(dbfile, 'retail')
        self.hoster = re.compile(self.config.get("hoster"))

        search = int(RssConfig(self._INTERNAL_NAME, configfile).get("search"))
        self.historical = False
        if search == 99:
            self.historical = True
            search = 3
        i = 2
        while i <= search:
            self.MB_FEED_URLS.append(self.MB_URL + "?paged=" + str(i))
            i += 1

        i = 2
        while i <= search:
            self.HW_FEED_URLS.append(self.HW_URL + "?paged=" + str(i))
            i += 1

        self.cdc = RssDb(dbfile, 'cdc')

        self.last_set_mbhw = self.cdc.retrieve("MBHWSet-" + self.filename)
        self.headers_mb = {'If-Modified-Since': str(self.cdc.retrieve("MBHeaders-" + self.filename))}
        self.headers_hw = {'If-Modified-Since': str(self.cdc.retrieve("HWHeaders-" + self.filename))}

        self.last_sha_mb = self.cdc.retrieve("MB-" + self.filename)
        self.last_sha_hw = self.cdc.retrieve("HW-" + self.filename)
        settings = ["quality", "ignore", "search", "regex", "cutoff", "crawl3d", "crawl3dtype", "enforcedl",
                    "crawlseasons", "seasonsquality", "seasonpacks", "seasonssource", "imdbyear", "imdb", "hoster"]
        self.settings = []
        self.settings.append(self.rsscrawler.get("english"))
        self.settings.append(self.rsscrawler.get("surround"))
        for s in settings:
            self.settings.append(self.config.get(s))
        self.i_mb_done = False
        self.i_hw_done = False
        self.mb_done = False
        self.hw_done = False
        self.dl_unsatisfied = False

        try:
            self.imdb = float(self.config.get('imdb'))
        except:
            self.imdb = 0.0
        self.dictWithNamesAndLinks = {}
        self.empty_list = False

    def read_input(self, liste):
        cont = ListDb(dbfile, liste).retrieve()
        if not cont:
            self.empty_list = True
            return ""
        else:
            return cont

    def get_patterns(self, patterns, **kwargs):
        if not patterns:
            self.empty_list = True
        if kwargs:
            return {line: (kwargs['quality'], kwargs['rg'], kwargs['sf']) for line in patterns}
        return {x: x for x in patterns}

    def search_links(self, feed, site):
        if self.empty_list:
            return
        ignore = "|".join(
            [r"\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if self.config.get(
            "ignore") else r"^unmatchable$"

        for key in self.allInfos:
            s = re.sub(self.SUBSTITUTE, ".", "^" + key).lower()
            settings = str(self.settings)
            liste = str(self.allInfos)
            for post in feed.entries:
                concat = post.title + post.published + \
                         settings + liste
                sha = hashlib.sha256(concat.encode(
                    'ascii', 'ignore')).hexdigest()
                if ("MB" in site and sha == self.last_sha_mb) or ("HW" in site and sha == self.last_sha_hw):
                    if not self.historical:
                        self.log_debug(
                            site + "-Feed ab hier bereits gecrawlt (" + post.title + ") " + "- breche Suche nach '" + key + "' ab!")
                        if "MB" in site:
                            self.mb_done = True
                        elif "HW" in site:
                            self.hw_done = True
                        break

                found = re.search(s, post.title.lower())
                if found:
                    content = post.content[0].value
                    if re.search(r'.*([mM][kK][vV]).*', content):
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
                                    yield (post.title, content, key)
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
                                    yield (post.title, content, key)

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
                                    yield (post.title, content, key)
                        else:
                            yield (post.title, content, key)

    def download_dl(self, title):
        search_title = fullhd_title(title).split('.x264-', 1)[0].split('.h264-', 1)[0].replace(".", " ").replace(" ",
                                                                                                                 "+")
        search_url = decode_base64("aHR0cDovL21vdmllLWJsb2cudG8vc2VhcmNoLw==") + search_title + "/feed/rss2/"
        feedsearch_title = fullhd_title(title).split('.x264-', 1)[0].split('.h264-', 1)[0]
        if not '.dl.' in feedsearch_title.lower():
            self.log_debug(
                "%s - Release ignoriert (nicht zweisprachig, da wahrscheinlich nicht Retail)" % feedsearch_title)
            return False
        for (key, value, pattern) in self.dl_search(feedparser.parse(get_url(search_url, configfile, dbfile)),
                                                    feedsearch_title):
            download_links = self._get_download_links(value)
            if download_links:
                for download_link in download_links:
                    if decode_base64("bW92aWUtYmxvZy50by8=") in download_link:
                        self.log_debug("Fake-Link erkannt!")
                        break
                download_link = download_links[0]
                if str(self.db.retrieve(key)) == 'added' or str(self.db.retrieve(key)) == 'dl' or str(
                        self.db.retrieve(key.replace(".COMPLETE", "").replace(".Complete", ""))) == 'added':
                    self.log_debug(
                        "%s - zweisprachiges Release ignoriert (bereits gefunden)" % key)
                    return True
                elif self.filename == 'MB_Filme' or 'IMDB':
                    retail = False
                    if self.config.get('cutoff'):
                        if self.config.get('enforcedl'):
                            if common.cutoff(key, '1', dbfile):
                                retail = True
                        else:
                            if common.cutoff(key, '0', dbfile):
                                retail = True
                    common.write_crawljob_file(
                        key,
                        key,
                        download_links,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler/Remux",
                        configfile
                    )
                    self.db.store(
                        key,
                        'dl' if self.config.get(
                            'enforcedl') and '.dl.' in key.lower() else 'added'
                    )
                    log_entry = '[Film] - <b>' + (
                        'Retail/' if retail else "") + 'Zweisprachig</b> - ' + key + ' - <a href="' + download_link + \
                                '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                                key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                    self.log_info(log_entry)
                    added_items.append(log_entry)
                    return True
                elif self.filename == 'MB_3D':
                    retail = False
                    if self.config.get('cutoff'):
                        if common.cutoff(key, '2', dbfile):
                            retail = True
                    common.write_crawljob_file(
                        key,
                        key,
                        download_links,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler/3Dcrawler",
                        configfile
                    )
                    self.db.store(
                        key,
                        'dl' if self.config.get(
                            'enforcedl') and '.dl.' in key.lower() else 'added'
                    )
                    log_entry = '[Film] - <b>' + (
                        'Retail/' if retail else "") + '3D/Zweisprachig</b> - ' + key + ' - <a href="' + download_link + \
                                '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                                key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                    self.log_info(log_entry)
                    added_items.append(log_entry)
                    return True
                elif self.filename == 'MB_Regex':
                    common.write_crawljob_file(
                        key,
                        key,
                        download_links,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler",
                        configfile
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
                        download_links,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler/Remux",
                        configfile
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
            [r"\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if self.config.get(
            "ignore") else r"^unmatchable$"

        s = re.sub(self.SUBSTITUTE, ".", title).lower()
        for post in feed.entries:
            found = re.search(s, post.title.lower())
            if found:
                content = post.content[0].value
                found = re.search(ignore, post.title.lower())
                if found:
                    self.log_debug(
                        "%s - zweisprachiges Release ignoriert (basierend auf ignore-Einstellung)" % post.title)
                    continue
                yield (post.title, content, title)

    def imdb_search(self, imdb, feed, site):
        settings = str(self.settings)
        score = str(self.imdb)
        for post in feed.entries:
            concat = post.title + post.published + \
                     settings + score
            sha = hashlib.sha256(concat.encode(
                'ascii', 'ignore')).hexdigest()
            if ("MB" in site and sha == self.last_sha_mb) or ("HW" in site and sha == self.last_sha_hw):
                self.log_debug(
                    site + "-Feed ab hier bereits gecrawlt (" + post.title + ") - breche Suche ab!")
                if "MB" in site:
                    self.i_mb_done = True
                elif "HW" in site:
                    self.i_hw_done = True
                break
            content = post.content[0].value
            if "mkv" in content.lower():
                post_imdb = re.findall(
                    r'.*?(?:href=.?http(?:|s):\/\/(?:|www\.)imdb\.com\/title\/(tt[0-9]{7,9}).*?).*?(\d(?:\.|\,)\d)(?:.|.*?)<\/a>.*?',
                    content)

                if post_imdb:
                    post_imdb = post_imdb.pop()
                replaced = common.retail_sub(post.title)
                retailtitle = self.db_retail.retrieve(replaced[0])
                retailyear = self.db_retail.retrieve(replaced[1])
                if str(self.db.retrieve(post.title)) == 'added' or str(self.db.retrieve(post.title)) == 'notdl' or str(
                        self.db.retrieve(post.title.replace(".COMPLETE", "").replace(".Complete", ""))) == 'added':
                    self.log_debug(
                        "%s - Release ignoriert (bereits gefunden)" % post.title)
                    continue
                elif retailtitle == 'retail' or retailyear == 'retail':
                    self.log_debug(
                        "%s - Release ignoriert (Retail-Release bereits gefunden)" % post.title)
                    continue
                quality_set = self.config.get('quality')
                if '.3d.' not in post.title.lower():
                    if quality_set == "480p":
                        if "720p" in post.title.lower() or "1080p" in post.title.lower() or "1080i" in post.title.lower() or "2160p" in post.title.lower():
                            quality_match = False
                    else:
                        quality_match = re.search(
                            quality_set, post.title.lower())
                    if not quality_match:
                        self.log_debug(
                            "%s - Release ignoriert (falsche Aufloesung)" % post.title)
                        continue
                else:
                    if not self.config.get('crawl3d'):
                        self.log_debug(
                            "%s - Release ignoriert (3D-Suche deaktiviert)" % post.title)
                        return
                    if self.config.get('crawl3d') and ("1080p" in post.title.lower() or "1080i" in post.title.lower()):
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
                    else:
                        continue

                ignore = "|".join(
                    [r"\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if self.config.get(
                    "ignore") else r"^unmatchable$"
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
                season = re.search(r'\.S(\d{1,3})(\.|-|E)', post.title)
                if season:
                    self.log_debug(
                        "%s - Release ignoriert (IMDB sucht nur Filme)" % post.title)
                    continue

                year_in_title = re.findall(
                    r"\.((?:19|20)\d{2})\.", post.title)
                years_in_title = len(year_in_title)
                if years_in_title > 0:
                    title_year = year_in_title[years_in_title - 1]
                else:
                    title_year = ""

                download_pages = self._get_download_links(content)

                if post_imdb:
                    download_imdb = "http://www.imdb.com/title/" + post_imdb[0]
                else:
                    try:
                        search_title = \
                            re.findall(r"(.*?)(?:\.(?:(?:19|20)\d{2})|\.German|\.\d{3,4}p|\.S(?:\d{1,3})\.)",
                                       post.title)[
                                0].replace(
                                ".", "+").replace("ae", u"ä").replace("oe", u"ö").replace("ue", u"ü").replace("Ae",
                                                                                                              u"Ä").replace(
                                "Oe", u"Ö").replace("Ue", u"Ü")
                    except:
                        break
                    search_url = "http://www.imdb.com/find?q=" + search_title
                    search_page = get_url(search_url, configfile, dbfile)
                    search_results = re.findall(
                        r'<td class="result_text"> <a href="\/title\/(tt[0-9]{7,9})\/\?ref_=fn_al_tt_\d" >(.*?)<\/a>.*? \((\d{4})\)..(.{9})',
                        search_page)
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
                                "%s - Keine passende Film-IMDB-Seite gefunden" % post.title)

                details = ""
                min_year = self.config.get("imdbyear")
                if min_year:
                    if len(title_year) > 0:
                        if title_year < min_year:
                            self.log_debug(
                                "%s - Release ignoriert (Film zu alt)" % post.title)
                            continue
                    elif len(download_imdb) > 0:
                        details = get_url(download_imdb, configfile, dbfile)
                        if not details:
                            self.log_debug(
                                "%s - Fehler bei Aufruf der IMDB-Seite" % post.title)
                            continue
                        title_year = re.findall(
                            r"<title>(?:.*) \(((?:19|20)\d{2})\) - IMDb<\/title>", details)
                        if not title_year:
                            self.log_debug(
                                "%s - Erscheinungsjahr nicht ermittelbar" % post.title)
                            continue
                        else:
                            title_year = title_year[0]
                        if title_year < min_year:
                            self.log_debug(
                                "%s - Release ignoriert (Film zu alt)" % post.title)
                            continue
                if len(download_imdb) > 0:
                    if len(details) == 0:
                        details = get_url(download_imdb, configfile, dbfile)
                    if not details:
                        self.log_debug(
                            "%s - Release ignoriert (Film zu alt)" % post.title)
                        continue
                    vote_count = re.findall(
                        r'ratingCount">(.*?)<\/span>', details)
                    if not vote_count:
                        self.log_debug(
                            "%s - Wertungsanzahl nicht ermittelbar" % post.title)
                        continue
                    else:
                        vote_count = int(vote_count[0].replace(
                            ".", "").replace(",", ""))
                    if vote_count < 1500:
                        self.log_debug(
                            post.title + " - Release ignoriert (Weniger als 1500 IMDB-Votes: " + str(vote_count) + ")")
                        continue
                    download_score = re.findall(
                        r'ratingValue">(.*?)<\/span>', details)
                    download_score = float(download_score[0].replace(
                        ",", "."))
                    if download_score > imdb:
                        if '.3d.' not in post.title.lower():
                            self.download_imdb(
                                post.title, download_pages, str(download_score), download_imdb, details)
                        else:
                            self.download_imdb(
                                post.title, download_pages, str(download_score), download_imdb, details)

    def download_imdb(self, key, download_links, score, download_imdb, details):
        if download_links:
            for download_link in download_links:
                url = decode_base64("bW92aWUtYmxvZy50by8=")
                if url in download_link:
                    self.log_debug("Fake-Link erkannt!")
                    break
            download_link = download_links[0]
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
                    details = get_url(download_imdb, configfile, dbfile)
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

            if '.3d.' not in key.lower():
                retail = False
                if (self.config.get('enforcedl') and '.dl.' in key.lower()) or not self.config.get(
                        'enforcedl'):
                    if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                        if self.config.get('enforcedl'):
                            if common.cutoff(key, '1', dbfile):
                                retail = True
                        else:
                            if common.cutoff(key, '0', dbfile):
                                retail = True
                common.write_crawljob_file(
                    key,
                    key,
                    download_links,
                    jdownloaderpath + "/folderwatch",
                    "RSScrawler",
                    configfile
                )
                self.db.store(
                    key,
                    'notdl' if self.config.get(
                        'enforcedl') and '.dl.' not in key.lower() else 'added'
                )
                log_entry = '[IMDB ' + score + '/Film] - ' + (
                    '<b>Englisch</b> - ' if englisch and not retail else "") + (
                                '<b>Englisch/Retail</b> - ' if englisch and retail else "") + (
                                '<b>Retail</b> - ' if not englisch and retail else "") + key + ' - <a href="' + \
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
                            if common.cutoff(key, '2', dbfile):
                                retail = True
                common.write_crawljob_file(
                    key,
                    key,
                    download_links,
                    jdownloaderpath + "/folderwatch",
                    "RSScrawler/3Dcrawler",
                    configfile
                )
                self.db.store(
                    key,
                    'notdl' if self.config.get(
                        'enforcedl') and '.dl.' not in key.lower() else 'added'
                )
                log_entry = '[IMDB ' + score + '/Film] - <b>' + (
                    'Retail/' if retail else "") + '3D</b> - ' + key + ' - <a href="' + download_link + \
                            '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                            key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                self.log_info(log_entry)
                added_items.append(log_entry)

    def _get_download_links(self, content):
        url_hosters = re.findall(r'href="([^"\'>]*)".+?(.+?)<', content)
        links = {}
        for url_hoster in reversed(url_hosters):
            url = decode_base64("bW92aWUtYmxvZy50by8=")
            if not url in url_hoster[0] and not "https://goo.gl/" in url_hoster[0]:
                hoster = url_hoster[1].lower().replace('target="_blank">', '')
                if re.match(self.hoster, hoster):
                    links[hoster] = url_hoster[0]
        return links.values() if six.PY2 else list(links.values())

    def feed_download(self, key, content):
        download_links = self._get_download_links(content)
        if download_links:
            for download_link in download_links:
                url = decode_base64("bW92aWUtYmxvZy50by8=")
                if url in download_link:
                    self.log_debug("Fake-Link erkannt!")
                    break
            replaced = common.retail_sub(key)
            retailtitle = self.db_retail.retrieve(replaced[0])
            retailyear = self.db_retail.retrieve(replaced[1])
            if str(self.db.retrieve(key)) == 'added' or str(self.db.retrieve(key)) == 'notdl' or str(
                    self.db.retrieve(key.replace(".COMPLETE", "").replace(".Complete", ""))) == 'added':
                self.log_debug(
                    "%s - Release ignoriert (bereits gefunden)" % key)
                return
            elif retailtitle == 'retail' or retailyear == 'retail':
                self.log_debug(
                    "%s - Release ignoriert (Retail-Release bereits gefunden)" % key)
                return
            download_link = download_links[0]
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

                imdb_id = re.findall(
                    r'.*?(?:href=.?http(?:|s):\/\/(?:|www\.)imdb\.com\/title\/(tt[0-9]{7,9}).*?).*?(\d(?:\.|\,)\d)(?:.|.*?)<\/a>.*?',
                    content)

                if imdb_id:
                    imdb_id = imdb_id[0][0]
                else:
                    search_title = re.findall(
                        r"(.*?)(?:\.(?:(?:19|20)\d{2})|\.German|\.\d{3,4}p|\.S(?:\d{1,3})\.)", key)[0].replace(".", "+")
                    search_url = "http://www.imdb.com/find?q=" + search_title
                    search_page = get_url(search_url, configfile, dbfile)
                    search_results = re.findall(
                        r'<td class="result_text"> <a href="\/title\/(tt[0-9]{7,9})\/\?ref_=fn_al_tt_\d" >(.*?)<\/a>.*? \((\d{4})\)..(.{9})',
                        search_page)
                    total_results = len(search_results)
                    if self.filename == 'MB_Staffeln':
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
                        self.dl_unsatisfied = True
                else:
                    if isinstance(imdb_id, list):
                        imdb_id = imdb_id.pop()
                    imdb_url = "http://www.imdb.com/title/" + imdb_id
                    details = get_url(imdb_url, configfile, dbfile)
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
                            self.dl_unsatisfied = True
                            return
            if self.filename == 'MB_Filme':
                retail = False
                if (self.config.get('enforcedl') and '.dl.' in key.lower()) or not self.config.get(
                        'enforcedl'):
                    if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                        if self.config.get('enforcedl'):
                            if common.cutoff(key, '1', dbfile):
                                retail = True
                        else:
                            if common.cutoff(key, '0', dbfile):
                                retail = True
                else:
                    if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                        if common.cutoff(key, '0', dbfile):
                            retail = True
                common.write_crawljob_file(
                    key,
                    key,
                    download_links,
                    jdownloaderpath + "/folderwatch",
                    "RSScrawler",
                    configfile
                )
                self.db.store(
                    key,
                    'notdl' if self.config.get(
                        'enforcedl') and '.dl.' not in key.lower() else 'added'
                )
                log_entry = '[Film] - ' + ('<b>Englisch</b> - ' if englisch and not retail else "") + (
                    '<b>Englisch/Retail</b> - ' if englisch and retail else "") + (
                                '<b>Retail</b> - ' if not englisch and retail else "") + key + ' - <a href="' + download_link + \
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
                            if common.cutoff(key, '2', dbfile):
                                retail = True
                else:
                    if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                        if common.cutoff(key, '2', dbfile):
                            retail = True
                common.write_crawljob_file(
                    key,
                    key,
                    download_links,
                    jdownloaderpath + "/folderwatch",
                    "RSScrawler/3Dcrawler",
                    configfile
                )
                self.db.store(
                    key,
                    'notdl' if self.config.get(
                        'enforcedl') and '.dl.' not in key.lower() else 'added'
                )
                log_entry = '[Film] - <b>' + (
                    'Retail/' if retail else "") + '3D</b> - ' + key + ' - <a href="' + download_link + '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                            key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                self.log_info(log_entry)
                added_items.append(log_entry)
            elif self.filename == 'MB_Staffeln':
                common.write_crawljob_file(
                    key,
                    key,
                    download_links,
                    jdownloaderpath + "/folderwatch",
                    "RSScrawler",
                    configfile
                )
                self.db.store(
                    key.replace(".COMPLETE", "").replace(
                        ".Complete", ""),
                    'notdl' if self.config.get(
                        'enforcedl') and '.dl.' not in key.lower() else 'added'
                )
                log_entry = '[Staffel] - ' + key.replace(".COMPLETE", "").replace(
                    ".Complete",
                    "") + ' - <a href="' + download_link + '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                            key.replace(".COMPLETE", "").replace(
                                ".Complete",
                                "") + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                self.log_info(log_entry)
                added_items.append(log_entry)
            else:
                common.write_crawljob_file(
                    key,
                    key,
                    download_links,
                    jdownloaderpath + "/folderwatch",
                    "RSScrawler",
                    configfile
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

    def periodical_task(self):
        imdb = self.imdb
        mb_urls = []
        hw_urls = []

        if self.filename == 'MB_Staffeln':
            if not self.config.get('crawlseasons'):
                return
            self.allInfos = dict(
                set({key: value for (key, value) in self.get_patterns(
                    self.read_input(self.filename),
                    quality=self.config.get('seasonsquality'), rg='.*', sf='.complete.'
                ).items()}.items()
                    )
            )
        elif self.filename == 'MB_Regex':
            if not self.config.get('regex'):
                return
            self.allInfos = dict(
                set({key: value for (key, value) in self.get_patterns(
                    self.read_input(self.filename)
                ).items()}.items()
                    ) if self.config.get('regex') else []
            )
        elif self.filename == "IMDB":
            self.allInfos = self.filename
        else:
            if self.filename == 'MB_3D':
                if not self.config.get('crawl3d'):
                    return
            self.allInfos = dict(
                set({key: value for (key, value) in self.get_patterns(
                    self.read_input(self.filename), quality=self.config.get('quality'), rg='.*', sf=None
                ).items()}.items()
                    )
            )
        if self.filename != 'MB_Regex' and self.filename != 'IMDB':
            if self.historical:
                for xline in self.allInfos.keys():
                    if len(xline) > 0 and not xline.startswith("#"):
                        xn = xline.split(",")[0].replace(
                            ".", " ").replace(" ", "+")
                        mb_urls.append(
                            decode_base64('aHR0cDovL21vdmllLWJsb2cudG8=') + '/search/%s/feed/rss2/' % xn)
                        hw_urls.append(decode_base64('aHR0cDovL2hkLXdvcmxkLm9yZw==') + '/search/%s/feed/rss2/' % xn)
            else:
                for URL in self.MB_FEED_URLS:
                    mb_urls.append(URL)
                for URL in self.HW_FEED_URLS:
                    hw_urls.append(URL)
        else:
            for URL in self.MB_FEED_URLS:
                mb_urls.append(URL)
            for URL in self.HW_FEED_URLS:
                hw_urls.append(URL)

        if self.filename != 'IMDB':
            if self.empty_list:
                self.log_debug(
                    "Liste ist leer. Stoppe Suche für Filme! (" + self.filename + ")")
                return
        elif imdb == 0:
            self.log_debug(
                "IMDB-Suchwert ist 0. Stoppe Suche für Filme! (" + self.filename + ")")
            return

        first_mb = get_url_headers(mb_urls[0], configfile, dbfile, self.headers_mb)
        first_hw = get_url_headers(hw_urls[0], configfile, dbfile, self.headers_hw)
        first_page_mb = feedparser.parse(first_mb.content)
        first_page_hw = feedparser.parse(first_hw.content)

        mb_304 = False
        hw_304 = False

        set_mbhw = str(self.settings) + str(self.allInfos)
        set_mbhw = hashlib.sha256(set_mbhw.encode('ascii', 'ignore')).hexdigest()

        if self.last_set_mbhw == set_mbhw:
            if first_mb.status_code == 304:
                mb_304 = True
                mb_urls = []
                self.log_debug("MB-Feed seit letztem Aufruf nicht aktualisiert - breche Suche ab!")

            if first_hw.status_code == 304:
                hw_304 = True
                hw_urls = []
                self.log_debug("HW-Feed seit letztem Aufruf nicht aktualisiert - breche Suche ab!")

        if mb_304 and hw_304:
            return

        sha_mb = None
        sha_hw = None

        if not self.historical:
            if self.filename != 'IMDB':
                if not mb_304:
                    for i in first_page_mb.entries:
                        concat_mb = i.title + i.published + \
                                    str(self.settings) + str(self.allInfos)
                        sha_mb = hashlib.sha256(concat_mb.encode(
                            'ascii', 'ignore')).hexdigest()
                        break
                if not hw_304:
                    for i in first_page_mb.entries:
                        concat_hw = i.title + i.published + \
                                    str(self.settings) + str(self.allInfos)
                        sha_hw = hashlib.sha256(concat_hw.encode(
                            'ascii', 'ignore')).hexdigest()
                        break
            else:
                if not mb_304:
                    for i in first_page_mb.entries:
                        concat_mb = i.title + i.published + \
                                    str(self.settings) + str(self.imdb)
                        sha_mb = hashlib.sha256(concat_mb.encode(
                            'ascii', 'ignore')).hexdigest()
                        break
                if not hw_304:
                    for i in first_page_mb.entries:
                        concat_hw = i.title + i.published + \
                                    str(self.settings) + str(self.imdb)
                        sha_hw = hashlib.sha256(concat_hw.encode(
                            'ascii', 'ignore')).hexdigest()
                        break

                if not hw_304:
                    try:
                        first_post_hw = first_page_hw.entries[0]
                        concat_hw = first_post_hw.title + first_post_hw.published + \
                                    str(self.settings) + str(self.imdb)
                        sha_hw = hashlib.sha256(concat_hw.encode(
                            'ascii', 'ignore')).hexdigest()
                    except:
                        sha_hw = None

        if self.filename == "IMDB":
            if imdb > 0:
                i = 0
                for url in mb_urls:
                    if not self.i_mb_done:
                        if i == 0:
                            mb_parsed_url = first_page_mb
                        else:
                            mb_parsed_url = feedparser.parse(get_url(url, configfile, dbfile))
                        self.imdb_search(imdb, mb_parsed_url, "MB")
                        i += 1
                i = 0
                for url in hw_urls:
                    if not self.i_hw_done:
                        if i == 0:
                            hw_parsed_url = first_page_hw
                        else:
                            hw_parsed_url = feedparser.parse(get_url(url, configfile, dbfile))
                        self.imdb_search(imdb, hw_parsed_url, "HW")
                        i += 1
        else:
            i = 0
            for url in mb_urls:
                if not self.mb_done:
                    if i == 0:
                        mb_parsed_url = first_page_mb
                    else:
                        mb_parsed_url = feedparser.parse(get_url(url, configfile, dbfile))
                    for (key, value, pattern) in self.search_links(mb_parsed_url, "MB"):
                        self.feed_download(key, value)
                    i += 1
            i = 0
            for url in hw_urls:
                if not self.hw_done:
                    if i == 0:
                        hw_parsed_url = first_page_hw
                    else:
                        hw_parsed_url = feedparser.parse(get_url(url, configfile, dbfile))
                    for (key, value, pattern) in self.search_links(hw_parsed_url, "HW"):
                        self.feed_download(key, value)
                        i += 1

        self.cdc.delete("MBHWSet-" + self.filename)
        self.cdc.store("MBHWSet-" + self.filename, set_mbhw)
        if sha_mb and sha_hw:
            if not self.dl_unsatisfied:
                self.cdc.delete("MB-" + self.filename)
                self.cdc.delete("HW-" + self.filename)
                self.cdc.store("MB-" + self.filename, sha_mb)
                self.cdc.store("HW-" + self.filename, sha_hw)
            else:
                self.log_debug(
                    "Für ein oder mehrere Release(s) wurde kein zweisprachiges gefunden. Setze kein neues CDC!")
        if not mb_304:
            self.cdc.delete("MBHeaders-" + self.filename)
            self.cdc.store("MBHeaders-" + self.filename, first_mb.headers['Last-Modified'])
        if not hw_304:
            self.cdc.delete("HWHeaders-" + self.filename)
            self.cdc.store("HWHeaders-" + self.filename, first_hw.headers['Last-Modified'])


def main():
    arguments = docopt(__doc__, version='RSScrawler')

    print("┌──────────────────────────────────────────────┐")
    print("  RSScrawler " + version + " von RiX")
    print("  https://github.com/rix1337/RSScrawler")
    print("└──────────────────────────────────────────────┘")

    if arguments['--docker']:
        configpath = "/config"
    else:
        configpath = files.config(arguments['--config'])
    configfile = os.path.join(configpath, "RSScrawler.ini")
    dbfile = os.path.join(configpath, "RSScrawler.db")

    print("Nutze das Verzeichnis " + configpath + " für Einstellungen/Logs")

    log_level = logging.__dict__[
        arguments['--log-level']] if arguments['--log-level'] in logging.__dict__ else logging.INFO
    log_file = os.path.join(configpath, 'RSScrawler.log')
    log_format = '%(asctime)s - %(message)s'

    if not os.path.exists(configfile):
        device = files.myjd_input(configfile, arguments['--port'])
    else:
        rsscrawler = RssConfig('RSScrawler', configfile)
        jdownloaderpath = ""
        user = rsscrawler.get('myjd_user')
        password = rsscrawler.get('myjd_pass')
        if user and password:
            device = get_device(configfile)
            if not device:
                device = get_if_one_device(user, password)
                if device:
                    print(u"Gerätename " + device + " automatisch ermittelt.")
                    rsscrawler.save('myjd_device', device)
                    device = get_device(configfile)
                else:
                    print(u'My JDownloader Zugangsdaten fehlerhaft! Beende RSScrawler!')
                    sys.exit(0)

    if not device:
        if not os.path.exists(configfile):
            if not arguments['--jd-pfad']:
                if files.jd_input(configfile, arguments['--port']):
                    print("Der Pfad wurde in der RSScrawler.ini gespeichert.")
                elif arguments['--port']:
                    files.startup(configfile,
                                  "Muss unbedingt vergeben werden!", arguments['--port'])
                else:
                    files.startup(configfile, "Muss unbedingt vergeben werden!", "9090")
                    print(
                        'Der Pfad des JDownloaders muss jetzt unbedingt in der RSScrawler.ini hinterlegt werden.')
                    print('Diese liegt unter ' + configfile)
                    print(u'Viel Spaß! Beende RSScrawler!')
                    sys.exit(0)
            else:
                if arguments['--port']:
                    files.startup(configfile, arguments['--jd-pfad'], arguments['--port'])
                else:
                    files.startup(configfile, arguments['--jd-pfad'], "9090")
                    print(
                        'Die Einstellungen und Listen sind jetzt im Webinterface anpassbar.')
        elif arguments['--jd-pfad'] and arguments['--port']:
            files.startup(configfile, arguments['--jd-pfad'], arguments['--port'])
        elif arguments['--jd-pfad']:
            files.startup(configfile, arguments['--jd-pfad'], None)
        elif arguments['--port']:
            files.startup(configfile, None, arguments['--port'])

        rsscrawler = RssConfig('RSScrawler', configfile)

        if arguments['--jd-pfad']:
            jdownloaderpath = arguments['--jd-pfad']
        else:
            jdownloaderpath = rsscrawler.get("jdownloader")
        if arguments['--docker']:
            jdownloaderpath = '/jd2'
            print(u'Docker-Modus: JDownloader-Pfad und Port können nur per Docker-Run angepasst werden!')
        elif jdownloaderpath == 'Muss unbedingt vergeben werden!':
            jdownloaderpath = files.jd_input(configfile, arguments['--port'])
            if jdownloaderpath:
                print("Der Pfad wurde in der RSScrawler.ini gespeichert.")
            else:
                print('Der Pfad des JDownloaders muss unbedingt in der RSScrawler.ini hinterlegt werden.')
                print('Diese liegt unter ' + configfile)
                print('Beende RSScrawler...')
                sys.exit(0)

        jdownloaderpath = jdownloaderpath.replace("\\", "/")
        jdownloaderpath = jdownloaderpath[:-
        1] if jdownloaderpath.endswith('/') else jdownloaderpath

        print('Nutze das "folderwatch" Unterverzeichnis von "' +
              jdownloaderpath + u'" für Crawljobs')

        if not os.path.exists(jdownloaderpath):
            print('Der Pfad des JDownloaders existiert nicht.')
            rsscrawler.save("jdownloader", "Muss unbedingt vergeben werden!")
            print('Beende RSScrawler...')
            sys.exit(0)

        if not os.path.exists(jdownloaderpath + "/folderwatch"):
            print(
                u'Der Pfad des JDownloaders enthält nicht das "folderwatch" Unterverzeichnis. Sicher, dass der Pfad stimmt?')
            rsscrawler.save("jdownloader", "Muss unbedingt vergeben werden!")
            print('Beende RSScrawler...')
            sys.exit(0)
    else:
        print("Erfolgreich mit My JDownloader verbunden. Gerätename: " + device.name)

    port = int(rsscrawler.get("port"))
    docker = False
    if arguments['--docker']:
        port = int('9090')
        docker = True
    elif arguments['--port']:
        port = int(arguments['--port'])

    if rsscrawler.get("prefix"):
        prefix = '/' + rsscrawler.get("prefix")
    else:
        prefix = ''
    if not arguments['--docker']:
        print('Der Webserver ist erreichbar unter http://' +
              common.check_ip() + ':' + str(port) + prefix)

    if arguments['--cdc-reset']:
        print("CDC-Tabelle geleert!")
        RssDb(dbfile, 'cdc').reset()

    p = Process(target=web_server, args=(
        port, docker, jdownloaderpath, configfile, dbfile, log_level, log_file, log_format, device))
    p.start()

    if not arguments['--testlauf']:
        c = Process(target=crawler, args=(jdownloaderpath, configfile, dbfile,
                                          rsscrawler, log_level, log_file, log_format, device))
        c.start()

        print(u'Drücke [Strg] + [C] zum Beenden')

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
        crawler(jdownloaderpath, configfile, dbfile, rsscrawler, log_level, log_file, log_format, device)
        p.terminate()
        sys.exit(0)


if __name__ == "__main__":
    main()
