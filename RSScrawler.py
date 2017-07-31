# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337
# Enthält Code von:
# https://github.com/zapp-brannigan/ (offline)
# https://github.com/Gutz-Pilz/pyLoad-stuff/blob/master/SJ.py
# Beschreibung:
# RSScrawler erstellt .crawljobs für den JDownloader.

"""RSScrawler.

Usage:
  RSScrawler.py [--testlauf]
                [--docker]
                [--port=<PORT>]
                [--jd-pfad="<JDPATH>"]
                [--log-level=<LOGLEVEL>]

Options:
  --testlauf                Einmalige Ausführung von RSScrawler
  --docker                  Sperre Pfad und Port auf Docker-Standardwerte (um falsche Einstellungen zu vermeiden)
  --port=<PORT>             Legt den Port des Webservers fest
  --jd-pfad="<JDPFAD>"      Legt den Pfad von JDownloader fest um nicht die RSScrawler.ini direkt bearbeiten zu müssen
  --log-level=<LOGLEVEL>    Legt fest, wie genau geloggt wird (CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET )
"""

import version
version = version.getVersion()

from docopt import docopt
import requests
import feedparser
import re
import urllib2
import codecs
from bs4 import BeautifulSoup as bs
import time
import sys
import signal
import socket
import logging
import os
from multiprocessing import Process

from rssconfig import RssConfig
from rssdb import RssDb
import common
import cherry
import files


def cherry_server(port, prefix, docker):
    starten = cherry.Server()
    starten.start(port, prefix, docker)

def crawler():
    log_debug = logging.debug
    search_pool = [
        YT(),
        SJ(filename='SJ_Serien', internal_name='SJ'),
        SJ(filename='SJ_Serien_Regex', internal_name='SJ'),
        SJ(filename='MB_Staffeln', internal_name='MB'),
        MB(filename='MB_Regex'),
        MB(filename='MB_Filme'),
        MB(filename='MB_Staffeln'),
        MB(filename='MB_3D'),
        HW(filename='MB_Regex'),
        HW(filename='MB_Filme'),
        HW(filename='MB_Staffeln'),
        HW(filename='MB_3D'),
        HA(filename='MB_Regex'),
        HA(filename='MB_Filme'),
        HA(filename='MB_Staffeln'),
        HA(filename='MB_3D')
    ]
    if not arguments['--testlauf']:
        while True:
            for task in search_pool:
                task.periodical_task()
            log_debug("-----------Alle Suchfunktion ausgeführt!-----------")
            time.sleep(int(rsscrawler.get('interval')) * 60)
            log_debug("-------------Wartezeit verstrichen-------------")
    else:
        for task in search_pool:
            task.periodical_task()
        log_debug("-----------Testlauf ausgeführt!-----------")

def getURL(url):
    try:
        req = urllib2.Request(
            url,
            None,
            {
                'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'}
        )
        return urllib2.urlopen(req).read()
    except urllib2.HTTPError as e:
        logging.debug('Bei der HTTP-Anfrage ist ein Fehler Aufgetreten: Fehler: %s Grund: %s' % (e.code, e.reason))
        return ''
    except urllib2.URLError as e:
        logging.debug('Bei der HTTP-Anfrage ist ein Fehler Aufgetreten: Grund: %s' % e.reason)
        return ''
    except socket.error as e:
        logging.debug('Die HTTP-Anfrage wurde unterbrochen. Grund: %s' % e)
        return ''

class YT():
    _INTERNAL_NAME='YT'

    def __init__(self):
        self.config = RssConfig(self._INTERNAL_NAME)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.db = RssDb(os.path.join(os.path.dirname(sys.argv[0]), "Einstellungen/Downloads/YT_Downloads.db"))
        self.youtube = os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/YT_Channels.txt')
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
        text = []
        videos = []
        key = ""
        download_link = ""
        self.allInfos = self.readInput(self.youtube)

        for xline in self.allInfos:
            if len(xline) > 0 and not xline.startswith("#"):
                if xline.startswith("XXXXXXXXXX") or self.config.get("youtube") == False:
                    self.log_debug("Liste enthält Platzhalter. Stoppe Suche für YouTube!")
                    return
                channels.append(xline)

        for channel in channels:
            url = 'https://www.youtube.com/user/' + channel + '/videos'
            urlc = 'https://www.youtube.com/channel/' + channel + '/videos'
            cnotfound = False
            try:
                html = urllib2.urlopen(url)
            except urllib2.HTTPError:
                try:
                    html = urllib2.urlopen(urlc)
                except urllib2.HTTPError:
                    cnotfound = True
                if cnotfound:
                    self.log_debug("YouTube-Kanal: " + channel + " nicht gefunden!")
                    return
                    
            response = html.read()
            links = re.findall('href="(\/watch.*?)">(.*?)<\/a>', response)

            maxvideos = int(self.config.get("maxvideos"))
            if maxvideos < 1:
                self.log_debug("Anzahl zu suchender YouTube-Videos (" + str(maxvideos) +") zu gering. Suche stattdessen 1 Video!")
                maxvideos = 1
            elif maxvideos > 50:
                self.log_debug("Anzahl zu suchender YouTube-Videos (" + str(maxvideos) +") zu hoch. Suche stattdessen maximal 50 Videos!")
                maxvideos = 50

            for link in links[:maxvideos]:
                if len(link[0]) > 10:
                    videos.append([link[0], link[1], channel])

        for video in videos:
            channel = video[2]
            video_title = video[1].replace("&amp;", "&").replace("&gt;", ">").replace("&lt;", "<").replace('&quot;', '"').replace("&#39;", "'")
            video = video[0]
            key = video.replace("/watch?v=", "")
            download_link = 'https://www.youtube.com' + video
            if not download_link == None:
                if self.db.retrieve(key) == 'added':
                    self.log_debug("[%s] - YouTube-Video ignoriert (bereits gefunden)" % key)
                else:
                    ignore = "|".join(["%s" % p for p in self.config.get("ignore").lower().split(',')]) if not self.config.get("ignore") == "" else "^unmatchable$"
                    ignorevideo = re.search(ignore,video_title.lower())
                    if ignorevideo:
                        self.log_debug(video_title + " (" + channel + ") " + "[" + key + "] - YouTube-Video ignoriert (basierend auf ignore-Einstellung)")
                        continue
                    
                    self.log_info('[YouTube] - ' + video_title + ' (' + channel + ') - [<a href="' + download_link + '" target="_blank">Link</a>]')
                    common.write_crawljob_file(
                        key,
                        "YouTube/" + channel,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler"
                    ) and text.append(video_title + "[" + key + "]")
                    self.db.store(
                        key,
                        'added',
                        channel
                )
                    
        if len(text) > 0 and len(rsscrawler.get("pushbulletapi")) > 0:
            common.Pushbullet(rsscrawler.get("pushbulletapi"),text)

