# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337
# Enthält Code von:
# https://github.com/dmitryint (im Auftrag von https://github.com/rix1337)
# https://github.com/zapp-brannigan/own-pyload-plugins/blob/master/hooks/MovieblogFeed.py
# https://github.com/Gutz-Pilz/pyLoad-stuff/blob/master/SJ.py
# Beschreibung:
# RSScrawler erstellt .crawljobs für den JDownloader.

# Startparameter/Hilfetext für docopt (nicht verändern!)
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

# Globale Variablen
import version
version = version.getVersion()
no_mb_filme = False
no_mb_3d = False
no_mb_regex = False
no_mb_staffeln = False
no_sj_serien = False
no_sj_regex = False
no_sj_staffeln = False

from docopt import docopt
from lxml import html
import requests
import feedparser
import re
import urllib
import urllib2
import codecs
import base64
from BeautifulSoup import BeautifulSoup
import time
import sys
import signal
import socket
import logging
import os
import multiprocessing
from multiprocessing import Process

# Lokales
from rssconfig import RssConfig
from rssdb import RssDb
from timer import RepeatableTimer
import common
import cherry
import files

# Definiere cherrypy Serverinstanz
def cherry_server(port, prefix, docker):
    starten = cherry.Server()
    starten.start(port, prefix, docker)

# Funktion für das wiederholte Ausführen des Scriptes
def _restart_timer(func):
    def wrapper(self):
        func(self)
        # Wenn testlauf inaktiv ist wurde dies aktiviert. Der folgende Code führt das Script in Intervallen aus
        if self._periodical_active:
            self.periodical.cancel()
            self.periodical.start()
    return wrapper