class SJ():
    def __init__(self, filename, internal_name):
        self._INTERNAL_NAME = internal_name
        self.config = RssConfig(self._INTERNAL_NAME)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.filename = filename
        self.db = RssDb(os.path.join(os.path.dirname(sys.argv[0]), "Einstellungen/Downloads/SJ_Downloads.db"))
        self.search_list = os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/{}.txt'.format(self.filename))
        self.empty_list = False
        if self.filename == 'MB_Staffeln':
            self.seasonssource = self.config.get('seasonssource').lower()
            self.level = 2
        elif self.filename == 'SJ_Serien_Regex':
            self.level = 1
        else:
            self.level = 0

    def periodical_task(self):
        if self.filename == "MB_Staffeln":
            feed = feedparser.parse('aHR0cDovL3Nlcmllbmp1bmtpZXMub3JnL3htbC9mZWVkcy9zdGFmZmVsbi54bWw='.decode('base64'))
        else:
            feed = feedparser.parse('aHR0cDovL3Nlcmllbmp1bmtpZXMub3JnL3htbC9mZWVkcy9lcGlzb2Rlbi54bWw='.decode('base64'))
            
        self.pattern = "|".join(self.getSeriesList(self.search_list, self.level)).lower()

        if self.filename == 'SJ_Serien_Regex':
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
                self.config.get("rejectlist")) > 0 else "^unmatchable$"
        except TypeError:
            reject = "^unmatchable$"
        self.quality = self.config.get("quality")
        self.hoster = rsscrawler.get("hoster")

        self.added_items = []

        for post in feed.entries:
            if post.link == None:
                continue

            link = post.link
            title = post.title

            if self.filename == 'SJ_Serien_Regex':
                if self.config.get("regex"):
                    m = re.search(self.pattern, title.lower())
                    if not m and not "720p" in title and not "1080p" in title and not "2160p" in title:
                        m = re.search(self.pattern.replace("480p", "."), title.lower())
                        self.quality = "480p"
                    if m:
                        if "720p" in title.lower(): self.quality = "720p"
                        if "1080p" in title.lower(): self.quality = "1080p"
                        if "2160p" in title.lower(): self.quality = "2160p"
                        m = re.search(reject, title.lower())
                        if m:
                            self.log_debug(title + " - Release durch Regex gefunden (trotz rejectlist-Einstellung)")
                        title = re.sub('\[.*\] ', '', post.title)
                        self.range_checkr(link, title)

                else:
                    continue
            else:
                if self.config.get("quality") != '480p':
                    m = re.search(self.pattern, title.lower())
                    if m:
                        if '[DEUTSCH]' in title:
                            mm = re.search(self.quality, title.lower())
                            if mm:
                                mmm = re.search(reject, title.lower())
                                if mmm:
                                    self.log_debug(
                                        title + " - Release ignoriert (basierend auf rejectlist-Einstellung)")
                                    continue
                                title = re.sub('\[.*\] ', '', post.title)
                                self.range_checkr(link, title)

                    else:
                        m = re.search(self.pattern, title.lower())
                        if m:
                            if '[DEUTSCH]' in title:
                                if "720p" in title.lower() or "1080p" in title.lower() or "2160p" in title.lower():
                                    continue
                                mm = re.search(reject, title.lower())
                                if mm:
                                    self.log_debug(title + " Release ignoriert (basierend auf rejectlist-Einstellung)")
                                    continue
                                title = re.sub('\[.*\] ', '', post.title)
                                self.range_checkr(link, title)

        if len(rsscrawler.get('pushbulletapi')) > 2:
            common.Pushbullet(rsscrawler.get("pushbulletapi"), self.added_items) if len(self.added_items) > 0 else True

    def range_checkr(self, link, title):
        if self.filename == 'MB_Staffeln':
            season = re.search("\.s\d", title.lower())
            if not season:
                self.log_debug(title + " - Release ist keine Staffel")
                return
            if self.config.get("seasonpacks") == "False":
                staffelpack = re.search("s\d.*(-|\.).*s\d", title.lower())
                if staffelpack:
                    self.log_debug("%s - Release ignoriert (Staffelpaket)" % title)
                    return
        pattern = re.match(".*S\d{2}E\d{2}-\w?\d{2}.*", title)
        if pattern is not None:
            range0 = re.sub(r".*S\d{2}E(\d{2}-\w?\d{2}).*", r"\1", title).replace("E", "")
            number1 = re.sub(r"(\d{2})-\d{2}", r"\1", range0)
            number2 = re.sub(r"\d{2}-(\d{2})", r"\1", range0)
            title_cut = re.findall(r"(.*S\d{2}E)(\d{2}-\w?\d{2})(.*)", title)
            try:
                for count in range(int(number1), (int(number2) + 1)):
                    NR = re.match("\d{2}", str(count))
                    if NR is not None:
                        title1 = title_cut[0][0] + str(count) + ".*" + title_cut[0][-1]
                        self.range_parse(link, title1)
                    else:
                        title1 = title_cut[0][0] + "0" + str(count) + ".*" + title_cut[0][-1]
                        self.range_parse(link, title1)
            except ValueError as e:
                logging.error("Fehler in Variablenwert: %s" % e.message)
        else:
            self.parse_download(link, title)

    def range_parse(self, series_url, search_title):
        req_page = getURL(series_url)
        soup = bs(req_page, 'lxml')
        try:
            titles = soup.findAll(text=re.compile(search_title))
            for title in titles:
                if self.quality != '480p' and self.quality in title:
                    self.parse_download(series_url, title)
                if self.quality == '480p' and not (('.720p.' in title) or ('.1080p.' in title) or ('.2160p.' in title)):
                    self.parse_download(series_url, title)
        except re.error as e:
            self.log_error('Konstantenfehler: %s' % e)

    def parse_download(self, series_url, search_title):
        req_page = getURL(series_url)
        soup = bs(req_page, 'lxml')
        escape_brackets = search_title.replace("(", ".*").replace(")", ".*").replace("+", ".*")
        title = soup.find(text=re.compile(escape_brackets))
        if title:
            valid = False
            if self.filename == 'MB_Staffeln':
                valid = re.search(self.seasonssource, title.lower())
            else:
                valid = True
            if valid:
                url_hosters = re.findall('<a href="([^"\'>]*)".+?\| (.+?)<', str(title.parent.parent))
                for url_hoster in url_hosters:
                    if self.hoster.lower() in url_hoster[1]:
                        self.send_package(title, url_hoster[0])
            else:
                self.log_debug(title + " - Release hat falsche Quelle")

    def send_package(self, title, link):
        if self.filename == 'SJ_Serien_Regex':
            link_place_holder = '[Episode/RegEx] - '
        elif self.filename == 'SJ_Serien':
            link_place_holder = '[Episode] - '
        else:
            link_place_holder = '[Staffel] - '
        try:
            storage = self.db.retrieve(title)
        except Exception as e:
            self.log_debug("Fehler bei Datenbankzugriff: %s, Grund: %s" % (e, title))
        if storage == 'downloaded':
            self.log_debug(title + " - Release ignoriert (bereits gefunden)")
        else:
            self.log_info(link_place_holder + title + ' - [<a href="' + link + '" target="_blank">Link</a>]')
            self.db.store(title, 'downloaded')
            common.write_crawljob_file(title, title, link,
                                       jdownloaderpath + "/folderwatch", "RSScrawler") and self.added_items.append(
                title.encode("utf-8"))

    def getSeriesList(self, file, type):
        loginfo = ""
        if type == 1:
            loginfo = " (RegEx)"
        elif type == 2:
            loginfo = " (Staffeln)"

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
                self.log_debug("Liste enthält Platzhalter. Stoppe Suche für Serien!" + loginfo)
                if type == 1:
                    self.empty_list = True
                elif type == 2:
                    self.empty_list = True
                else:
                    self.empty_list = True
            return titles
        except UnicodeError:
            self.log_error("ANGEHALTEN, ungültiges Zeichen in Serien" + loginfo + "Liste!")
        except IOError:
            self.log_error("ANGEHALTEN, Serien" + loginfo + "-Liste nicht gefunden!")
        except Exception, e:
            self.log_error("Unbekannter Fehler: %s" % e)

class MB():
    _INTERNAL_NAME = 'MB'
    FEED_URL = "aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZy9mZWVkLw==".decode('base64')
    SUBSTITUTE = "[&#\s/]"

    def __init__(self, filename):
        self.config = RssConfig(self._INTERNAL_NAME)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.filename = filename
        self.db = RssDb(os.path.join(os.path.dirname(sys.argv[0]), "Einstellungen/Downloads/MB_Downloads.db"))
        self.search_list = os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/{}.txt'.format(self.filename))
        if filename == 'MB_Staffeln':
            self.db_sj = RssDb(os.path.join(os.path.dirname(sys.argv[0]), "Einstellungen/Downloads/SJ_Downloads.db"))
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

    def getPatterns(self,patterns, **kwargs):
        if patterns == ["XXXXXXXXXX"]:
            self.log_debug("Liste enthält Platzhalter. Stoppe Suche für Filme!")
            self.empty_list = True
        if kwargs:
            return {line: (kwargs['quality'], kwargs['rg'], kwargs['sf']) for line in patterns}
        return {x: (x) for x in patterns}

    def searchLinks(self, feed):
        if self.empty_list:
            return
        ignore = "|".join(
            ["\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if not self.config.get(
            "ignore") == "" else "^unmatchable$"

        for key in self.allInfos:
            s = re.sub(self.SUBSTITUTE, ".", "^" + key).lower()
            for post in feed.entries:
                found = re.search(s, post.title.lower())
                if found:
                    found = re.search(ignore, post.title.lower())
                    if found:
                        self.log_debug("%s - Release ignoriert (basierend auf ignore-Einstellung)" % post.title)
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
                            sss = "[\.-]+" + self.allInfos[key][1].lower()
                            found = re.search(sss, post.title.lower())
                            if self.allInfos[key][2]:
                                found = all([word in post.title.lower() for word in self.allInfos[key][2]])
                            if found:
                                episode = re.search(r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', post.title.lower())
                                if episode:
                                    self.log_debug("%s - Release ignoriert (Serienepisode)" % post.title)
                                    continue
                                yield (post.title, [post.link], key)
                    elif self.filename == 'MB_3D':
                        if '.3d.' in post.title.lower():
                            if self.config.get('crawl3d') and (
                                    "1080p" in post.title.lower() or "1080i" in post.title.lower()):
                                found = True
                            else:
                                continue
                        if found:
                            sss = "[\.-]+" + self.allInfos[key][1].lower()
                            found = re.search(sss, post.title.lower())
                            if self.allInfos[key][2]:
                                found = all([word in post.title.lower() for word in self.allInfos[key][2]])
                            if found:
                                episode = re.search(r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', post.title.lower())
                                if episode:
                                    self.log_debug("%s - Release ignoriert (Serienepisode)" % post.title)
                                    continue
                                yield (post.title, [post.link], key)

                    elif self.filename == 'MB_Staffeln':
                        validsource = re.search(self.config.get("seasonssource"), post.title.lower())
                        if not validsource:
                            self.log_debug(post.title + " - Release hat falsche Quelle")
                            continue
                        season = re.search("\.s\d", post.title.lower())
                        if not season:
                            self.log_debug(post.title + " - Release ist keine Staffel")
                            continue
                        if self.config.get("seasonpacks") == "False":
                            staffelpack = re.search("s\d.*(-|\.).*s\d", post.title.lower())
                            if staffelpack:
                                self.log_debug("%s - Release ignoriert (Staffelpaket)" % post.title)
                                continue
                        ss = self.allInfos[key][0].lower()

                        if ss == "480p":
                            if "720p" in post.title.lower() or "1080p" in post.title.lower() or "1080i" in post.title.lower() or "2160p" in post.title.lower():
                                continue
                            found = True
                        else:
                            found = re.search(ss, post.title.lower())
                        if found:
                            sss = "[\.-]+" + self.allInfos[key][1].lower()
                            found = re.search(sss, post.title.lower())

                            if self.allInfos[key][2]:
                                found = all([word in post.title.lower() for word in self.allInfos[key][2]])
                            if found:
                                episode = re.search(r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', post.title.lower())
                                if episode:
                                    self.log_debug("%s - Release ignoriert (Serienepisode)" % post.title)
                                    continue
                                yield (post.title, [post.link], key)
                    else:
                        yield (post.title, [post.link], key)

    def download_dl(self, title):
        text = []
        search_title = title.replace(".German.720p.", ".German.DL.1080p.").replace(".German.DTS.720p.", ".German.DTS.DL.1080p.").replace(".German.AC3.720p.", ".German.AC3.DL.1080p.").replace(".German.AC3LD.720p.", ".German.AC3LD.DL.1080p.").replace(".German.AC3.Dubbed.720p.", ".German.AC3.Dubbed.DL.1080p.").split('.x264-', 1)[0].split('.h264-', 1)[0].replace(".", " ").replace(" ", "+")
        search_url = "aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZy9zZWFyY2gv".decode('base64') + search_title + "/feed/rss2/"
        feedsearch_title = title.replace(".German.720p.", ".German.DL.1080p.").replace(".German.DTS.720p.", ".German.DTS.DL.1080p.").replace(".German.AC3.720p.", ".German.AC3.DL.1080p.").replace(".German.AC3LD.720p.", ".German.AC3LD.DL.1080p.").replace(".German.AC3.Dubbed.720p.", ".German.AC3.Dubbed.DL.1080p.").split('.x264-', 1)[0].split('.h264-', 1)[0]
        if not '.dl.' in feedsearch_title.lower():
            self.log_debug("%s - Release ignoriert (nicht zweisprachig, da wahrscheinlich nicht Retail)" %feedsearch_title)
            return
        for (key, value, pattern) in self.dl_search(feedparser.parse(search_url), feedsearch_title):
            download_link = self._get_download_links(value[0])
            if not download_link == None:
                if self.db.retrieve(key) == 'added' or self.db.retrieve(key) == 'dl':
                    self.log_debug("%s - zweisprachiges Release ignoriert (bereits gefunden)" % key)
                elif  self.filename == 'MB_Filme':
                    retail = False
                    if self.config.get('cutoff'):
                        if self.config.get('enforcedl'):
                            if common.cutoff(key, '1'):
                                retail = True
                        else:
                            if common.cutoff(key, '0'):
                                retail = True
                    self.log_info('[Film] - <b>' + (
                    'Retail/' if retail else "") + 'Zweisprachig</b> - ' + key + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')
                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler/Remux"
                    ) and text.append(key)
                    self.db.store(
                        key,
                        'dl' if self.config.get('enforcedl') and '.dl.' in key.lower() else 'added',
                        pattern
                    )
                elif self.filename == 'MB_3D':
                    retail = False
                    if self.config.get('cutoff'):
                        if common.cutoff(key, '2'):
                            retail = True

                    self.log_info('[Film] - <b>' + (
                    'Retail/' if retail else "") + '3D/Zweisprachig</b> - ' + key + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')

                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler/3Dcrawler"
                    ) and text.append(key)
                    self.db.store(
                        key,
                        'dl' if self.config.get('enforcedl') and '.dl.' in key.lower() else 'added',
                        pattern
                    )
                elif self.filename == 'MB_Regex':
                    self.log_info('[Film/Serie/RegEx] - <b>Zweisprachig</b> - ' + key + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')

                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler"
                    ) and text.append(key)
                    self.db.store(
                        key,
                        'dl' if self.config.get('enforcedl') and '.dl.' in key.lower() else 'added',
                        pattern
                        )
                else:
                    self.log_info(
                        '[Staffel] - <b>Zweisprachig</b> - ' + key + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')

                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler/Remux"
                    ) and text.append(key)
                    self.db.store(
                        key,
                        'dl' if self.config.get('enforcedl') and '.dl.' in key.lower() else 'added',
                        pattern
                    )
        if len(text) > 0 and len(rsscrawler.get("pushbulletapi")) > 0:
            common.Pushbullet(rsscrawler.get("pushbulletapi"),text)
            return True

    def dl_search(self, feed, title):
        ignore = "|".join(
            ["\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if not self.config.get(
            "ignore") == "" else "^unmatchable$"

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

    def _get_download_links(self, url):
        req_page = getURL(url)
        soup = bs(req_page, 'lxml')
        download = soup.find("div", {"id": "content"})
        url_hosters = re.findall('href="([^"\'>]*)".+?(.+?)<', str(download))
        for url_hoster in url_hosters:
            if self.hoster.lower() in url_hoster[1].lower():
                return url_hoster[0]

    def periodical_task(self):
        if self.empty_list:
            return
        urls = []
        text = []
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
                        xn = xline.split(",")[0].replace(".", " ").replace(" ", "+")
                        urls.append('aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZw=='.decode('base64') + '/search/%s/feed/rss2/' % xn)
            else:
                urls.append(self.FEED_URL)
        else:
            urls.append(self.FEED_URL)
        for url in urls:
            for (key, value, pattern) in self.searchLinks(feedparser.parse(url)):
                download_link = self._get_download_links(value[0])
                if not download_link == None:
                    englisch = False
                    if "*englisch*" in key.lower():
                        key = key.replace('*ENGLISCH*', '').replace("*Englisch*", "")
                        englisch = True
                    if self.config.get('enforcedl') and '.dl.' not in key.lower():
                        if not self.download_dl(key):
                            self.log_debug("%s - Kein zweisprachiges Release gefunden" % key)
                    if self.db.retrieve(key) == 'added' or self.db.retrieve(key) == 'notdl':
                        self.log_debug("%s - Release ignoriert (bereits gefunden)" % key)
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
                        self.log_info('[Film] - ' + ('<b>Englisch</b> - ' if englisch and not retail else "") + (
                        '<b>Englisch/Retail</b> - ' if englisch and retail else "") + (
                                      '<b>Retail</b> - ' if not englisch and retail else "") + key + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')
                        common.write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler"
                        ) and text.append(key)
                        self.db.store(
                            key,
                            'notdl' if self.config.get('enforcedl') and '.dl.' not in key.lower() else 'added',
                            pattern
                        )
                    elif self.filename == 'MB_3D':
                        retail = False
                        if (self.config.get('enforcedl') and '.dl.' in key.lower()) or not self.config.get(
                                'enforcedl'):
                            if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                                if self.config.get('enforcedl'):
                                    if common.cutoff(key, '2'):
                                        retail = True
                        self.log_info('[Film] - <b>' + ('Retail/' if retail else "") + '3D</b> - ' + key + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')
                        common.write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler"
                        ) and text.append(key)
                        self.db.store(
                            key,
                            'notdl' if self.config.get('enforcedl') and '.dl.' not in key.lower() else 'added',
                            pattern
                        )
                    elif self.filename == 'MB_Staffeln':
                        self.log_info('[Staffel] - ' + key.replace(".COMPLETE.",
                                                                   ".") + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')
                        common.write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler"
                        ) and text.append(key)
                        self.db.store(
                            key,
                            'notdl' if self.config.get('enforcedl') and '.dl.' not in key.lower() else 'added',
                            pattern
                        )
                        self.db_sj.store(
                            key.replace(".COMPLETE", "").replace(".Complete", ""),
                            'downloaded',
                            pattern
                        )
                    else:
                        self.log_info(
                            '[Film/Serie/RegEx] - ' + key + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')
                        common.write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler"
                        ) and text.append(key)
                        self.db.store(
                            key,
                            'notdl' if self.config.get('enforcedl') and '.dl.' not in key.lower() else 'added',
                            pattern
                        )
            if len(text) > 0 and len(rsscrawler.get("pushbulletapi")) > 0:
                common.Pushbullet(rsscrawler.get("pushbulletapi"), text)

class HW():
    _INTERNAL_NAME = 'MB'
    FEED_URL = "aHR0cDovL3d3dy5oZC13b3JsZC5vcmcvZmVlZC8=".decode('base64')
    SUBSTITUTE = "[&#\s/]"

    def __init__(self, filename):
        self.config = RssConfig(self._INTERNAL_NAME)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.filename = filename
        self.db = RssDb(os.path.join(os.path.dirname(sys.argv[0]), "Einstellungen/Downloads/MB_Downloads.db"))
        self.search_list = os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/{}.txt'.format(self.filename))
        if filename == 'MB_Staffeln':
            self.db_sj = RssDb(os.path.join(os.path.dirname(sys.argv[0]), "Einstellungen/Downloads/SJ_Downloads.db"))
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

    def getPatterns(self,patterns, **kwargs):
        if patterns == ["XXXXXXXXXX"]:
            self.log_debug("Liste enthält Platzhalter. Stoppe Suche für Filme!")
            self.empty_list = True
        if kwargs:
            return {line: (kwargs['quality'], kwargs['rg'], kwargs['sf']) for line in patterns}
        return {x: (x) for x in patterns}

    def searchLinks(self, feed):
        if self.empty_list:
            return
        ignore = "|".join(
            ["\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if not self.config.get(
            "ignore") == "" else "^unmatchable$"

        for key in self.allInfos:
            s = re.sub(self.SUBSTITUTE, ".", "^" + key).lower()
            for post in feed.entries:
                found = re.search(s, post.title.lower())
                if found:
                    found = re.search(ignore, post.title.lower())
                    if found:
                        self.log_debug("%s - Release ignoriert (basierend auf ignore-Einstellung)" % post.title)
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
                            sss = "[\.-]+" + self.allInfos[key][1].lower()
                            found = re.search(sss, post.title.lower())
                            if self.allInfos[key][2]:
                                found = all([word in post.title.lower() for word in self.allInfos[key][2]])
                            if found:
                                episode = re.search(r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', post.title.lower())
                                if episode:
                                    self.log_debug("%s - Release ignoriert (Serienepisode)" % post.title)
                                    continue
                                yield (post.title, [post.link], key)
                    elif self.filename == 'MB_3D':
                        if '.3d.' in post.title.lower():
                            if self.config.get('crawl3d') and (
                                    "1080p" in post.title.lower() or "1080i" in post.title.lower()):
                                found = True
                            else:
                                continue
                        if found:
                            sss = "[\.-]+" + self.allInfos[key][1].lower()
                            found = re.search(sss, post.title.lower())
                            if self.allInfos[key][2]:
                                found = all([word in post.title.lower() for word in self.allInfos[key][2]])
                            if found:
                                episode = re.search(r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', post.title.lower())
                                if episode:
                                    self.log_debug("%s - Release ignoriert (Serienepisode)" % post.title)
                                    continue
                                yield (post.title, [post.link], key)

                    elif self.filename == 'MB_Staffeln':
                        validsource = re.search(self.config.get("seasonssource"), post.title.lower())
                        if not validsource:
                            self.log_debug(post.title + " - Release hat falsche Quelle")
                            continue
                        season = re.search("\.s\d", post.title.lower())
                        if not season:
                            self.log_debug(post.title + " - Release ist keine Staffel")
                            continue
                        if self.config.get("seasonpacks") == "False":
                            staffelpack = re.search("s\d.*(-|\.).*s\d", post.title.lower())
                            if staffelpack:
                                self.log_debug("%s - Release ignoriert (Staffelpaket)" % post.title)
                                continue
                        ss = self.allInfos[key][0].lower()

                        if ss == "480p":
                            if "720p" in post.title.lower() or "1080p" in post.title.lower() or "1080i" in post.title.lower() or "2160p" in post.title.lower():
                                continue
                            found = True
                        else:
                            found = re.search(ss, post.title.lower())
                        if found:
                            sss = "[\.-]+" + self.allInfos[key][1].lower()
                            found = re.search(sss, post.title.lower())

                            if self.allInfos[key][2]:
                                found = all([word in post.title.lower() for word in self.allInfos[key][2]])
                            if found:
                                episode = re.search(r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', post.title.lower())
                                if episode:
                                    self.log_debug("%s - Release ignoriert (Serienepisode)" % post.title)
                                    continue
                                yield (post.title, [post.link], key)
                    else:
                        yield (post.title, [post.link], key)

    def download_dl(self, title):
        text = []
        search_title = title.replace(".German.720p.", ".German.DL.1080p.").replace(".German.DTS.720p.", ".German.DTS.DL.1080p.").replace(".German.AC3.720p.", ".German.AC3.DL.1080p.").replace(".German.AC3LD.720p.", ".German.AC3LD.DL.1080p.").replace(".German.AC3.Dubbed.720p.", ".German.AC3.Dubbed.DL.1080p.").split('.x264-', 1)[0].split('.h264-', 1)[0].replace(".", " ").replace(" ", "+")
        search_url = "aHR0cDovL2hkLXdvcmxkLm9yZy9zZWFyY2gv".decode('base64') + search_title + "/feed/rss2/"
        feedsearch_title = title.replace(".German.720p.", ".German.DL.1080p.").replace(".German.DTS.720p.", ".German.DTS.DL.1080p.").replace(".German.AC3.720p.", ".German.AC3.DL.1080p.").replace(".German.AC3LD.720p.", ".German.AC3LD.DL.1080p.").replace(".German.AC3.Dubbed.720p.", ".German.AC3.Dubbed.DL.1080p.").split('.x264-', 1)[0].split('.h264-', 1)[0]
        if not '.dl.' in feedsearch_title.lower():
            self.log_debug("%s - Release ignoriert (nicht zweisprachig, da wahrscheinlich nicht Retail)" %feedsearch_title)
            return
        for (key, value, pattern) in self.dl_search(feedparser.parse(search_url), feedsearch_title):
            download_link = self._get_download_links(value[0])
            if not download_link == None:
                if self.db.retrieve(key) == 'added' or self.db.retrieve(key) == 'dl':
                    self.log_debug("%s - zweisprachiges Release ignoriert (bereits gefunden)" % key)
                elif  self.filename == 'MB_Filme':
                    retail = False
                    if self.config.get('cutoff'):
                        if self.config.get('enforcedl'):
                            if common.cutoff(key, '1'):
                                retail = True
                        else:
                            if common.cutoff(key, '0'):
                                retail = True
                    self.log_info('[Film] - <b>' + (
                    'Retail/' if retail else "") + 'Zweisprachig</b> - ' + key + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')
                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler/Remux"
                    ) and text.append(key)
                    self.db.store(
                        key,
                        'dl' if self.config.get('enforcedl') and '.dl.' in key.lower() else 'added',
                        pattern
                    )
                elif self.filename == 'MB_3D':
                    retail = False
                    if self.config.get('cutoff'):
                        if common.cutoff(key, '2'):
                            retail = True

                    self.log_info('[Film] - <b>' + (
                    'Retail/' if retail else "") + '3D/Zweisprachig</b> - ' + key + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')

                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler/3Dcrawler"
                    ) and text.append(key)
                    self.db.store(
                        key,
                        'dl' if self.config.get('enforcedl') and '.dl.' in key.lower() else 'added',
                        pattern
                    )
                elif self.filename == 'MB_Regex':
                    self.log_info('[Film/Serie/RegEx] - <b>Zweisprachig</b> - ' + key + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')

                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler"
                    ) and text.append(key)
                    self.db.store(
                        key,
                        'dl' if self.config.get('enforcedl') and '.dl.' in key.lower() else 'added',
                        pattern
                        )
                else:
                    self.log_info(
                        '[Staffel] - <b>Zweisprachig</b> - ' + key + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')

                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler/Remux"
                    ) and text.append(key)
                    self.db.store(
                        key,
                        'dl' if self.config.get('enforcedl') and '.dl.' in key.lower() else 'added',
                        pattern
                    )
        if len(text) > 0 and len(rsscrawler.get("pushbulletapi")) > 0:
            common.Pushbullet(rsscrawler.get("pushbulletapi"),text)
            return True

    def dl_search(self, feed, title):
        ignore = "|".join(
            ["\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if not self.config.get(
            "ignore") == "" else "^unmatchable$"

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

    def _get_download_links(self, url):
        req_page = getURL(url)
        soup = bs(req_page, 'lxml')
        download = soup.find("div", {"id": "content"})
        url_hosters = re.findall('href="([^"\'>]*)".+?(.+?)<', str(download))
        for url_hoster in url_hosters:
            if self.hoster.lower() in url_hoster[1].lower():
                return url_hoster[0]

    def periodical_task(self):
        if self.empty_list:
            return
        urls = []
        text = []
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
                        xn = xline.split(",")[0].replace(".", " ").replace(" ", "+")
                        urls.append('aHR0cDovL2hkLXdvcmxkLm9yZw=='.decode('base64') + '/search/%s/feed/rss2/' % xn)
            else:
                urls.append(self.FEED_URL)
        else:
            urls.append(self.FEED_URL)
        for url in urls:
            for (key, value, pattern) in self.searchLinks(feedparser.parse(url)):
                download_link = self._get_download_links(value[0])
                if not download_link == None:
                    englisch = False
                    if "*englisch*" in key.lower():
                        key = key.replace('*ENGLISCH*', '').replace("*Englisch*", "")
                        englisch = True
                    if self.config.get('enforcedl') and '.dl.' not in key.lower():
                        if not self.download_dl(key):
                            self.log_debug("%s - Kein zweisprachiges Release gefunden" % key)
                    if self.db.retrieve(key) == 'added' or self.db.retrieve(key) == 'notdl':
                        self.log_debug("%s - Release ignoriert (bereits gefunden)" % key)
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
                        self.log_info('[Film] - ' + ('<b>Englisch</b> - ' if englisch and not retail else "") + (
                        '<b>Englisch/Retail</b> - ' if englisch and retail else "") + (
                                      '<b>Retail</b> - ' if not englisch and retail else "") + key + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')
                        common.write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler"
                        ) and text.append(key)
                        self.db.store(
                            key,
                            'notdl' if self.config.get('enforcedl') and '.dl.' not in key.lower() else 'added',
                            pattern
                        )
                    elif self.filename == 'MB_3D':
                        retail = False
                        if (self.config.get('enforcedl') and '.dl.' in key.lower()) or not self.config.get(
                                'enforcedl'):
                            if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                                if self.config.get('enforcedl'):
                                    if common.cutoff(key, '2'):
                                        retail = True
                        self.log_info('[Film] - <b>' + ('Retail/' if retail else "") + '3D</b> - ' + key + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')
                        common.write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler"
                        ) and text.append(key)
                        self.db.store(
                            key,
                            'notdl' if self.config.get('enforcedl') and '.dl.' not in key.lower() else 'added',
                            pattern
                        )
                    elif self.filename == 'MB_Staffeln':
                        self.log_info('[Staffel] - ' + key.replace(".COMPLETE.",
                                                                   ".") + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')
                        common.write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler"
                        ) and text.append(key)
                        self.db.store(
                            key,
                            'notdl' if self.config.get('enforcedl') and '.dl.' not in key.lower() else 'added',
                            pattern
                        )
                        self.db_sj.store(
                            key.replace(".COMPLETE", "").replace(".Complete", ""),
                            'downloaded',
                            pattern
                        )
                    else:
                        self.log_info(
                            '[Film/Serie/RegEx] - ' + key + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')
                        common.write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler"
                        ) and text.append(key)
                        self.db.store(
                            key,
                            'notdl' if self.config.get('enforcedl') and '.dl.' not in key.lower() else 'added',
                            pattern
                        )
            if len(text) > 0 and len(rsscrawler.get("pushbulletapi")) > 0:
                common.Pushbullet(rsscrawler.get("pushbulletapi"), text)
 
class HA():
    _INTERNAL_NAME = 'MB'
    FEED_URL = "aHR0cDovL3d3dy5oZC1hcmVhLm9yZy9pbmRleC5waHA=".decode('base64')
    SUBSTITUTE = "[&#\s/]"

    def __init__(self, filename):
        self.config = RssConfig(self._INTERNAL_NAME)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.filename = filename
        self.db = RssDb(os.path.join(os.path.dirname(sys.argv[0]), "Einstellungen/Downloads/MB_Downloads.db"))
        self.search_list = os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/{}.txt'.format(self.filename))
        if filename == 'MB_Staffeln':
            self.db_sj = RssDb(os.path.join(os.path.dirname(sys.argv[0]), "Einstellungen/Downloads/SJ_Downloads.db"))
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

    def getPatterns(self,patterns, **kwargs):
        if patterns == ["XXXXXXXXXX"]:
            self.log_debug("Liste enthält Platzhalter. Stoppe Suche für Filme!")
            self.empty_list = True
        if kwargs:
            return {line: (kwargs['quality'], kwargs['rg'], kwargs['sf']) for line in patterns}
        return {x: (x) for x in patterns}

    def searchLinks(self, feed):
        if self.empty_list:
            return
        ignore = "|".join(
            ["\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if not self.config.get(
            "ignore") == "" else "^unmatchable$"

        for key in self.allInfos:
            if not key.replace(" ", "+") in feed:
                continue
            req_page = getURL(feed)
            soup = bs(req_page, 'lxml')
            content = soup.find("div", {"id" : "content"})
            if "index.php" in feed.lower():
                titles = content.findAll("div", {"id" : "title"})
            else:
                titles = content.findAll("a")
            for title in titles:
                try:
                    hda = re.findall('href="(.*?)" title="(.*?)">', str(title))[0]
                except:
                    self.log_debug("Ungültiger Link bei Suche nach Titel")
                url = hda[0]
                title = hda[1]
                s = re.sub(self.SUBSTITUTE, ".", "^" + key).lower()
                found = re.search(s, title.lower())
                if found:
                    found = re.search(ignore, title.lower())
                    if found:
                        self.log_debug("%s - Release ignoriert (basierend auf ignore-Einstellung)" % title)
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
                            sss = "[\.-]+" + self.allInfos[key][1].lower()
                            found = re.search(sss, title.lower())
                            if self.allInfos[key][2]:
                                found = all([word in title.lower() for word in self.allInfos[key][2]])
                            if found:
                                episode = re.search(r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', title.lower())
                                if episode:
                                    self.log_debug("%s - Release ignoriert (Serienepisode)" % title)
                                    continue
                                link = self._get_download_links(url)
                                yield (title, link, key)
                    elif self.filename == 'MB_3D':
                        if '.3d.' in title.lower():
                            if self.config.get('crawl3d') and (
                                    "1080p" in title.lower() or "1080i" in title.lower()):
                                found = True
                            else:
                                continue
                        if found:
                            sss = "[\.-]+" + self.allInfos[key][1].lower()
                            found = re.search(sss, title.lower())
                            if self.allInfos[key][2]:
                                found = all([word in title.lower() for word in self.allInfos[key][2]])
                            if found:
                                episode = re.search(r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', title.lower())
                                if episode:
                                    self.log_debug("%s - Release ignoriert (Serienepisode)" % title)
                                    continue
                                link = self._get_download_links(url)
                                yield (title, link, key)

                    elif self.filename == 'MB_Staffeln':
                        validsource = re.search(self.config.get("seasonssource"), title.lower())
                        if not validsource:
                            self.log_debug(title + " - Release hat falsche Quelle")
                            continue
                        season = re.search("\.s\d", title.lower())
                        if not season:
                            self.log_debug(title + " - Release ist keine Staffel")
                            continue
                        if self.config.get("seasonpacks") == "False":
                            staffelpack = re.search("s\d.*(-|\.).*s\d", title.lower())
                            if staffelpack:
                                self.log_debug("%s - Release ignoriert (Staffelpaket)" % title)
                                continue
                        ss = self.allInfos[key][0].lower()

                        if ss == "480p":
                            if "720p" in title.lower() or "1080p" in title.lower() or "1080i" in title.lower():
                                continue
                            found = True
                        else:
                            found = re.search(ss, title.lower())
                        if found:
                            sss = "[\.-]+" + self.allInfos[key][1].lower()
                            found = re.search(sss, title.lower())

                            if self.allInfos[key][2]:
                                found = all([word in title.lower() for word in self.allInfos[key][2]])
                            if found:
                                episode = re.search(r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', title.lower())
                                if episode:
                                    self.log_debug("%s - Release ignoriert (Serienepisode)" % title)
                                    continue
                                link = self._get_download_links(url)
                                yield (title, link, key)
                    else:
                        link = self._get_download_links(url)
                        yield (title, link, key)

    def download_dl(self, title):
        text = []
        search_title = title.replace(".German.720p.", ".German.DL.1080p.").replace(".German.DTS.720p.", ".German.DTS.DL.1080p.").replace(".German.AC3.720p.", ".German.AC3.DL.1080p.").replace(".German.AC3LD.720p.", ".German.AC3LD.DL.1080p.").replace(".German.AC3.Dubbed.720p.", ".German.AC3.Dubbed.DL.1080p.").split('.x264-', 1)[0].split('.h264-', 1)[0].replace(".", " ").replace(" ", "+")
        search_url = "aHR0cDovL3d3dy5oZC1hcmVhLm9yZy8/cz1zZWFyY2gmcT0=".decode('base64') + search_title
        feedsearch_title = title.replace(".German.720p.", ".German.DL.1080p.").replace(".German.DTS.720p.", ".German.DTS.DL.1080p.").replace(".German.AC3.720p.", ".German.AC3.DL.1080p.").replace(".German.AC3LD.720p.", ".German.AC3LD.DL.1080p.").replace(".German.AC3.Dubbed.720p.", ".German.AC3.Dubbed.DL.1080p.").split('.x264-', 1)[0].split('.h264-', 1)[0]
        if not '.dl.' in feedsearch_title.lower():
            self.log_debug("%s - Release ignoriert (nicht zweisprachig, da wahrscheinlich nicht Retail)" %feedsearch_title)
            return
        for (key, download_link, pattern) in self.dl_search(search_url, feedsearch_title):
            if not download_link == None:
                if self.db.retrieve(key) == 'added' or self.db.retrieve(key) == 'dl':
                    self.log_debug("%s - zweisprachiges Release ignoriert (bereits gefunden)" % key)
                elif  self.filename == 'MB_Filme':
                    retail = False
                    if self.config.get('cutoff'):
                        if self.config.get('enforcedl'):
                            if common.cutoff(key, '1'):
                                retail = True
                        else:
                            if common.cutoff(key, '0'):
                                retail = True
                    self.log_info('[Film] - <b>' + (
                    'Retail/' if retail else "") + 'Zweisprachig</b> - ' + key + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')
                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler/Remux"
                    ) and text.append(key)
                    self.db.store(
                        key,
                        'dl' if self.config.get('enforcedl') and '.dl.' in key.lower() else 'added',
                        pattern
                    )
                elif self.filename == 'MB_3D':
                    retail = False
                    if self.config.get('cutoff'):
                        if common.cutoff(key, '2'):
                            retail = True

                    self.log_info('[Film] - <b>' + (
                    'Retail/' if retail else "") + '3D/Zweisprachig</b> - ' + key + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')

                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler/3Dcrawler"
                    ) and text.append(key)
                    self.db.store(
                        key,
                        'dl' if self.config.get('enforcedl') and '.dl.' in key.lower() else 'added',
                        pattern
                    )
                elif self.filename == 'MB_Regex':
                    self.log_info('[Film/Serie/RegEx] - <b>Zweisprachig</b> - ' + key + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')

                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler"
                    ) and text.append(key)
                    self.db.store(
                        key,
                        'dl' if self.config.get('enforcedl') and '.dl.' in key.lower() else 'added',
                        pattern
                        )
                else:
                    self.log_info(
                        '[Staffel] - <b>Zweisprachig</b> - ' + key + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')

                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler/Remux"
                    ) and text.append(key)
                    self.db.store(
                        key,
                        'dl' if self.config.get('enforcedl') and '.dl.' in key.lower() else 'added',
                        pattern
                    )
        if len(text) > 0 and len(rsscrawler.get("pushbulletapi")) > 0:
            common.Pushbullet(rsscrawler.get("pushbulletapi"),text)
            return True

    def dl_search(self, feed, title):
        ignore = "|".join(
            ["\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if not self.config.get(
            "ignore") == "" else "^unmatchable$"
        req_page = getURL(feed)
        soup = bs(req_page, 'lxml')
        content = soup.find("div", {"id" : "content"})
        try:
            found = content.findAll("a")[0]
        except:
            return
        hda = re.findall('href="(.*?)" title="(.*?)">', str(found))[0]
        url = hda[0]
        title = hda[1]
        link = getURL(url)
        dl_soup = bs(link, 'lxml')
        dl_links = re.findall('href="(http:\/\/filecrypt.cc.*?|https:\/\/www.filecrypt.cc.*?)" target="_blank">(.*?)<\/a>', str(dl_soup))
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
        dl_links = re.findall('href="(http:\/\/filecrypt.cc.*?|https:\/\/www.filecrypt.cc.*?)" target="_blank">(.*?)<\/a>', str(dl_soup))
        for link in dl_links:
            url = link[0]
            if self._hosters_pattern.lower().replace(" ", "-") in link[1].lower().replace(" ", "-"):
                return url

    def periodical_task(self):
        urls = []
        text = []
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
                        search_title = title.replace(".", " ").replace(" ", "+")
                        urls.append("aHR0cDovL3d3dy5oZC1hcmVhLm9yZy8/cz1zZWFyY2gmcT0=".decode('base64') + search_title)
            else:
                urls.append(self.FEED_URL)
        else:
            urls.append(self.FEED_URL)

        for url in urls:
            for (key, download_link, pattern) in self.searchLinks(url):
                if not download_link == None:
                    englisch = False
                    if "*englisch*" in key.lower():
                        key = key.replace('*ENGLISCH*', '').replace("*Englisch*", "")
                        englisch = True
                    if self.config.get('enforcedl') and '.dl.' not in key.lower():
                        if not self.download_dl(key):
                            self.log_debug("%s - Kein zweisprachiges Release gefunden" % key)
                    if self.db.retrieve(key) == 'added' or self.db.retrieve(key) == 'notdl':
                        self.log_debug("%s - Release ignoriert (bereits gefunden)" % key)
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
                        self.log_info('[Film] - ' + ('<b>Englisch</b> - ' if englisch and not retail else "") + (
                        '<b>Englisch/Retail</b> - ' if englisch and retail else "") + (
                                      '<b>Retail</b> - ' if not englisch and retail else "") + key + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')
                        common.write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler"
                        ) and text.append(key)
                        self.db.store(
                            key,
                            'notdl' if self.config.get('enforcedl') and '.dl.' not in key.lower() else 'added',
                            pattern
                        )
                    elif self.filename == 'MB_3D':
                        retail = False
                        if (self.config.get('enforcedl') and '.dl.' in key.lower()) or not self.config.get(
                                'enforcedl'):
                            if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                                if self.config.get('enforcedl'):
                                    if common.cutoff(key, '2'):
                                        retail = True
                        self.log_info('[Film] - <b>' + ('Retail/' if retail else "") + '3D</b> - ' + key + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')
                        common.write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler"
                        ) and text.append(key)
                        self.db.store(
                            key,
                            'notdl' if self.config.get('enforcedl') and '.dl.' not in key.lower() else 'added',
                            pattern
                        )
                    elif self.filename == 'MB_Staffeln':
                        self.log_info('[Staffel] - ' + key.replace(".COMPLETE.",
                                                                   ".") + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')
                        common.write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler"
                        ) and text.append(key)
                        self.db.store(
                            key,
                            'notdl' if self.config.get('enforcedl') and '.dl.' not in key.lower() else 'added',
                            pattern
                        )
                        self.db_sj.store(
                            key.replace(".COMPLETE", "").replace(".Complete", ""),
                            'downloaded',
                            pattern
                        )
                    else:
                        self.log_info(
                            '[Film/Serie/RegEx] - ' + key + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')
                        common.write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler"
                        ) and text.append(key)
                        self.db.store(
                            key,
                            'notdl' if self.config.get('enforcedl') and '.dl.' not in key.lower() else 'added',
                            pattern
                        )
            if len(text) > 0 and len(rsscrawler.get("pushbulletapi")) > 0:
                common.Pushbullet(rsscrawler.get("pushbulletapi"), text)

if __name__ == "__main__":
    arguments = docopt(__doc__, version='RSScrawler')

    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logging.basicConfig(
        filename=os.path.join(os.path.dirname(sys.argv[0]), 'RSScrawler.log'), format='%(asctime)s - %(message)s', level=logging.__dict__[arguments['--log-level']] if arguments['--log-level'] in logging.__dict__ else logging.INFO
    )
    console = logging.StreamHandler()
    console.setLevel(logging.__dict__[arguments['--log-level']] if arguments['--log-level'] in logging.__dict__ else logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    print("┌────────────────────────────────────────────────────────┐")
    print("  Programminfo:    RSScrawler " + version + " von RiX")
    print("  Projektseite:    https://github.com/rix1337/RSScrawler")
    print("└────────────────────────────────────────────────────────┘")
    
    files.startup()

    einstellungen = os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/RSScrawler.ini')
    if not arguments['--jd-pfad']:
        if not os.path.exists(einstellungen):
            if arguments['--port']:
                files.einsteller(einstellungen, version, "Muss unbedingt vergeben werden!", arguments['--port'])
            else:
                files.einsteller(einstellungen, version, "Muss unbedingt vergeben werden!", "9090")
            print('Der Ordner "Einstellungen" wurde erstellt.')
            print('Der Pfad des JDownloaders muss jetzt unbedingt in der RSScrawler.ini hinterlegt werden.')
            print('Die Einstellungen und Listen sind beim nächsten Start im Webinterface anpassbar.')
            print('Viel Spass! Beende RSScrawler!')
            sys.exit(0)
    else:
        if not os.path.exists(einstellungen):
            if arguments['--port']:
                files.einsteller(einstellungen, version, arguments['--jd-pfad'], arguments['--port'])
            else:
                files.einsteller(einstellungen, version, arguments['--jd-pfad'], "9090")
            print('Der Ordner "Einstellungen" wurde erstellt.')
            print('Die Einstellungen und Listen sind jetzt im Webinterface anpassbar.')
    
    configfile = os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/RSScrawler.ini')
    if not 'port' in open(configfile).read() and not 'prefix' in open(configfile).read() :
        print "Veraltete Konfigurationsdatei erkannt. Ergänze neue Einstellungen!"
        with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/RSScrawler.ini'), 'r+') as f:
            content = f.read()
            f.seek(0)
            f.truncate()
            f.write(content.replace('[RSScrawler]\n', '[RSScrawler]\nport = 9090\nprefix =\n'))
            
    rsscrawler = RssConfig('RSScrawler')

    if arguments['--jd-pfad']:
        jdownloaderpath = arguments['--jd-pfad']
    else:
        jdownloaderpath = rsscrawler.get("jdownloader")
    if arguments['--docker']:
       jdownloaderpath = '/jd2'
    jdownloaderpath = jdownloaderpath.replace("\\", "/")
    jdownloaderpath = jdownloaderpath[:-1] if jdownloaderpath.endswith('/') else jdownloaderpath

    if arguments['--docker']:
       print('Docker-Modus: JDownloader-Pfad und Port können nur per Docker-Run angepasst werden!')
       
    if jdownloaderpath == 'Muss unbedingt vergeben werden!':
        print('Der Pfad des JDownloaders muss unbedingt in der RSScrawler.ini hinterlegt werden.')
        print('Weiterhin sollten die Listen entsprechend der README.md gefüllt werden!')
        print('Beende RSScrawler...')
        sys.exit(0)
    
    print('Nutze das "folderwatch" Unterverzeichnis von "' + jdownloaderpath + '" für Crawljobs')
        
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
    docker = '0'
    if arguments['--docker']:
       port = int('9090')
       docker = '1'
       
    prefix = rsscrawler.get("prefix")
    print('Der Webserver ist erreichbar unter ' + common.checkIp() +':' + str(port) + '/' + prefix)

    p = Process(target=cherry_server, args=(port, prefix, docker))
    p.start()
    
    files.check()
    
    c = Process(target=crawler, args=())
    c.start()

    print('Drücke [Strg] + [C] zum Beenden')
    
    def signal_handler(signal, frame):
        print('Beende RSScrawler...')
        p.terminate()
        c.terminate()
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    if not arguments['--testlauf']:
        try:
            while True:
                signal.pause()
        except AttributeError:
            while True:
              time.sleep(1)