class MB():
    FEED_URL = "aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZy9mZWVkLw==".decode('base64')
    SUBSTITUTE = "[&#\s/]"
    _INTERNAL_NAME='MB'

    def __init__(self):
        self.config = RssConfig(self._INTERNAL_NAME)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.db = RssDb(os.path.join(os.path.dirname(sys.argv[0]), "Einstellungen/Downloads/MB_Downloads.db"))
        self.filme = os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/MB_Filme.txt')
        self._hosters_pattern = rsscrawler.get('hoster').replace(',','|')
        self._periodical_active = False
        self.periodical = RepeatableTimer(
            int(rsscrawler.get('interval')) * 60,
            self.periodical_task
        )
        self.dictWithNamesAndLinks = {}

    def activate(self):
        self._periodical_active = True
        self.periodical.start()
        return self

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

    def getPatterns(self, patterns, quality, rg, sf):
        # Importiere globale Parameter (sollten beide Falsch sein)
        global no_mb_filme
        # Wenn Liste exakt die Platzhalterzeile enthält:
        if patterns == ["XXXXXXXXXX"]:
            # Wenn keine Information zur Quellart weitergegeben wurde (gilt nur bei Staffeln, Standard ist: BluRay):
            # Logge vorhandenen Platzhalter, der in der Filme-Liste stehen muss (da keine Quellart angegeben)
            self.log_debug("Liste enthält Platzhalter. Stoppe Suche für Filme!")
            # Setze globale Variable auf wahr, um in der MB-Klasse die Suche abbrechen zu können
            no_mb_filme = True
        # Ansonsten gib die Zeilen einzeln als Zeilen in patters zurück
        return {line: (quality, rg, sf) for line in patterns}

    def searchLinks(self, feed):
        ignore = "|".join(["\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if not self.config.get("ignore") == "" else "^unmatchable$"
        
        for key in self.allInfos:
            s = re.sub(self.SUBSTITUTE,".","^" + key).lower()
            for post in feed.entries:
                found = re.search(s,post.title.lower())
                if found:
                    found = re.search(ignore,post.title.lower())
                    if found:
                        # Wenn zu ignorierender Eintrag, logge diesen
                        self.log_debug("%s - Release ignoriert (basierend auf ignore-Einstellung)" %post.title)
                        continue
                    ss = self.allInfos[key][0].lower()


                    if ss == "480p":
                        if "720p" in post.title.lower() or "1080p" in post.title.lower() or "1080i" in post.title.lower():
                            continue
                        found = True
                    else:
                        found = re.search(ss,post.title.lower())
                    if found:
                        # Funktion, die Listeneinträge wie folgt erwartet: Titel,Auflösung,Gruppe
                        sss = "[\.-]+"+self.allInfos[key][1].lower()
                        found = re.search(sss,post.title.lower())

                        if self.allInfos[key][2]:
                            # Wenn alles True, dann found = True (also gilt Release nur als gefunden, wenn alle Parameter wahr sind)
                            found = all([word in post.title.lower() for word in self.allInfos[key][2]])

                        if found:
                            # Check, ob das Release zu einer Serie gehört
                            try:
                                episode = re.search(r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*',post.title.lower()).group(1)
                                if "repack" in post.title.lower():
                                    episode = episode + "-repack"
                                self.log_debug("Serie entdeckt. Kürze Titel: [%s]" %episode)
                                yield (episode, [post.link], key)
                            except:
                                # Gebe den Link (der alle obigen Checks bestandend hat) weiter
                                yield (post.title, [post.link], key)


    def download_dl(self, title):
        # Schreibe den nicht-zweisprachigen Titel für die folgende Suche um
        text = []
        # Dies generiert den in die Suche einfügbaren String (+ statt Leerzeichen)
        search_title = title.replace(".German.720p.", ".German.DL.1080p.").replace(".German.DTS.720p.", ".German.DTS.DL.1080p.").replace(".German.AC3.720p.", ".German.AC3.DL.1080p.").replace(".German.AC3LD.720p.", ".German.AC3LD.DL.1080p.").replace(".German.AC3.Dubbed.720p.", ".German.AC3.Dubbed.DL.1080p.").split('.x264-', 1)[0].split('.h264-', 1)[0].replace(".", " ").replace(" ", "+")
        search_url = "aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZy9zZWFyY2gv".decode('base64') + search_title + "/feed/rss2/"
        # Nach diesem String (also Releasetitel) wird schlussendlich in den Suchergebnissen gesucht (. statt Leerzeichen)
        feedsearch_title = title.replace(".German.720p.", ".German.DL.1080p.").replace(".German.DTS.720p.", ".German.DTS.DL.1080p.").replace(".German.AC3.720p.", ".German.AC3.DL.1080p.").replace(".German.AC3LD.720p.", ".German.AC3LD.DL.1080p.").replace(".German.AC3.Dubbed.720p.", ".German.AC3.Dubbed.DL.1080p.").split('.x264-', 1)[0].split('.h264-', 1)[0]
        if not '.dl.' in feedsearch_title.lower():
            self.log_debug("%s - Release ignoriert (nicht zweisprachig, da wahrscheinlich nicht Retail)" %feedsearch_title)
            return
        
        # Suche nach title im Ergebnisfeed der obigen Suche (nicht nach dem für die suche genutzten search_title)
        for (key, value, pattern) in self.dl_search(feedparser.parse(search_url), feedsearch_title, title):
            # Nimm nur den ersten validen Downloadlink der auf der Unterseite eines jeden Releases gefunden wurde
            download_link = common.get_first(self._get_download_links(value[0], self._hosters_pattern))
            # Füge Release nur hinzu, wenn überhaupt ein Link gefunden wurde (erzeuge hierfür einen crawljob)
            if not download_link == None:
                # Wenn das Release als bereits hinzugefügt in der Datenbank vermerkt wurde, logge dies und breche ab
                if self.db.retrieve(key) == 'added' or self.db.retrieve(key) == 'dl':
                    self.log_debug("%s - zweisprachiges Release ignoriert (bereits gefunden)" % key)
                # Ansonsten speichere das Release als hinzugefügt in der Datenbank
                else:
                    # Cutofffunktion um bei Retail Release den Listeneintrag zu entfernen
                    retail = False
                    if self.config.get('cutoff'):
                        if self.config.get('enforcedl'):
                            if common.cutoff(key, '1'):
                                retail = True
                        else:
                            if common.cutoff(key, '0'):
                                retail = True

                    # Logge gefundenes Release auch im RSScrawler (Konsole/Logdatei)
                    self.log_info('[Film] - <b>' + ('Retail/' if retail else "") + 'Zweisprachig</b> - ' + key + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')
                
                    # Schreibe Crawljob            
                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler/Remux"
                    ) and text.append(key)
                    self.db.store(
                        key,
                        # Vermerke zweisprachiges Release entsprechend in der Datenbank
                        'dl' if self.config.get('enforcedl') and '.dl.' in key.lower() else 'added',
                        pattern
                        )
        # Wenn zuvor ein key dem Text hinzugefügt wurde (also ein Release gefunden wurde):
        if len(text) > 0 and len(rsscrawler.get("pushbulletapi")) > 0:
            # Löse Pushbullet-Benachrichtigung aus
            common.Pushbullet(rsscrawler.get("pushbulletapi"),text)
            return True
                
    def dl_search(self, feed, title, notdl_title):
        ignore = "|".join(["\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if not self.config.get("ignore") == "" else "^unmatchable$"
            
        s = re.sub(self.SUBSTITUTE,".",title).lower()
        for post in feed.entries:
            found = re.search(s,post.title.lower())
            if found:
                found = re.search(ignore,post.title.lower())
                if found:
                    # Wenn zu ignorierender Eintrag, logge diesen
                    self.log_debug("%s - zweisprachiges Release ignoriert (basierend auf ignore-Einstellung)" %post.title)
                    continue
                yield (post.title, [post.link], title)

    # Suchfunktion für Downloadlinks (auf der zuvor gefundenen Unterseite):
    def _get_download_links(self, url, hosters_pattern=None):
        # Definiere die zu durchsuchende Baumstruktur (auf Basis der Unterseite)
        tree = html.fromstring(requests.get(url).content)
        # Genaue Anweisung, wo die Links zu finden sind (Unterhalb des Download:/Mirror # Textes)
        xpath = '//*[@id="content"]/span/div/div[2]//strong[contains(text(),"Download:") or contains(text(),"Mirror #")]/following-sibling::a[1]'
        # Jeder link wird zurück gegeben, wenn kein Wunschhoster festgelegt wurde. Ansonsten werden nur Links zum Wunschhoster weitergegeben.
        return [common.get_first(link.xpath('./@href')) for link in tree.xpath(xpath) if hosters_pattern is None or re.search(hosters_pattern, link.text, flags=re.IGNORECASE)]

    # Periodische Aufgabe
    @_restart_timer
    def periodical_task(self):
        # Leere/Definiere interne URL/Text-Arrays
        urls = []
        text = []
            
        # Definiere interne Suchliste auf Basis der MB_Filme Liste
        self.allInfos = dict(
            # Füge der Suche sämtliche Titel aus der MB_Filme Liste hinzu
            set({key: value for (key, value) in self.getPatterns(
                    self.readInput(self.filme),
                    self.config.get('quality'),
                    '.*',
                    None
                ).items()}.items()
            )
        )
        
        # Stoppe Suche, wenn Platzhalter aktiv ist.
        if no_mb_filme:
            return

        # Wenn historical aktiv ist nutzt RSScrawler die Suchfunktion von MB, statt nur den (zeitlich begrenzten) Feed zu nutzen. Dies dauert etwas länger, durchsucht aber den kompletten MB!
        if self.config.get("historical"):
            # Suche nach jeder Zeile in der internen Suchliste
            for xline in self.allInfos.keys():
                # Wenn die Zeile nicht leer ist bzw. keine Raute (für Kommentare) enthält:
                if len(xline) > 0 and not xline.startswith("#"):
                    # Entferne Zusatzinfos der obsoleten Funktion, die Listeneinträge wie folgt erwartet: Titel,Auflösung,Gruppe
                    # Die Suche Benötigt nur den Titel vor dem ersten Komma. Ersetze Weiterhin Punkte durch Leerzeichen und diese für die Suche durch ein +
                    xn = xline.split(",")[0].replace(".", " ").replace(" ", "+")
                    # Generiere aus diesen Suchurl-kompatiblen String als Seitenaufruf (entspricht einer Suche auf MB nach dem entsprechenden Titel) eine Liste an Suchanfragen-URLs (Anzahl entspricht Einträgen der internen Suchliste)
                    urls.append('aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZw=='.decode('base64') + '/search/%s/feed/rss2/' %xn)
        # Nutze ansonsten den Feed (und dessen Inhalt) als Grundlage zur Suche
        else:
            # Hierfür wird nur eine einzelne URL (die oben vergebene) benötigt
            urls.append(self.FEED_URL)

        # Suchfunktion für valide Releases (und deren Downloadlinks) wird für jede URL durchgeführt:
        for url in urls:
            # Führe für jeden Eintrag auf der URL eine Suche nach Releases durch:
            for (key, value, pattern) in self.searchLinks(feedparser.parse(url)):
                # Nimm nur den ersten validen Downloadlink der auf der Unterseite eines jeden Releases gefunden wurde
                download_link = common.get_first(self._get_download_links(value[0], self._hosters_pattern))
                # Füge Release nur hinzu, wenn überhaupt ein Link gefunden wurde (erzeuge hierfür einen crawljob)
                if not download_link == None:
                    # Suche nach zweisprachigem Release, sollte das aktuelle nicht zweisprachig sein:
                    if self.config.get('enforcedl') and '.dl.' not in key.lower():
                        # Wenn die Suche für zweisprachige Releases nichts findet (wird zugleich ausgeführt)
                        if not self.download_dl(key):
                            # Logge nicht gefundenes zweisprachiges Release
                            self.log_debug("%s - Kein zweisprachiges Release gefunden" %key)
                                
                    # Wenn das Release als bereits hinzugefügt in der Datenbank vermerkt wurde, logge dies und breche ab
                    if self.db.retrieve(key) == 'added' or self.db.retrieve(key) == 'notdl':
                        self.log_debug("%s - Release ignoriert (bereits gefunden)" % key)
                    # Ansonsten speichere das Release als hinzugefügt in der Datenbank
                    else:
                        # Entferne normale Filme nur, wenn diese die DL-Kriterien erfüllen bzw. enforcedl inaktiv ist.
                        retail = False
                        if (self.config.get('enforcedl') and '.dl.' in key.lower()) or not self.config.get('enforcedl'):
                            # Cutofffunktion um bei Retail Release den Listeneintrag zu entfernen
                            if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                                if self.config.get('enforcedl'):
                                    if common.cutoff(key, '1'):
                                        retail = True
                                else:
                                    if common.cutoff(key, '0'):
                                        retail = True

                        englisch = False
                        if "*englisch*" in key.lower():
                            key = key.replace('*ENGLISCH*', '').replace("*Englisch*","")
                            englisch = True

                        # Logge gefundenes Release auch im RSScrawler (Konsole/Logdatei)
                        self.log_info('[Film] - ' + ('<b>Englisch</b> - ' if englisch and not retail else "") + ('<b>Englisch/Retail</b> - ' if englisch and retail else "") + ('<b>Retail</b> - ' if not englisch and retail else "") + key + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')

                        # Schreibe Crawljob  
                        common.write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler"
                        ) and text.append(key)
                        self.db.store(
                            key,
                            # Vermerke Releases, die nicht zweisprachig sind in der Datenbank (falls enforcedl aktiv ist). Speichere jedes gefundene Release
                            'notdl' if self.config.get('enforcedl') and '.dl.' not in key.lower() else 'added',
                            pattern
                        )
        # Wenn zuvor ein key dem Text hinzugefügt wurde (also ein Release gefunden wurde):
        if len(text) > 0 and len(rsscrawler.get("pushbulletapi")) > 0:
            # Löse Pushbullet-Benachrichtigung aus
            common.Pushbullet(rsscrawler.get("pushbulletapi"),text)

class MB3d():
    FEED_URL = "aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZy9mZWVkLw==".decode('base64')
    SUBSTITUTE = "[&#\s/]"
    _INTERNAL_NAME='MB'

    def __init__(self):
        self.config = RssConfig(self._INTERNAL_NAME)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.db = RssDb(os.path.join(os.path.dirname(sys.argv[0]), "Einstellungen/Downloads/MB_Downloads.db"))
        self.filme = os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/MB_3D.txt')
        self._hosters_pattern = rsscrawler.get('hoster').replace(',','|')
        self._periodical_active = False
        self.periodical = RepeatableTimer(
            int(rsscrawler.get('interval')) * 60,
            self.periodical_task
        )
        self.dictWithNamesAndLinks = {}

    def activate(self):
        self._periodical_active = True
        self.periodical.start()
        return self

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

    def getPatterns(self, patterns, quality, rg, sf):
        # Importiere globale Parameter (sollten beide Falsch sein)
        global no_mb_3d
        # Wenn Liste exakt die Platzhalterzeile enthält:
        if patterns == ["XXXXXXXXXX"]:
            # Wenn keine Information zur Quellart weitergegeben wurde (gilt nur bei Staffeln, Standard ist: BluRay):
            # Logge vorhandenen Platzhalter, der in der Filme-Liste stehen muss (da keine Quellart angegeben)
            self.log_debug("Liste enthält Platzhalter. Stoppe Suche für 3D-Filme!")
            # Setze globale Variable auf wahr, um in der MB-Klasse die Suche abbrechen zu können
            no_mb_3d = True
        # Ansonsten gib die Zeilen einzeln als Zeilen in patters zurück
        return {line: (quality, rg, sf) for line in patterns}

    def searchLinks(self, feed):
        ignore = "|".join(["\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if not self.config.get("ignore") == "" else "^unmatchable$"
        
        for key in self.allInfos:
            s = re.sub(self.SUBSTITUTE,".","^" + key).lower()
            for post in feed.entries:
                found = re.search(s,post.title.lower())
                if found:
                    found = re.search(ignore,post.title.lower())
                    if found:
                        # Wenn zu ignorierender Eintrag, logge diesen
                        self.log_debug("%s - Release ignoriert (basierend auf ignore-Einstellung)" %post.title)
                        continue
                    ss = self.allInfos[key][0].lower()

                    # Crawl3d Funktion gilt wenn 3D im Titel enthalten ist
                    if '.3d.' in post.title.lower():
                        # Wenn crawl3d aktiv ist und 1080p/1080i zusätzlich zu 3D im Titel steht:
                        if self.config.get('crawl3d') and ("1080p" in post.title.lower() or "1080i" in post.title.lower()):
                            # Release gilt als gefunden
                            found = True
                        # Ansonsten ignoriere das Release mit 3D im Titel (weil es bspw. in 720p released wurde)
                        else:
                            continue
                    if found:
                        # Funktion, die Listeneinträge wie folgt erwartet: Titel,Auflösung,Gruppe
                        sss = "[\.-]+"+self.allInfos[key][1].lower()
                        found = re.search(sss,post.title.lower())

                        if self.allInfos[key][2]:
                            # Wenn alles True, dann found = True (also gilt Release nur als gefunden, wenn alle Parameter wahr sind)
                            found = all([word in post.title.lower() for word in self.allInfos[key][2]])

                        if found:
                            yield (post.title, [post.link], key)
                            
    def download_dl(self, title):
        # Schreibe den nicht-zweisprachigen Titel für die folgende Suche um
        text = []
        # Dies generiert den in die Suche einfügbaren String (+ statt Leerzeichen)
        search_title = title.replace(".German.720p.", ".German.DL.1080p.").replace(".German.DTS.720p.", ".German.DTS.DL.1080p.").replace(".German.AC3.720p.", ".German.AC3.DL.1080p.").replace(".German.AC3LD.720p.", ".German.AC3LD.DL.1080p.").replace(".German.AC3.Dubbed.720p.", ".German.AC3.Dubbed.DL.1080p.").split('.x264-', 1)[0].split('.h264-', 1)[0].replace(".", " ").replace(" ", "+")
        search_url = "aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZy9zZWFyY2gv".decode('base64') + search_title + "/feed/rss2/"
        # Nach diesem String (also Releasetitel) wird schlussendlich in den Suchergebnissen gesucht (. statt Leerzeichen)
        feedsearch_title = title.replace(".German.720p.", ".German.DL.1080p.").replace(".German.DTS.720p.", ".German.DTS.DL.1080p.").replace(".German.AC3.720p.", ".German.AC3.DL.1080p.").replace(".German.AC3LD.720p.", ".German.AC3LD.DL.1080p.").replace(".German.AC3.Dubbed.720p.", ".German.AC3.Dubbed.DL.1080p.").split('.x264-', 1)[0].split('.h264-', 1)[0]
        if not '.dl.' in feedsearch_title.lower():
            self.log_debug("%s - Release ignoriert (nicht zweisprachig, da wahrscheinlich nicht Retail)" %feedsearch_title)
            return
        
        # Suche nach title im Ergebnisfeed der obigen Suche (nicht nach dem für die suche genutzten search_title)
        for (key, value, pattern) in self.dl_search(feedparser.parse(search_url), feedsearch_title, title):
            # Nimm nur den ersten validen Downloadlink der auf der Unterseite eines jeden Releases gefunden wurde
            download_link = common.get_first(self._get_download_links(value[0], self._hosters_pattern))
            # Füge Release nur hinzu, wenn überhaupt ein Link gefunden wurde (erzeuge hierfür einen crawljob)
            if not download_link == None:
                # Wenn das Release als bereits hinzugefügt in der Datenbank vermerkt wurde, logge dies und breche ab
                if self.db.retrieve(key) == 'added' or self.db.retrieve(key) == 'dl':
                    self.log_debug("%s - zweisprachiges Release ignoriert (bereits gefunden)" % key)
                # Ansonsten speichere das Release als hinzugefügt in der Datenbank
                else:
                    # Cutofffunktion um bei Retail Release den Listeneintrag zu entfernen
                    retail = False
                    if self.config.get('cutoff'):
                        if common.cutoff(key, '2'):
                            retail = True

                    # Logge gefundenes Release auch im RSScrawler (Konsole/Logdatei)
                    self.log_info('[Film] - <b>' + ('Retail/' if retail else "") + '3D/Zweisprachig</b> - ' + key + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')
                
                    # Schreibe Crawljob            
                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler/3Dcrawler"
                    ) and text.append(key)
                    self.db.store(
                        key,
                        # Vermerke zweisprachiges Release entsprechend in der Datenbank
                        'dl' if self.config.get('enforcedl') and '.dl.' in key.lower() else 'added',
                        pattern
                        )
        # Wenn zuvor ein key dem Text hinzugefügt wurde (also ein Release gefunden wurde):
        if len(text) > 0 and len(rsscrawler.get("pushbulletapi")) > 0:
            # Löse Pushbullet-Benachrichtigung aus
            common.Pushbullet(rsscrawler.get("pushbulletapi"),text)
            return True
                
    def dl_search(self, feed, title, notdl_title):
        ignore = "|".join(["\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if not self.config.get("ignore") == "" else "^unmatchable$"
            
        s = re.sub(self.SUBSTITUTE,".",title).lower()
        for post in feed.entries:
            found = re.search(s,post.title.lower())
            if found:
                found = re.search(ignore,post.title.lower())
                if found:
                    # Wenn zu ignorierender Eintrag, logge diesen
                    self.log_debug("%s - zweisprachiges Release ignoriert (basierend auf ignore-Einstellung)" %post.title)
                    continue
                yield (post.title, [post.link], title)
                                

    # Suchfunktion für Downloadlinks (auf der zuvor gefundenen Unterseite):
    def _get_download_links(self, url, hosters_pattern=None):
        # Definiere die zu durchsuchende Baumstruktur (auf Basis der Unterseite)
        tree = html.fromstring(requests.get(url).content)
        # Genaue Anweisung, wo die Links zu finden sind (Unterhalb des Download:/Mirror # Textes)
        xpath = '//*[@id="content"]/span/div/div[2]//strong[contains(text(),"Download:") or contains(text(),"Mirror #")]/following-sibling::a[1]'
        # Jeder link wird zurück gegeben, wenn kein Wunschhoster festgelegt wurde. Ansonsten werden nur Links zum Wunschhoster weitergegeben.
        return [common.get_first(link.xpath('./@href')) for link in tree.xpath(xpath) if hosters_pattern is None or re.search(hosters_pattern, link.text, flags=re.IGNORECASE)]


    # Periodische Aufgabe
    @_restart_timer
    def periodical_task(self):
        # Abbruch, bei Deaktivierter Suche
        if not self.config.get('crawl3d'):
            self.log_debug("Suche für Filme-3D deaktiviert!")
            return
        # Leere/Definiere interne URL/Text-Arrays
        urls = []
        text = []
        
        # Definiere interne Suchliste auf Basis der MB_Serien, MB_Staffeln (und notdl) Listen
        self.allInfos = dict(
            # Füge der Suche sämtliche Titel aus der MB_Filme Liste hinzu
            set({key: value for (key, value) in self.getPatterns(
                    self.readInput(self.filme),
                    self.config.get('quality'),
                    '.*',
                    None
                ).items()}.items()
            )
        )
        
        # Stoppe Suche, wenn Platzhalter aktiv ist.
        if no_mb_3d:
            return
        
        # Stoppe Suche, wenn Option deaktiviert ist.
        if not self.config.get('crawl3d'):
            return

        # Wenn historical aktiv ist nutzt RSScrawler die Suchfunktion von MB, statt nur den (zeitlich begrenzten) Feed zu nutzen. Dies dauert etwas länger, durchsucht aber den kompletten MB!
        if self.config.get("historical"):
            # Suche nach jeder Zeile in der internen Suchliste
            for xline in self.allInfos.keys():
                # Wenn die Zeile nicht leer ist bzw. keine Raute (für Kommentare) enthält:
                if len(xline) > 0 and not xline.startswith("#"):
                    # Entferne Zusatzinfos der obsoleten Funktion, die Listeneinträge wie folgt erwartet: Titel,Auflösung,Gruppe
                    # Die Suche Benötigt nur den Titel vor dem ersten Komma. Ersetze Weiterhin Punkte durch Leerzeichen und diese für die Suche durch ein +
                    xn = xline.split(",")[0].replace(".", " ").replace(" ", "+")
                    # Generiere aus diesen Suchurl-kompatiblen String als Seitenaufruf (entspricht einer Suche auf MB nach dem entsprechenden Titel) eine Liste an Suchanfragen-URLs (Anzahl entspricht Einträgen der internen Suchliste)
                    urls.append('aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZw=='.decode('base64') + '/search/%s/feed/rss2/' %xn)
        # Nutze ansonsten den Feed (und dessen Inhalt) als Grundlage zur Suche
        else:
            # Hierfür wird nur eine einzelne URL (die oben vergebene) benötigt
            urls.append(self.FEED_URL)

        # Suchfunktion für valide Releases (und deren Downloadlinks) wird für jede URL durchgeführt:
        for url in urls:
            # Führe für jeden Eintrag auf der URL eine Suche nach Releases durch:
            for (key, value, pattern) in self.searchLinks(feedparser.parse(url)):
                # Nimm nur den ersten validen Downloadlink der auf der Unterseite eines jeden Releases gefunden wurde
                download_link = common.get_first(self._get_download_links(value[0], self._hosters_pattern))
                # Füge Release nur hinzu, wenn überhaupt ein Link gefunden wurde (erzeuge hierfür einen crawljob)
                if not download_link == None:
                    # Suche nach zweisprachigem Release, sollte das aktuelle nicht zweisprachig sein:
                    if self.config.get('enforcedl') and '.dl.' not in key.lower():
                        # Wenn die Suche für zweisprachige Releases nichts findet (wird zugleich ausgeführt)
                        if not self.download_dl(key):
                            # Logge nicht gefundenes zweisprachiges Release
                            self.log_debug("%s - Kein zweisprachiges Release gefunden" %key)
                                
                    # Wenn das Release als bereits hinzugefügt in der Datenbank vermerkt wurde, logge dies und breche ab
                    if self.db.retrieve(key) == 'added' or self.db.retrieve(key) == 'notdl':
                        self.log_debug("%s - Release ignoriert (bereits gefunden)" % key)
                    # Ansonsten speichere das Release als hinzugefügt in der Datenbank
                    else:
                        # Entferne normale Filme nur, wenn diese die DL-Kriterien erfüllen bzw. enforcedl inaktiv ist.
                        retail = False
                        if (self.config.get('enforcedl') and '.dl.' in key.lower()) or not self.config.get('enforcedl'):
                            # Cutofffunktion um bei Retail Release den Listeneintrag zu entfernen
                            if self.config.get('cutoff'):
                                if common.cutoff(key, '2'):
                                    retail = True

                        # Logge gefundenes Release auch im RSScrawler (Konsole/Logdatei)
                        self.log_info('[Film] - <b>' + ('Retail/' if retail else "") + '3D</b> - ' + key + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')
                                    
                        # Schreibe Crawljob  
                        common.write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler/3Dcrawler"
                        ) and text.append(key)
                        self.db.store(
                            key,
                            # Vermerke Releases, die nicht zweisprachig sind in der Datenbank (falls enforcedl aktiv ist). Speichere jedes gefundene Release
                            'notdl' if self.config.get('enforcedl') and '.dl.' not in key.lower() else 'added',
                            pattern
                        )
        # Wenn zuvor ein key dem Text hinzugefügt wurde (also ein Release gefunden wurde):
        if len(text) > 0 and len(rsscrawler.get("pushbulletapi")) > 0:
            # Löse Pushbullet-Benachrichtigung aus
            common.Pushbullet(rsscrawler.get("pushbulletapi"),text)

class MBstaffeln():
    FEED_URL = "aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZy9mZWVkLw==".decode('base64')
    SUBSTITUTE = "[&#\s/]"
    _INTERNAL_NAME='MB'

    def __init__(self):
        self.config = RssConfig(self._INTERNAL_NAME)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.db = RssDb(os.path.join(os.path.dirname(sys.argv[0]), "Einstellungen/Downloads/MB_Downloads.db"))
        self.db_sj = RssDb(os.path.join(os.path.dirname(sys.argv[0]), "Einstellungen/Downloads/SJ_Downloads.db"))
        self.staffeln = os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/MB_Staffeln.txt')
        self._hosters_pattern = rsscrawler.get('hoster').replace(',','|')
        self._periodical_active = False
        self.periodical = RepeatableTimer(
            int(rsscrawler.get('interval')) * 60,
            self.periodical_task
        )
        self.dictWithNamesAndLinks = {}

    def activate(self):
        self._periodical_active = True
        self.periodical.start()
        return self

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

    def getPatterns(self, patterns, quality, rg, sf):
        # Importiere globale Parameter (sollten beide Falsch sein)
        global no_mb_staffeln
        # Wenn Liste exakt die Platzhalterzeile enthält:
        if patterns == ["XXXXXXXXXX"]:
            # Wenn keine Information zur Quellart weitergegeben wurde (gilt nur bei Staffeln, Standard ist: BluRay):
            # Logge vorhandenen Platzhalter, der in der Filme-Liste stehen muss (da keine Quellart angegeben)
            self.log_debug("Liste enthält Platzhalter. Stoppe Suche für Staffeln!")
            # Setze globale Variable auf wahr, um in der MB-Klasse die Suche abbrechen zu können
            no_mb_staffeln = True
        # Ansonsten gib die Zeilen einzeln als Zeilen in patters zurück
        return {line: (quality, rg, sf) for line in patterns}

    def searchLinks(self, feed):
        ignore = "|".join(["\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if not self.config.get("ignore") == "" else "^unmatchable$"
        
        for key in self.allInfos:
            s = re.sub(self.SUBSTITUTE,".","^" + key).lower()
            for post in feed.entries:
                found = re.search(s,post.title.lower())
                if found:
                    found = re.search(ignore,post.title.lower())
                    if found:
                        # Wenn zu ignorierender Eintrag, logge diesen
                        self.log_debug("%s - Release ignoriert (basierend auf ignore-Einstellung)" %post.title)
                        continue
                    # Prüfe Quellart
                    validsource = re.search(self.config.get("seasonssource"),post.title.lower())
                    if not validsource:
                        self.log_debug(post.title + " - Release hat falsche Quelle")
                        continue
                    # Ignoriere Staffelpakete. Sind häufig Duplikate alter, inkl. soeben erschienener Staffeln und bis zu mehrere hundert GB groß
                    if self.config.get("seasonpacks") == "False":
                        staffelpack = re.search("s\d.*(-|\.).*s\d",post.title.lower())
                        if staffelpack:
                            self.log_debug("%s - Release ignoriert (Staffelpaket)" %post.title)
                            continue
                    ss = self.allInfos[key][0].lower()

                    if ss == "480p":
                        if "720p" in post.title.lower() or "1080p" in post.title.lower() or "1080i" in post.title.lower():
                            continue
                        found = True
                    else:
                        found = re.search(ss,post.title.lower())
                    if found:
                        # Funktion, die Listeneinträge wie folgt erwartet: Titel,Auflösung,Gruppe
                        sss = "[\.-]+"+self.allInfos[key][1].lower()
                        found = re.search(sss,post.title.lower())

                        if self.allInfos[key][2]:
                            # Wenn alles True, dann found = True (also gilt Release nur als gefunden, wenn alle Parameter wahr sind)
                            found = all([word in post.title.lower() for word in self.allInfos[key][2]])

                        if found:
                            # Check, ob das Release zu einer Serie gehört
                            try:
                                episode = re.search(r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*',post.title.lower()).group(1)
                                if "repack" in post.title.lower():
                                    episode = episode + "-repack"
                                self.log_debug("Serie entdeckt. Kürze Titel: [%s]" %episode)
                                yield (episode, [post.link], key)
                            except:
                                # Gebe den Link (der alle obigen Checks bestandend hat) weiter
                                yield (post.title, [post.link], key)
                                
    def download_dl(self, title):
        # Schreibe den nicht-zweisprachigen Titel für die folgende Suche um
        text = []
        # Dies generiert den in die Suche einfügbaren String (+ statt Leerzeichen)
        search_title = title.replace(".German.720p.", ".German.DL.1080p.").replace(".German.DTS.720p.", ".German.DTS.DL.1080p.").replace(".German.AC3.720p.", ".German.AC3.DL.1080p.").replace(".German.AC3LD.720p.", ".German.AC3LD.DL.1080p.").replace(".German.AC3.Dubbed.720p.", ".German.AC3.Dubbed.DL.1080p.").split('.x264-', 1)[0].split('.h264-', 1)[0].replace(".", " ").replace(" ", "+")
        search_url = "aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZy9zZWFyY2gv".decode('base64') + search_title + "/feed/rss2/"
        # Nach diesem String (also Releasetitel) wird schlussendlich in den Suchergebnissen gesucht (. statt Leerzeichen)
        feedsearch_title = title.replace(".German.720p.", ".German.DL.1080p.").replace(".German.DTS.720p.", ".German.DTS.DL.1080p.").replace(".German.AC3.720p.", ".German.AC3.DL.1080p.").replace(".German.AC3LD.720p.", ".German.AC3LD.DL.1080p.").replace(".German.AC3.Dubbed.720p.", ".German.AC3.Dubbed.DL.1080p.").split('.x264-', 1)[0].split('.h264-', 1)[0]
        if not '.dl.' in feedsearch_title.lower():
            self.log_debug("%s - Release ignoriert (nicht zweisprachig, da wahrscheinlich nicht Retail)" %feedsearch_title)
            return
        
        # Suche nach title im Ergebnisfeed der obigen Suche (nicht nach dem für die suche genutzten search_title)
        for (key, value, pattern) in self.dl_search(feedparser.parse(search_url), feedsearch_title, title):
            # Nimm nur den ersten validen Downloadlink der auf der Unterseite eines jeden Releases gefunden wurde
            download_link = common.get_first(self._get_download_links(value[0], self._hosters_pattern))
            # Füge Release nur hinzu, wenn überhaupt ein Link gefunden wurde (erzeuge hierfür einen crawljob)
            if not download_link == None:
                # Wenn das Release als bereits hinzugefügt in der Datenbank vermerkt wurde, logge dies und breche ab
                if self.db.retrieve(key) == 'added' or self.db.retrieve(key) == 'dl':
                    self.log_debug("%s - zweisprachiges Release ignoriert (bereits gefunden)" % key)
                # Ansonsten speichere das Release als hinzugefügt in der Datenbank
                else:
                    # Logge gefundenes Release auch im RSScrawler (Konsole/Logdatei)
                    self.log_info('[Staffel] - <b>Zweisprachig</b> - ' + key + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')
                
                    # Schreibe Crawljob            
                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler/Remux"
                    ) and text.append(key)
                    self.db.store(
                        key,
                        # Vermerke zweisprachiges Release entsprechend in der Datenbank
                        'dl' if self.config.get('enforcedl') and '.dl.' in key.lower() else 'added',
                        pattern
                        )
                
    def dl_search(self, feed, title, notdl_title):
        ignore = "|".join(["\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if not self.config.get("ignore") == "" else "^unmatchable$"
            
        s = re.sub(self.SUBSTITUTE,".",title).lower()
        for post in feed.entries:
            found = re.search(s,post.title.lower())
            if found:
                found = re.search(ignore,post.title.lower())
                if found:
                    # Wenn zu ignorierender Eintrag, logge diesen
                    self.log_debug("%s - zweisprachiges Release ignoriert (basierend auf ignore-Einstellung)" %post.title)
                    continue
                yield (post.title, [post.link], title)
                                
    # Suchfunktion für Downloadlinks (auf der zuvor gefundenen Unterseite):
    def _get_download_links(self, url, hosters_pattern=None):
        # Definiere die zu durchsuchende Baumstruktur (auf Basis der Unterseite)
        tree = html.fromstring(requests.get(url).content)
        # Genaue Anweisung, wo die Links zu finden sind (Unterhalb des Download:/Mirror # Textes)
        xpath = '//*[@id="content"]/span/div/div[2]//strong[contains(text(),"Download:") or contains(text(),"Mirror #")]/following-sibling::a[1]'
        # Jeder link wird zurück gegeben, wenn kein Wunschhoster festgelegt wurde. Ansonsten werden nur Links zum Wunschhoster weitergegeben.
        return [common.get_first(link.xpath('./@href')) for link in tree.xpath(xpath) if hosters_pattern is None or re.search(hosters_pattern, link.text, flags=re.IGNORECASE)]

    # Periodische Aufgabe
    @_restart_timer
    def periodical_task(self):
        # Abbruch, bei Deaktivierter Suche
        if not self.config.get('crawlseasons'):
            self.log_debug("Suche für MB-Staffeln deaktiviert!")
            return
        # Leere/Definiere interne URL/Text-Arrays
        urls = []
        text = []
            
        # Definiere interne Suchliste auf Basis der MB_Staffeln Liste
        self.allInfos = dict(
            # Füge der Suche sämtliche Titel aus der MB_Staffeln Liste hinzu
            set({key: value for (key, value) in self.getPatterns(
                    self.readInput(self.staffeln),
                    self.config.get('seasonsquality'),
                    '.*',
                    ('.complete.')
            ).items()}.items()
            )
        )
        
        # Stoppe Suche, wenn Platzhalter aktiv ist.
        if no_mb_staffeln:
            return

        # Stoppe Suche, wenn Option deaktiviert ist.
        if not self.config.get('crawlseasons'):
            return

        # Wenn historical aktiv ist nutzt RSScrawler die Suchfunktion von MB, statt nur den (zeitlich begrenzten) Feed zu nutzen. Dies dauert etwas länger, durchsucht aber den kompletten MB!
        if self.config.get("historical"):
            # Suche nach jeder Zeile in der internen Suchliste
            for xline in self.allInfos.keys():
                # Wenn die Zeile nicht leer ist bzw. keine Raute (für Kommentare) enthält:
                if len(xline) > 0 and not xline.startswith("#"):
                    # Entferne Zusatzinfos der obsoleten Funktion, die Listeneinträge wie folgt erwartet: Titel,Auflösung,Gruppe
                    # Die Suche Benötigt nur den Titel vor dem ersten Komma. Ersetze Weiterhin Punkte durch Leerzeichen und diese für die Suche durch ein +
                    xn = xline.split(",")[0].replace(".", " ").replace(" ", "+")
                    # Generiere aus diesen Suchurl-kompatiblen String als Seitenaufruf (entspricht einer Suche auf MB nach dem entsprechenden Titel) eine Liste an Suchanfragen-URLs (Anzahl entspricht Einträgen der internen Suchliste)
                    urls.append('aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZw=='.decode('base64') + '/search/%s/feed/rss2/' %xn)
        # Nutze ansonsten den Feed (und dessen Inhalt) als Grundlage zur Suche
        else:
            # Hierfür wird nur eine einzelne URL (die oben vergebene) benötigt
            urls.append(self.FEED_URL)

        # Suchfunktion für valide Releases (und deren Downloadlinks) wird für jede URL durchgeführt:
        for url in urls:
            # Führe für jeden Eintrag auf der URL eine Suche nach Releases durch:
            for (key, value, pattern) in self.searchLinks(feedparser.parse(url)):
                # Nimm nur den ersten validen Downloadlink der auf der Unterseite eines jeden Releases gefunden wurde
                download_link = common.get_first(self._get_download_links(value[0], self._hosters_pattern))
                # Füge Release nur hinzu, wenn überhaupt ein Link gefunden wurde (erzeuge hierfür einen crawljob)
                if not download_link == None:
                    # Suche nach zweisprachigem Release, sollte das aktuelle nicht zweisprachig sein:
                    if self.config.get('enforcedl') and '.dl.' not in key.lower():
                        # Wenn die Suche für zweisprachige Releases nichts findet (wird zugleich ausgeführt)
                        if not self.download_dl(key):
                            # Logge nicht gefundenes zweisprachiges Release
                            self.log_debug("%s - Kein zweisprachiges Release gefunden" %key)
                                
                    # Wenn das Release als bereits hinzugefügt in der Datenbank vermerkt wurde, logge dies und breche ab
                    if self.db.retrieve(key) == 'added' or self.db.retrieve(key) == 'notdl':
                        self.log_debug("%s - Release ignoriert (bereits gefunden)" % key)
                    # Ansonsten speichere das Release als hinzugefügt in der Datenbank
                    else:
                        # Logge gefundenes Release auch im RSScrawler (Konsole/Logdatei)
                        self.log_info('[Staffel] - ' + key.replace(".COMPLETE.", ".") + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')
                                    
                        # Schreibe Crawljob  
                        common.write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler"
                        ) and text.append(key)
                        self.db.store(
                            key,
                            # Vermerke Releases, die nicht zweisprachig sind in der Datenbank (falls enforcedl aktiv ist). Speichere jedes gefundene Release
                            'notdl' if self.config.get('enforcedl') and '.dl.' not in key.lower() else 'added',
                            pattern
                        )
                        # Speichere geladene Staffel auch in SJ Datenbank
                        self.db_sj.store(
                            key.replace(".COMPLETE", "").replace(".Complete", ""),
                            'downloaded',
                            pattern
                        )
        # Wenn zuvor ein key dem Text hinzugefügt wurde (also ein Release gefunden wurde):
        if len(text) > 0 and len(rsscrawler.get("pushbulletapi")) > 0:
            # Löse Pushbullet-Benachrichtigung aus
            common.Pushbullet(rsscrawler.get("pushbulletapi"),text)

class MBregex():
    FEED_URL = "aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZy9mZWVkLw==".decode('base64')
    SUBSTITUTE = "[&#\s/]"
    _INTERNAL_NAME='MB'

    def __init__(self):
        self.config = RssConfig(self._INTERNAL_NAME)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.db = RssDb(os.path.join(os.path.dirname(sys.argv[0]), "Einstellungen/Downloads/MB_Downloads.db"))
        self.regex = os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/MB_Regex.txt')
        self._hosters_pattern = rsscrawler.get('hoster').replace(',','|')
        self._periodical_active = False
        self.periodical = RepeatableTimer(
            int(rsscrawler.get('interval')) * 60,
            self.periodical_task
        )
        self.dictWithNamesAndLinks = {}

    def activate(self):
        self._periodical_active = True
        self.periodical.start()
        return self

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

    def getPatterns(self, patterns):
        # Importiere globale Parameter (sollten beide Falsch sein)
        global no_mb_regex
        # Wenn Liste exakt die Platzhalterzeile enthält:
        if patterns == ["XXXXXXXXXX"]:
            self.log_debug("Liste enthält Platzhalter. Stoppe Suche für Filme/Serien (RegEx)!")
            # Setze globale Variable auf wahr, um in der MB-Klasse die Suche abbrechen zu können
            no_mb_regex = True
        # Ansonsten gib die Zeilen einzeln als Zeilen in patters zurück
        return {x: (x) for x in patterns}

    def searchLinks(self, feed):
        for key in self.allInfos:
            s = re.sub(self.SUBSTITUTE,".","^" + key).lower()
            for post in feed.entries:
                found = re.search(s,post.title.lower())
                if found:
                    yield (post.title, [post.link], key)
                    
    def download_dl(self, title):
        # Schreibe den nicht-zweisprachigen Titel für die folgende Suche um
        text = []
        # Dies generiert den in die Suche einfügbaren String (+ statt Leerzeichen)
        search_title = title.replace(".German.720p.", ".German.DL.1080p.").replace(".German.DTS.720p.", ".German.DTS.DL.1080p.").replace(".German.AC3.720p.", ".German.AC3.DL.1080p.").replace(".German.AC3LD.720p.", ".German.AC3LD.DL.1080p.").replace(".German.AC3.Dubbed.720p.", ".German.AC3.Dubbed.DL.1080p.").split('.x264-', 1)[0].split('.h264-', 1)[0].replace(".", " ").replace(" ", "+")
        search_url = "aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZy9zZWFyY2gv".decode('base64') + search_title + "/feed/rss2/"
        # Nach diesem String (also Releasetitel) wird schlussendlich in den Suchergebnissen gesucht (. statt Leerzeichen)
        feedsearch_title = title.replace(".German.720p.", ".German.DL.1080p.").replace(".German.DTS.720p.", ".German.DTS.DL.1080p.").replace(".German.AC3.720p.", ".German.AC3.DL.1080p.").replace(".German.AC3LD.720p.", ".German.AC3LD.DL.1080p.").replace(".German.AC3.Dubbed.720p.", ".German.AC3.Dubbed.DL.1080p.").split('.x264-', 1)[0].split('.h264-', 1)[0]
        if not '.dl.' in feedsearch_title.lower():
            self.log_debug("%s - Release ignoriert (nicht zweisprachig, da wahrscheinlich nicht Retail)" %feedsearch_title)
            return
        
        # Suche nach title im Ergebnisfeed der obigen Suche (nicht nach dem für die suche genutzten search_title)
        for (key, value, pattern) in self.dl_search(feedparser.parse(search_url), feedsearch_title, title):
            # Nimm nur den ersten validen Downloadlink der auf der Unterseite eines jeden Releases gefunden wurde
            download_link = common.get_first(self._get_download_links(value[0], self._hosters_pattern))
            # Füge Release nur hinzu, wenn überhaupt ein Link gefunden wurde (erzeuge hierfür einen crawljob)
            if not download_link == None:
                # Wenn das Release als bereits hinzugefügt in der Datenbank vermerkt wurde, logge dies und breche ab
                if self.db.retrieve(key) == 'added' or self.db.retrieve(key) == 'dl':
                    self.log_debug("%s - zweisprachiges Release ignoriert (bereits gefunden)" % key)
                # Ansonsten speichere das Release als hinzugefügt in der Datenbank
                else:
                    # Logge gefundenes Release auch im RSScrawler (Konsole/Logdatei)
                    self.log_info('[Film/Serie/RegEx] - <b>Zweisprachig</b> - ' + key + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')
                
                    # Schreibe Crawljob            
                    common.write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler/Remux"
                    ) and text.append(key)
                    self.db.store(
                        key,
                        # Vermerke zweisprachiges Release entsprechend in der Datenbank
                        'dl' if self.config.get('enforcedl') and '.dl.' in key.lower() else 'added',
                        pattern
                        )
        # Wenn zuvor ein key dem Text hinzugefügt wurde (also ein Release gefunden wurde):
        if len(text) > 0 and len(rsscrawler.get("pushbulletapi")) > 0:
            # Löse Pushbullet-Benachrichtigung aus
            common.Pushbullet(rsscrawler.get("pushbulletapi"),text)
            return True
                
    def dl_search(self, feed, title, notdl_title):
        ignore = "|".join(["\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if not self.config.get("ignore") == "" else "^unmatchable$"
            
        s = re.sub(self.SUBSTITUTE,".",title).lower()
        for post in feed.entries:
            found = re.search(s,post.title.lower())
            if found:
                found = re.search(ignore,post.title.lower())
                if found:
                    # Wenn zu ignorierender Eintrag, logge diesen
                    self.log_debug("%s - zweisprachiges Release ignoriert (basierend auf ignore-Einstellung)" %post.title)
                    continue
                yield (post.title, [post.link], title)
                
    # Suchfunktion für Downloadlinks (auf der zuvor gefundenen Unterseite):
    def _get_download_links(self, url, hosters_pattern=None):
        # Definiere die zu durchsuchende Baumstruktur (auf Basis der Unterseite)
        tree = html.fromstring(requests.get(url).content)
        # Genaue Anweisung, wo die Links zu finden sind (Unterhalb des Download:/Mirror # Textes)
        xpath = '//*[@id="content"]/span/div/div[2]//strong[contains(text(),"Download:") or contains(text(),"Mirror #")]/following-sibling::a[1]'
        # Jeder link wird zurück gegeben, wenn kein Wunschhoster festgelegt wurde. Ansonsten werden nur Links zum Wunschhoster weitergegeben.
        return [common.get_first(link.xpath('./@href')) for link in tree.xpath(xpath) if hosters_pattern is None or re.search(hosters_pattern, link.text, flags=re.IGNORECASE)]

    # Periodische Aufgabe
    @_restart_timer
    def periodical_task(self):
        # Abbruch, bei Deaktivierter Suche
        if not self.config.get('regex'):
            self.log_debug("Suche für MB-Regex deaktiviert!")
            return
        # Leere/Definiere interne URL/Text-Arrays
        urls = []
        text = []
        
        # Definiere interne Suchliste auf Basis der MB_Serien, MB_Staffeln (und notdl) Listen
        self.allInfos = dict(
            # Füge der Suche sämtliche Titel aus der MB_Filme Liste hinzu
            set({key: value for (key, value) in self.getPatterns(
                    self.readInput(self.regex)
                ).items()}.items()
            ) if self.config.get('regex') else []
        )
        # Stoppe Suche, wenn Platzhalter aktiv ist ist.
        if no_mb_regex:
            return

        # Stoppe Suche, wenn Option deaktiviert ist.
        if not self.config.get('regex'):
            return
        
        # Setzte Url zur Suche (nur Feed für Regex)
        urls.append(self.FEED_URL)

        # Suchfunktion für valide Releases (und deren Downloadlinks) wird für jede URL durchgeführt:
        for url in urls:
            # Führe für jeden Eintrag auf der URL eine Suche nach Releases durch:
            for (key, value, pattern) in self.searchLinks(feedparser.parse(url)):
                # Nimm nur den ersten validen Downloadlink der auf der Unterseite eines jeden Releases gefunden wurde
                download_link = common.get_first(self._get_download_links(value[0], self._hosters_pattern))
                # Füge Release nur hinzu, wenn überhaupt ein Link gefunden wurde (erzeuge hierfür einen crawljob)
                if not download_link == None:
                    # Suche nach zweisprachigem Release, sollte das aktuelle nicht zweisprachig sein:
                    if self.config.get('enforcedl') and '.dl.' not in key.lower():
                        # Wenn die Suche für zweisprachige Releases nichts findet (wird zugleich ausgeführt)
                        if not self.download_dl(key):
                            # Logge nicht gefundenes zweisprachiges Release
                            self.log_debug("%s - Kein zweisprachiges Release gefunden" %key)
                                
                    # Wenn das Release als bereits hinzugefügt in der Datenbank vermerkt wurde, logge dies und breche ab
                    if self.db.retrieve(key) == 'added' or self.db.retrieve(key) == 'notdl':
                        self.log_debug("%s - Release ignoriert (bereits gefunden)" % key)
                    # Ansonsten speichere das Release als hinzugefügt in der Datenbank
                    else:
                        # Logge gefundenes Release auch im RSScrawler (Konsole/Logdatei)
                        self.log_info('[Film/Serie/RegEx] - ' + key + ' - [<a href="' + download_link + '" target="_blank">Link</a>]')
                                    
                        # Schreibe Crawljob  
                        common.write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler"
                        ) and text.append(key)
                        self.db.store(
                            key,
                            # Vermerke Releases, die nicht zweisprachig sind in der Datenbank (falls enforcedl aktiv ist). Speichere jedes gefundene Release
                            'notdl' if self.config.get('enforcedl') and '.dl.' not in key.lower() else 'added',
                            pattern
                        )
        # Wenn zuvor ein key dem Text hinzugefügt wurde (also ein Release gefunden wurde):
        if len(text) > 0 and len(rsscrawler.get("pushbulletapi")) > 0:
            # Löse Pushbullet-Benachrichtigung aus
            common.Pushbullet(rsscrawler.get("pushbulletapi"),text)

def getSeriesList(file, type):
    global no_sj_serien
    global no_sj_regex
    global no_sj_staffeln
    
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
            logging.debug("Liste enthält Platzhalter. Stoppe Suche für Serien!" + loginfo)
            if type == 1:
                no_sj_regex = True
            elif type == 2:
                no_sj_staffeln = True
            else:
                no_sj_serien = True
        return titles
    except UnicodeError:
        logging.error("ANGEHALTEN, ungültiges Zeichen in Serien" + loginfo + "Liste!")
    except IOError:
        logging.error("ANGEHALTEN, Serien" + loginfo + "-Liste nicht gefunden!")
    except Exception, e:
        logging.error("Unbekannter Fehler: %s" %e)
        
def getURL(url):
    try:
        req = urllib2.Request(
            url,
            None,
            {'User-agent' : 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36'}
        )
        return urllib2.urlopen(req).read()
    except urllib2.HTTPError as e:
        logging.debug('Bei der HTTP-Anfrage ist ein Fehler Aufgetreten: Fehler: %s Grund: %s' % (e.code, e.reason))
        return ''
    except urllib2.URLError as e:
        logging.debug('Bei der HTTP-Anfrage ist ein Fehler Aufgetreten: Grund: %s' %  e.reason)
        return ''
    except socket.error as e:
        logging.debug('Die HTTP-Anfrage wurde unterbrochen. Grund: %s' %  e)
        return ''

class SJ():
    _INTERNAL_NAME = 'SJ'

    def __init__(self):
        self.config = RssConfig(self._INTERNAL_NAME)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.db = RssDb(os.path.join(os.path.dirname(sys.argv[0]), "Einstellungen/Downloads/SJ_Downloads.db"))
        self.serien = os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/SJ_Serien.txt')
        self._periodical_active = False
        self.periodical = RepeatableTimer(
            int(rsscrawler.get('interval')) * 60,
            self.periodical_task
        )

    def activate(self):
        self._periodical_active = True
        self.periodical.start()
        return self

    @_restart_timer
    def periodical_task(self):
        feed = feedparser.parse('aHR0cDovL3Nlcmllbmp1bmtpZXMub3JnL3htbC9mZWVkcy9lcGlzb2Rlbi54bWw='.decode('base64'))
        self.pattern = "|".join(getSeriesList(self.serien, 0)).lower()
        

        # Stoppe Suche, wenn Platzhalter aktiv ist.
        if no_sj_serien:
            return

        reject = self.config.get("rejectlist").replace(",","|").lower() if len(self.config.get("rejectlist")) > 0 else "^unmatchable$"
        self.quality = self.config.get("quality")
        self.hoster = rsscrawler.get("hoster")

        # Lege Array als Typ für die added_items fest (Liste bereits hinzugefügter Releases)
        self.added_items = []

        for post in feed.entries:
            # Seltenen Fehler, bei dem ein Feedeintrag (noch) keinen Link enthält, umgehen:
            if post.link == None:
              continue
          
            link = post.link
            title = post.title

            if self.config.get("quality") != '480p':
                m = re.search(self.pattern,title.lower())
                if m:
                    if '[DEUTSCH]' in title:
                        mm = re.search(self.quality,title.lower())
                        if mm:
                            mmm = re.search(reject,title.lower())
                            if mmm:
                                self.log_debug(title +" - Release ignoriert (basierend auf rejectlist-Einstellung)")
                                continue
                            title = re.sub('\[.*\] ', '', post.title)
                            self.range_checkr(link,title)

                else:
                    m = re.search(self.pattern,title.lower())
                    if m:
                        if '[DEUTSCH]' in title:
                            if "720p" in title.lower() or "1080p" in title.lower():
                                continue
                            mm = re.search(reject,title.lower())
                            if mm:
                                self.log_debug(title +" Release ignoriert (basierend auf rejectlist-Einstellung)")
                                continue
                            title = re.sub('\[.*\] ', '', post.title)
                            self.range_checkr(link,title)

        if len(rsscrawler.get('pushbulletapi')) > 2:
            common.Pushbullet(rsscrawler.get("pushbulletapi"),self.added_items) if len(self.added_items) > 0 else True

    def range_checkr(self, link, title):
        pattern = re.match(".*S\d{2}E\d{2}-\w?\d{2}.*", title)
        if pattern is not None:
            range0 = re.sub(r".*S\d{2}E(\d{2}-\w?\d{2}).*",r"\1", title).replace("E","")
            number1 = re.sub(r"(\d{2})-\d{2}",r"\1", range0)
            number2 = re.sub(r"\d{2}-(\d{2})",r"\1", range0)
            title_cut = re.findall(r"(.*S\d{2}E)(\d{2}-\w?\d{2})(.*)",title)
            try:
                for count in range(int(number1),(int(number2)+1)):
                    NR = re.match("\d{2}", str(count))
                    if NR is not None:
                        title1 = title_cut[0][0] + str(count) + ".*" + title_cut[0][-1]
                        self.range_parse(link, title1)
                    else:
                        title1 = title_cut[0][0] + "0" + str(count) + ".*" + title_cut[0][-1]
                        self.range_parse(link, title1)
            except ValueError as e:
                logging.error("Fehler in Variablenwert: %s" %e.message)
        else:
            self.parse_download(link, title)

    def range_parse(self,series_url, search_title):
        req_page = getURL(series_url)
        soup = BeautifulSoup(req_page)

        try:
            titles = soup.findAll(text=re.compile(search_title))
            for title in titles:
               if self.quality !='480p' and self.quality in title:
                   self.parse_download(series_url, title)
               if self.quality =='480p' and not (('.720p.' in title) or ('.1080p.' in title)):
                   self.parse_download(series_url, title)
        except re.error as e:
            self.log_error('Konstantenfehler: %s' % e)


    def parse_download(self,series_url, search_title):
        req_page = getURL(series_url)
        soup = BeautifulSoup(req_page)
        
        # Da das beautifulsoup per Regex sucht, darf der Suchstring keine Klammern enthalten. Ersetze diese entsprechend durch Wildcard
        escape_brackets = search_title.replace("(", ".*").replace(")", ".*").replace("+", ".*")

        title = soup.find(text=re.compile(escape_brackets))
        if title:
            url_hosters = re.findall('<a href="([^"\'>]*)".+?\| (.+?)<', str(title.parent.parent))
            for url_hoster in url_hosters:
                if self.hoster.lower() in url_hoster[1]:
                    self.send_package(title, url_hoster[0])

    def send_package(self, title, link):
        try:
            storage = self.db.retrieve(title)
        except Exception as e:
            self.log_debug("Fehler bei Datenbankzugriff: %s, Grund: %s" % (e,title))
        if storage == 'downloaded':
            self.log_debug(title + " - Release ignoriert (bereits gefunden)")
        else:
            self.log_info('[Episode] - ' + title + ' - [<a href="' + link + '" target="_blank">Link</a>]')
            self.db.store(title, 'downloaded')
            common.write_crawljob_file(title, title, link,
                                jdownloaderpath + "/folderwatch", "RSScrawler") and self.added_items.append(title.encode("utf-8"))

class SJregex():
    _INTERNAL_NAME = 'SJ'

    def __init__(self):
        self.config = RssConfig(self._INTERNAL_NAME)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.db = RssDb(os.path.join(os.path.dirname(sys.argv[0]), "Einstellungen/Downloads/SJ_Downloads.db"))
        self.regex = os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/SJ_Serien_Regex.txt')
        self._periodical_active = False
        self.periodical = RepeatableTimer(
            int(rsscrawler.get('interval')) * 60,
            self.periodical_task
        )

    def activate(self):
        self._periodical_active = True
        if self.config.get("regex"):
          self.periodical.start()
        return self

    @_restart_timer
    def periodical_task(self):
        # Abbruch, bei Deaktivierter Suche
        if not self.config.get('regex'):
            self.log_debug("Suche für SJ-Regex deaktiviert!")
            return
        feed = feedparser.parse('aHR0cDovL3Nlcmllbmp1bmtpZXMub3JnL3htbC9mZWVkcy9lcGlzb2Rlbi54bWw='.decode('base64'))
        self.pattern = "|".join(getSeriesList(self.regex, 1)).lower()
        
        # Stoppe Suche, wenn Liste Platzhalter enthält
        if no_sj_regex:
            return
        
        reject = self.config.get("rejectlist").replace(",","|").lower() if len(self.config.get("rejectlist")) > 0 else "^unmatchable$"
        self.quality = self.config.get("quality")
        self.hoster = rsscrawler.get("hoster")

        # Lege Array als Typ für die added_items fest (Liste bereits hinzugefügter Releases)
        self.added_items = []

        for post in feed.entries:
            link = post.link
            title = post.title

            if self.config.get("regex"):
                m = re.search(self.pattern,title.lower())
                if not m and not "720p" in title and not "1080p" in title:
                    m = re.search(self.pattern.replace("480p","."),title.lower())
                    self.quality = "480p"
                if m:
                    if "720p" in title.lower(): self.quality = "720p"
                    if "1080p" in title.lower(): self.quality = "1080p"
                    m = re.search(reject,title.lower())
                    if m:
                        self.log_debug(title + " - Release durch Regex gefunden (trotz rejectlist-Einstellung)")
                    title = re.sub('\[.*\] ', '', post.title)
                    self.range_checkr(link,title)

            else:
                continue
            
        if len(rsscrawler.get('pushbulletapi')) > 2:
            common.Pushbullet(rsscrawler.get("pushbulletapi"),self.added_items) if len(self.added_items) > 0 else True

    def range_checkr(self, link, title):
        pattern = re.match(".*S\d{2}E\d{2}-\w?\d{2}.*", title)
        if pattern is not None:
            range0 = re.sub(r".*S\d{2}E(\d{2}-\w?\d{2}).*",r"\1", title).replace("E","")
            number1 = re.sub(r"(\d{2})-\d{2}",r"\1", range0)
            number2 = re.sub(r"\d{2}-(\d{2})",r"\1", range0)
            title_cut = re.findall(r"(.*S\d{2}E)(\d{2}-\w?\d{2})(.*)",title)
            try:
                for count in range(int(number1),(int(number2)+1)):
                    NR = re.match("\d{2}", str(count))
                    if NR is not None:
                        title1 = title_cut[0][0] + str(count) + ".*" + title_cut[0][-1]
                        self.range_parse(link, title1)
                    else:
                        title1 = title_cut[0][0] + "0" + str(count) + ".*" + title_cut[0][-1]
                        self.range_parse(link, title1)
            except ValueError as e:
                logging.error("Fehler in Variablenwert: %s" %e.message)
        else:
            self.parse_download(link, title)

    def range_parse(self,series_url, search_title):
        req_page = getURL(series_url)
        soup = BeautifulSoup(req_page)

        try:
            titles = soup.findAll(text=re.compile(search_title))
            for title in titles:
               if self.quality !='480p' and self.quality in title:
                   self.parse_download(series_url, title)
               if self.quality =='480p' and not (('.720p.' in title) or ('.1080p.' in title)):
                   self.parse_download(series_url, title)
        except re.error as e:
            self.log_error('sre_constants.error: %s' % e)


    def parse_download(self,series_url, search_title):
        req_page = getURL(series_url)
        soup = BeautifulSoup(req_page)
        
        # Da das beautifulsoup per Regex sucht, darf der Suchstring keine Klammern enthalten. Ersetze diese entsprechend durch Wildcard
        escape_brackets = search_title.replace("(", ".*").replace(")", ".*").replace("+", ".*")
        
        title = soup.find(text=re.compile(escape_brackets))
        if title:
            url_hosters = re.findall('<a href="([^"\'>]*)".+?\| (.+?)<', str(title.parent.parent))
            for url_hoster in url_hosters:
                if self.hoster.lower() in url_hoster[1]:
                    self.send_package(title, url_hoster[0])

    def send_package(self, title, link):
        try:
            storage = self.db.retrieve(title)
        except Exception as e:
            self.log_debug("Fehler bei Datenbankzugriff: %s, Grund: %s" % (e,title))
        if storage == 'downloaded':
            self.log_debug(title + " - Release ignoriert (bereits gefunden)")
        else:
            self.log_info('[Episode/RegEx] - ' + title + ' - [<a href="' + link + '" target="_blank">Link</a>]')
            self.db.store(title, 'downloaded')
            common.write_crawljob_file(title, title, link,
                                jdownloaderpath + "/folderwatch", "RSScrawler") and self.added_items.append(title.encode("utf-8"))

class SJstaffeln():
    _INTERNAL_NAME = 'MB'

    def __init__(self):
        self.config = RssConfig(self._INTERNAL_NAME)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.db = RssDb(os.path.join(os.path.dirname(sys.argv[0]), "Einstellungen/Downloads/SJ_Downloads.db"))
        self.staffeln = os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/MB_Staffeln.txt')
        self.seasonssource = self.config.get('seasonssource').lower()
        self._periodical_active = False
        self.periodical = RepeatableTimer(
            int(rsscrawler.get('interval')) * 60,
            self.periodical_task
        )

    def activate(self):
        self._periodical_active = True
        self.periodical.start()
        return self

    @_restart_timer
    def periodical_task(self):
        # Abbruch, bei Deaktivierter Suche
        if not self.config.get('crawlseasons'):
            self.log_debug("Suche für SJ-Staffeln deaktiviert!")
            return
        feed = feedparser.parse('aHR0cDovL3Nlcmllbmp1bmtpZXMub3JnL3htbC9mZWVkcy9zdGFmZmVsbi54bWw='.decode('base64'))
        self.pattern = "|".join(getSeriesList(self.staffeln, 2)).lower()
        
        # Stoppe Suche, wenn Platzhalter aktiv ist.
        if no_sj_staffeln:
            return

        reject = self.config.get("ignore").replace(",","|").lower() if len(self.config.get("ignore")) > 0 else "^unmatchable$"
        self.quality = self.config.get("seasonsquality")
        self.hoster = rsscrawler.get("hoster")

        # Lege Array als Typ für die added_items fest (Liste bereits hinzugefügter Releases)
        self.added_items = []

        for post in feed.entries:
            # Seltenen Fehler, bei dem ein Feedeintrag (noch) keinen Link enthält, umgehen:
            if post.link == None:
              continue
          
            link = post.link
            title = post.title

            if self.config.get("quality") != '480p':
                m = re.search(self.pattern,title.lower())
                if m:
                    if '[DEUTSCH]' in title:
                        mm = re.search(self.quality,title.lower())
                        if mm:
                            mmm = re.search(reject,title.lower())
                            if mmm:
                                self.log_debug(title +" - Release ignoriert (basierend auf rejectlist-Einstellung)")
                                continue
                            title = re.sub('\[.*\] ', '', post.title)
                            self.range_checkr(link, title)

                else:
                    m = re.search(self.pattern,title.lower())
                    if m:
                        if '[DEUTSCH]' in title:
                            if "720p" in title.lower() or "1080p" in title.lower():
                                continue
                            mm = re.search(reject,title.lower())
                            if mm:
                                self.log_debug(title +" Release ignoriert (basierend auf rejectlist-Einstellung)")
                                continue
                            title = re.sub('\[.*\] ', '', post.title)
                            self.range_checkr(link, title)

        if len(rsscrawler.get('pushbulletapi')) > 2:
            common.Pushbullet(rsscrawler.get("pushbulletapi"),self.added_items) if len(self.added_items) > 0 else True

    def range_checkr(self, link, title):
        # Ignoriere Staffelpakete. Sind häufig Duplikate alter, inkl. soeben erschienener Staffeln und bis zu mehrere hundert GB groß
        if self.config.get("seasonpacks") == "False":
            staffelpack = re.search("s\d.*(-|\.).*s\d",title.lower())
            if staffelpack:
                self.log_debug("%s - Release ignoriert (Staffelpaket)" %title)
                return
        pattern = re.match(".*S\d{2}-\w?\d{2}.*", title)
        if pattern is not None:
            range0 = re.sub(r".*S(\d{2}-\w?\d{2}).*",r"\1", title).replace("S","")
            number1 = re.sub(r"(\d{2})-\d{2}",r"\1", range0)
            number2 = re.sub(r"\d{2}-(\d{2})",r"\1", range0)
            title_cut = re.findall(r"(.*S)(\d{2}-\w?\d{2})(.*)",title)
            try:
                for count in range(int(number1),(int(number2)+1)):
                    NR = re.match("\d{2}", str(count))
                    if NR is not None:
                        title1 = title_cut[0][0] + str(count) + ".*" + title_cut[0][-1]
                        self.range_parse(link, title1)
                    else:
                        title1 = title_cut[0][0] + "0" + str(count) + ".*" + title_cut[0][-1]
                        self.range_parse(link, title1)
            except ValueError as e:
                logging.error("Fehler in Variablenwert: %s" %e.message)
        else:
            self.parse_download(link, title)

    def range_parse(self,series_url, search_title):
        req_page = getURL(series_url)
        soup = BeautifulSoup(req_page)

        try:
            titles = soup.findAll(text=re.compile(search_title))
            for title in titles:
                # Prüfe Quellart
                validsource = re.search(self.seasonssource,title.lower())
                if validsource:
                    for title in titles:
                       if self.quality !='480p' and self.quality in title:
                           self.parse_download(series_url, title)
                       if self.quality =='480p' and not (('.720p.' in title) or ('.1080p.' in title)):
                           self.parse_download(series_url, title)
                else:
                    self.log_debug(title + " - Release hat falsche Quelle")
        except re.error as e:
            self.log_error('Konstantenfehler: %s' % e)


    def parse_download(self,series_url, search_title):
        req_page = getURL(series_url)
        soup = BeautifulSoup(req_page)
        
        # Da das beautifulsoup per Regex sucht, darf der Suchstring keine Klammern enthalten. Ersetze diese entsprechend durch Wildcard
        escape_brackets = search_title.replace("(", ".*").replace(")", ".*").replace("+", ".*")

        title = soup.find(text=re.compile(escape_brackets))
        if title:
            url_hosters = re.findall('<a href="([^"\'>]*)".+?\| (.+?)<', str(title.parent.parent))
            for url_hoster in url_hosters:
                if self.hoster.lower() in url_hoster[1]:
                    self.send_package(title, url_hoster[0])

    def send_package(self, title, link):
        try:
            storage = self.db.retrieve(title)
            if storage == 'downloaded':
                self.log_debug(title + " - Release ignoriert (bereits gefunden)")
            else:
                self.log_info('[Staffel] - ' + title + ' - [<a href="' + link + '" target="_blank">Link</a>]')
                self.db.store(title, 'downloaded')
                common.write_crawljob_file(title, title, link,
                                    jdownloaderpath + "/folderwatch", "RSScrawler") and self.added_items.append(title.encode("utf-8"))
        except Exception as e:
            self.log_debug("Fehler bei Datenbankzugriff: %s, Grund: %s" % (e,title))

class YouTube():
    _INTERNAL_NAME='YT'

    def __init__(self):
        self.config = RssConfig(self._INTERNAL_NAME)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.db = RssDb(os.path.join(os.path.dirname(sys.argv[0]), "Einstellungen/Downloads/YT_Downloads.db"))
        self.youtube = os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/YT_Channels.txt')
        self._periodical_active = False
        self.periodical = RepeatableTimer(
            int(rsscrawler.get('interval')) * 60,
            self.periodical_task
        )
        self.dictWithNamesAndLinks = {}

    def activate(self):
        self._periodical_active = True
        self.periodical.start()
        return self

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

    # Periodische Aufgabe
    @_restart_timer
    def periodical_task(self):
        # Abbruch, bei Deaktivierter Suche
        if not self.config.get('youtube'):
            self.log_debug("Suche für YouTube deaktiviert!")
            return
        # Leere/Definiere interne URL/Text-Arrays
        channels = []
        text = []
        videos = []
        key = ""
        download_link = ""
        # Definiere interne Suchliste auf Basis der YT_Channels Liste
        self.allInfos = self.readInput(self.youtube)

        # Suche nach jeder Zeile in der internen Suchliste
        for xline in self.allInfos:
            # Wenn die Zeile nicht leer ist bzw. keine Raute (für Kommentare) enthält:
            if len(xline) > 0 and not xline.startswith("#"):
                if xline.startswith("XXXXXXXXXX") or self.config.get("youtube") == False:
                    self.log_debug("Liste enthält Platzhalter. Stoppe Suche für YouTube!")
                    return
                # Generiere aus diesen Suchurl-kompatiblen String als Seitenaufruf (entspricht einer Suche auf MB nach dem entsprechenden Titel) eine Liste an Suchanfragen-URLs (Anzahl entspricht Einträgen der internen Suchliste)
                channels.append(xline)

        for channel in channels:
            htmlParser = "lxml"
            url = 'https://www.youtube.com/user/' + channel + '/videos'
            urlc = 'https://www.youtube.com/channel/' + channel + '/videos'
            cnotfound = False
            try:
                html = urllib2.urlopen(url)
            except urllib2.HTTPError, e:
                try:
                    html = urllib2.urlopen(urlc)
                except urllib2.HTTPError, e:
                    cnotfound = True
                if cnotfound:
                    self.log_debug("YouTube-Kanal: " + channel + " nicht gefunden!")
                    return
                    
            response = html.read()
            soup = BeautifulSoup(response)
            links = soup.findAll('a', attrs={'class':'yt-uix-sessionlink'})
            
            # Maximal hinzuzufügende Links
            maxvideos = int(self.config.get("maxvideos"))
            if maxvideos < 1:
                self.log_debug("Anzahl zu suchender YouTube-Videos (" + str(maxvideos) +") zu gering. Suche stattdessen 1 Video!")
                maxvideos = 1
            elif maxvideos > 50:
                self.log_debug("Anzahl zu suchender YouTube-Videos (" + str(maxvideos) +") zu hoch. Suche stattdessen maximal 50 Videos!")
                maxvideos = 50

            for link in links[:maxvideos]:
                link = link.get("href")
                # Füge nur Links, die tatsächlich auf Videos verweisen(also lang genug sind), hinzu
                if len(link) > 10:
                    videos.append([link, channel])

        for video in videos:
            channel = video[1]
            video = video[0]
            key = video.replace("/watch?v=", "")
            download_link = 'https://www.youtube.com' + video
            title = ""
            # Füge Videos nur hinzu, wenn überhaupt ein Link gefunden wurde (erzeuge hierfür einen crawljob)
            if not download_link == None:
                # Wenn das Video als bereits hinzugefügt in der Datenbank vermerkt wurde, logge dies und breche ab
                if self.db.retrieve(key) == 'added':
                    self.log_debug("[%s] - YouTube-Video ignoriert (bereits gefunden)" % key)
                # Ansonsten speichere das Video als hinzugefügt in der Datenbank
                else:
                    # Finde den Titel des Video
                    video_title = re.findall(re.compile('<title>(.+?)</title>'),urllib2.urlopen(download_link).read())[0].replace(" - YouTube", "").decode("utf-8").replace("&amp;", "&").replace("&gt;", ">").replace("&lt;", "<").replace('&quot;', '"').replace("&#39;", "'")
                    
                    # Ignoriere Titel entsprechend der Einstellungen
                    ignore = "|".join(["%s" % p for p in self.config.get("ignore").lower().split(',')]) if not self.config.get("ignore") == "" else "^unmatchable$"
                    ignorevideo = re.search(ignore,video_title.lower())
                    if ignorevideo:
                        self.log_debug(video_title + " (" + channel + ") " + "[" + key + "] - YouTube-Video ignoriert (basierend auf ignore-Einstellung)")
                        continue
                    
                    # Logge gefundenes Video auch im RSScrawler (Konsole/Logdatei)
                    self.log_info('[YouTube] - ' + video_title + ' (' + channel + ') - [<a href="' + download_link + '" target="_blank">Link</a>]')
                    # Schreibe Crawljob  
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
                    
        # Wenn zuvor ein key dem Text hinzugefügt wurde (also ein Video gefunden wurde):
        if len(text) > 0 and len(rsscrawler.get("pushbulletapi")) > 0:
            # Löse Pushbullet-Benachrichtigung aus
            common.Pushbullet(rsscrawler.get("pushbulletapi"),text)

## Hauptsektion
if __name__ == "__main__":
    arguments = docopt(__doc__, version='RSScrawler')

    # Deaktiviere requests Log
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # Lege loglevel über Startparameter fest
    logging.basicConfig(
        filename=os.path.join(os.path.dirname(sys.argv[0]), 'RSScrawler.log'), format=time.strftime("%Y-%m-%d %H:%M:%S") + ' - %(message)s', level=logging.__dict__[arguments['--log-level']] if arguments['--log-level'] in logging.__dict__ else logging.INFO
    )
    console = logging.StreamHandler()
    console.setLevel(logging.__dict__[arguments['--log-level']] if arguments['--log-level'] in logging.__dict__ else logging.INFO)
    formatter = logging.Formatter(time.strftime("%Y-%m-%d %H:%M:%S") + ' - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    #  Zeige Programminformationen in der Konsole
    print("┌────────────────────────────────────────────────────────┐")
    print("  Programminfo:    RSScrawler " + version + " von RiX")
    print("  Projektseite:    https://github.com/rix1337/RSScrawler")
    print("└────────────────────────────────────────────────────────┘")
    
    # Dateien prüfen und erstellen
    files.startup()
            
    # Setze relativen Dateinamen der Einstellungsdatei    
    einstellungen = os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/RSScrawler.ini')
    # Erstelle RSScrawler.ini, wenn nicht bereits vorhanden
    # Wenn jd-pfad Startparameter nicht existiert, erstelle ini ohne diesen Parameter
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
    # Ansonsten erstelle ini mit angegebenem Pfad
    else:
        if not os.path.exists(einstellungen):
            # Prüfe weiterhin ob Port angegeben wurde
            if arguments['--port']:
                files.einsteller(einstellungen, version, arguments['--jd-pfad'], arguments['--port'])
            # Wenn nicht, vergebe nur Pfadangabe
            else:
                files.einsteller(einstellungen, version, arguments['--jd-pfad'], "9090")
            print('Der Ordner "Einstellungen" wurde erstellt.')
            print('Die Einstellungen und Listen sind jetzt im Webinterface anpassbar.')
    
    # Prüfe, ob neue Einstellungen in RSScrawler vorhanden sind
    configfile = os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/RSScrawler.ini')
    if not 'port' in open(configfile).read() and not 'prefix' in open(configfile).read() :
        print "Veraltete Konfigurationsdatei erkannt. Ergänze neue Einstellungen!"
        with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/RSScrawler.ini'), 'r+') as f:
            content = f.read()
            f.seek(0)
            f.truncate()
            f.write(content.replace('[RSScrawler]\n', '[RSScrawler]\nport = 9090\nprefix =\n'))
            
    # Definiere die allgemeinen Einstellungen global
    rsscrawler = RssConfig('RSScrawler')

    # Wenn JDPFAD als Argument vergeben wurde, ignoriere Konfigurationseintrag
    if arguments['--jd-pfad']:
        jdownloaderpath = arguments['--jd-pfad']
    else:
        jdownloaderpath = rsscrawler.get("jdownloader")
    # Sperre Pfad, wenn    als Docker gestartet wurde
    if arguments['--docker']:
       jdownloaderpath = '/jd2'
    # Ersetze Backslash durch Slash (für Windows)
    jdownloaderpath = jdownloaderpath.replace("\\", "/")
    # Entferne Slash, wenn jdownloaderpath darauf endet
    jdownloaderpath = jdownloaderpath[:-1] if jdownloaderpath.endswith('/') else jdownloaderpath

    # Konsolenhinweis bei docker-Parameter
    if arguments['--docker']:
       print('Docker-Modus: JDownloader-Pfad und Port können nur per Docker-Run angepasst werden!')
       
    # Abbrechen, wenn JDownloader Pfad nicht vergeben wurde
    if jdownloaderpath == 'Muss unbedingt vergeben werden!':
        print('Der Pfad des JDownloaders muss unbedingt in der RSScrawler.ini hinterlegt werden.')
        print('Weiterhin sollten die Listen entsprechend der README.md gefüllt werden!')
        print('Beende RSScrawler...')
        sys.exit(0)
    
    # Zeige Pfad erst nach obigem Check    
    print('Nutze das "folderwatch" Unterverzeichnis von "' + jdownloaderpath + '" für Crawljobs')
        
    # Abbrechen, wenn JDownloader Pfad nicht existiert
    if not os.path.exists(jdownloaderpath):
        print('Der Pfad des JDownloaders existiert nicht.')
        print('Beende RSScrawler...')
        sys.exit(0)

    # Abbrechen, wenn folderwatch Pfad im JDownloader Pfad nicht existiert
    if not os.path.exists(jdownloaderpath + "/folderwatch"):
        print('Der Pfad des JDownloaders enthält nicht das "folderwatch" Unterverzeichnis. Sicher, dass der Pfad stimmt?')
        print('Beende RSScrawler...')
        sys.exit(0)
        
    # Lege Port und Pfad der Webanwendung entsprechend der RSScrawler.ini bzw. des Startparameters fest
    if arguments['--port']:
        port = int(arguments['--port'])
    else:
        port = port = int(rsscrawler.get("port"))
    # Sperre Port, wenn    als Docker gestartet wurde
    docker = '0'
    if arguments['--docker']:
       port = int('9090')
       docker = '1'
       
    prefix = rsscrawler.get("prefix")
    print('Der Webserver ist erreichbar unter ' + common.checkIp() +':' + str(port) + '/' + prefix)

    # Starte Webanwendung
    p = Process(target=cherry_server, args=(port, prefix, docker))
    p.start()
    files.check()

    # Diese Klassen werden periodisch ausgeführt    
    pool = [
        MB(),
        MB3d(),
        MBstaffeln(),
        MBregex(),
        SJ(),
        SJregex(),
        SJstaffeln(),
        YouTube()
    ]

    # Hinweis, wie RSScrawler beendet werden kann
    print('Drücke [Strg] + [C] zum Beenden')
    
    # Sauberes Beenden (über STRG+C) ermöglichen
    def signal_handler(signal, frame):
        list([el.periodical.cancel() for el in pool])
        print('Beende RSScrawler...')
        p.terminate()
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    # Wenn testlauf gesetzt ist, führe RSScrawler nur einmalig aus:
    for el in pool:
        # Wenn also testlauf nicht gesetzt ist, aktiviere die wiederholte Ausführung
        if not arguments['--testlauf']:
            el.activate()
        # Starte unabhängig von testlauf das Script
        el.periodical_task()

    # Pausiere das Script für die festgelegte Zeit, nachdem es ausgeführt werde (bis zur nächsten Ausführung)
    if not arguments['--testlauf']:
        try:
            while True:
                signal.pause()
        except AttributeError:
            # signal.pause() fehlt in Windows. Schlafe daher für eine Sekunde
            while True:
              time.sleep(1)
