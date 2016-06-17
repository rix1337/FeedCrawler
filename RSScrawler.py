# -*- coding: utf-8 -*-
# RSScrawler - Version 1.6.4
# Projekt von https://github.com/rix1337
# Enthaltener Code
# https://github.com/dmitryint (im Auftrag von https://github.com/rix1337)
# https://github.com/zapp-brannigan/own-pyload-plugins/blob/master/hooks/MovieblogFeed.py
# https://github.com/Gutz-Pilz/pyLoad-stuff/blob/master/SJ.py
# https://github.com/bharnett/Infringer/blob/master/LinkRetrieve.py
# Beschreibung:
# RSScrawler durchsucht MB/SJ nach in .txt Listen hinterlegten Titeln und reicht diese im .crawljob Format an JDownloader weiter.

# Startparameter/Hilfetext fuer docopt (nicht veraendern!)
"""RSScrawler.

Usage:
  RSScrawler.py [--testlauf]
                [--jd-pfad=<JDPATH>]
                [--log-level=<LOGLEVEL>]

Options:
  --testlauf                Einmalige Ausfuehrung von RSScrawler
  --jd-pfad=<JDPFAD>        Legt den Pfad von JDownloader vorab fest (nuetzlich bei headless-Systemen), diese Option darf keine Leerzeichen enthalten
  --log-level=<LOGLEVEL>    Legt fest, wie genau geloggt wird (CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET )
"""

# Globale Variablen
version = "v.1.6.4"
placeholder_filme = False
placeholder_staffeln = False
placeholder_serien = False
placeholder_regex = False

# Externe Importe
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
import pycurl
import time
import sys
import signal
import logging
import os
import errno

# Interne Importe
from rssconfig import RssConfig
from rssdb import RssDb
from timer import RepeatableTimer
import common

# Importiere SimpleJson oder Json (nach Verfuegbarkeit)
try:
    import simplejson as json
except ImportError:
    import json

# Schreibe Crawljob fuer JDownloader (inkl. Parameter aus MB/SJ Funktionen)
def write_crawljob_file(package_name, folder_name, link_text, crawljob_dir, subdir):
    # Crawljobs enden auf .crawljob
    crawljob_file = crawljob_dir + '/%s.crawljob' % unicode(
        # Windows-inkompatible Sonderzeichen/Leerzeichen werden ersetzt
        re.sub('[^\w\s\.-]', '', package_name.replace(' ', '')).strip().lower()
    )
    # Versuche .crawljob zu schreiben
    try:
        # Oeffne Crawljob mit Schreibzugriff
        file = open(crawljob_file, 'w')
        # Optionen fuer Paketeigenschaften im JDownloader:
        # Paket ist aktiviert
        file.write('enabled=TRUE\n')
        # Download startet automatisch
        file.write('autoStart=TRUE\n')
        # Archive automatisch entpacken
        file.write('extractAfterDownload=TRUE\n')
        # Erzwinge automatischen Start
        file.write('forcedStart=TRUE\n')
        # Bestaetige Fragen des JDownloaders automatisch
        file.write('autoConfirm=TRUE\n')
        # Unterverzeichnis des Downloads ist folder_name & subdir wird wenn es nicht leer ist mit angegeben. Subdir hilft bei der Automatisierung (bspw. ueber Filebot).
        if not subdir == "":
            file.write('downloadFolder=' + subdir + "/" + '%s\n' % folder_name)
        else:
            file.write('downloadFolder=' + '%s\n' % folder_name)
        # Name des Pakets im JDownloader ist package_name (ohne Leerzeichen!)
        file.write('packageName=%s\n' % package_name.replace(' ', ''))
        # Nutze ersten Eintrag (lt. Code einzigen!) des link_text Arrays als Downloadlink
        file.write('text=%s\n' % link_text[0])
        # Beende Schreibvorgang
        file.close()
        # Bestaetige erfolgreichen Schreibvorgang
        return True
    # Bei Fehlern:
    except UnicodeEncodeError as e:
        # Beende Schreibvorgang
        file.close()
        # Erlaeutere den Fehler im Log inkl. Dateipfad des Crawljobs und Fehlerbericht
        logging.error("While writing in the file: %s the error occurred: %s" %(crawljob_file, e.message))
        # Wenn hiernach ein fehlerhafter Crawljob zurueck bleibt
        if os.path.isfile(crawljob_file):
            # Logge das weitere Vorgehen
            logging.info("Removing broken file: %s" % crawljob_file)
            # Entferne den Crawljob
            os.remove(crawljob_file)
        # Vermerke fehlgeschlagenen Schreibvorgang
        return False

# MovieBlog
def notifyPushbulletMB(apikey,text):
    # Wenn kein API-Key vergeben wurde:
    if apikey == "0" or apikey == "":
        # Beende vorzeitig
        return
    # Definiere Typ (note), Titel (RSScrawler), und Textinhalt (den Releasetitel) der Pushbullet-Nachricht
    postData = '{"type":"note", "title":"RSScrawler:", "body":"%s"}' %" ### ".join(text).encode("utf-8")
    # Vorgang erfolgt ueber pycurl an die pushbuan die pushbullet API
    c = pycurl.Curl()
    c.setopt(pycurl.WRITEFUNCTION, lambda x: None)
    c.setopt(pycurl.URL, 'https://api.pushbullet.com/v2/pushes')
    c.setopt(pycurl.HTTPHEADER, ['Content-Type: application/json'])
    c.setopt(pycurl.USERPWD, apikey.encode('utf-8'))
    c.setopt(pycurl.POST, 1)
    c.setopt(pycurl.POSTFIELDS, postData)
    c.perform()

# Versuche Ordner anzulegen um Ordner zu erstellen (mit Fehlererkennung)
def _mkdir_p(path):
    # Versuche Ordner anzulegen:
    try:
        os.makedirs(path)
    except OSError as e:
        # Kein Fehler, wenn Pfad bereits existiert
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        # Ansonsten logge den Fehler
        else:
            logging.error("Kann Pfad nicht anlegen: %s" % path)
            raise

# Funktion fuer das wiederholte Ausfuehren des Scriptes
def _restart_timer(func):
    def wrapper(self):
        func(self)
        # Wenn testlauf inaktiv ist wurde dies aktiviert. Der folgende Code fuehrt das Script in Intervallen aus
        if self._periodical_active:
            self.periodical.cancel()
            self.periodical.start()
    return wrapper

class MB():
    FEED_URL = "http://www.movie-blog.org/feed/"
    SUBSTITUTE = "[&#\s/]"
    _INTERNAL_NAME='MB'

    def __init__(self):
        self.config = RssConfig(self._INTERNAL_NAME)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.db = RssDb(os.path.join(os.path.dirname(sys.argv[0]), "Einstellungen/Downloads/MB_Downloads.db"))
        self.filme = os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/MB_Filme.txt')
        self.staffeln = os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/MB_Staffeln.txt')
        self._hosters_pattern = rsscrawler.get('hoster').replace(';','|')
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
            placeholder.write('RSSCRAWLER VON RIX - Ein Titel Pro Zeile - BEACHTE DIE README.md')
            placeholder.close()
        try:
            f = codecs.open(file, "rb")
            return f.read().splitlines()
        except:
            self.log_error("Liste nicht gefunden!")

    def getPatterns(self, patterns, quality, rg, sf):
        # Importiere globale Parameter (sollten beide Falsch sein)
        global placeholder_filme
        global placeholder_staffeln
        # Wenn Liste exakt die Platzhalterzeile enthaelt:
        if patterns == ["RSSCRAWLER VON RIX - Ein Titel Pro Zeile - BEACHTE DIE README.md"]:
            # Wenn keine Information zur Quellart weitergegeben wurde (gilt nur bei Staffeln, Standard ist: BluRay):
            if sf == None:
                # Logge vorhandenen Platzhalter, der in der Filme-Liste stehen muss (da keine Quellart angegeben)
                self.log_debug("Liste enthaelt Platzhalter. Stoppe Suche fuer MB_Filme!")
                # Setze globale Variable auf wahr, um in der MB-Klasse die Suche abbrechen zu koennen
                placeholder_filme = True
            else:
                # Logge vorhandenen Platzhalter, der in der Staffeln-Liste stehen muss (da Quellart angegeben)
                self.log_debug("Liste enthaelt Platzhalter. Stoppe Suche fuer MB_Staffeln!")
                # Setze globale Variable auf wahr, um in der MB-Klasse die Suche abbrechen zu koennen
                placeholder_staffeln = True
        # Ansonsten gib die Zeilen einzeln als Zeilen in patters zurueck
        return {line: (quality, rg, sf) for line in patterns}

    def searchLinks(self, feed):
        ignore = "|".join(["\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if not self.config.get("ignore") == "" else "^unmatchable$"
        
        for key in self.allInfos:
            s = re.sub(self.SUBSTITUTE,".",key).lower()
            for post in feed.entries:
                """Suche nach Titel"""
                found = re.search(s,post.title.lower())
                if found:
                    """Pruefe ob Release ignoriert werden soll (basierend auf ignore-Einstellung)"""
                    found = re.search(ignore,post.title.lower())
                    if found:
                        # Wenn zu ignorierender Eintrag, logge diesen
                        self.log_debug("%s - Release ignoriert (basierend auf ignore-Einstellung)" %post.title)
                        continue
                    """Suche nach Qualitaet"""
                    ss = self.allInfos[key][0].lower()

                    # Crawl3d Funktion gilt wenn 3D im Titel enthalten ist
                    if '.3d.' in post.title.lower():
                        # Wenn crawl3d aktiv ist und 1080p/1080i zusaetzlich zu 3D im Titel steht:
                        if self.config.get('crawl3d') and ("1080p" in post.title.lower() or "1080i" in post.title.lower()):
                            # Release gilt als gefunden
                            found = True
                        # Ansonsten ignoriere das Release mit 3D im Titel (weil es bspw. in 720p released wurde)
                        else:
                            continue
                    # Funktion, die Listeneintraege wie folgt erwartet: Titel,Aufloesung,Gruppe
                    else:
                        if ss == "480p":
                            if "720p" in post.title.lower() or "1080p" in post.title.lower() or "1080i" in post.title.lower():
                                continue
                            found = True
                        else:
                            found = re.search(ss,post.title.lower())
                    if found:
                        # Funktion, die Listeneintraege wie folgt erwartet: Titel,Aufloesung,Gruppe
                        """Suche nach Release-Gruppe"""
                        sss = "[\.-]+"+self.allInfos[key][1].lower()
                        found = re.search(sss,post.title.lower())

                        if self.allInfos[key][2]:
                            # Wenn alles True, dann found = True (also gilt Release nur als gefunden, wenn alle Parameter wahr sind)
                            found = all([word in post.title.lower() for word in self.allInfos[key][2]])

                        if found:
                            # Check, ob das Release zu einer Serie gehoert
                            try:
                                episode = re.search(r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*',post.title.lower()).group(1)
                                if "repack" in post.title.lower():
                                    episode = episode + "-repack"
                                self.log_debug("Serie entdeckt. Kuerze Titel: [%s]" %episode)
                                yield (episode, [post.link], key)
                            except:
                                # Gebe den Link (der alle obigen Checks bestandend hat) weiter
                                yield (post.title, [post.link], key)


    def download_dl(self, title):
        # Schreibe den nicht-zweisprachigen Titel fuer die folgende Suche um
        text = []
        # Dies generiert den in die Suche einfuegbaren String (+ statt Leerzeichen)
        search_title = title.replace(".German.720p.", ".German.DL.1080p.").replace(".German.DTS.720p.", ".German.DTS.DL.1080p.").replace(".German.AC3.720p.", ".German.AC3.DL.1080p.").replace(".German.AC3LD.720p.", ".German.AC3LD.DL.1080p.").replace(".German.AC3.Dubbed.720p.", ".German.AC3.Dubbed.DL.1080p.").split('.x264-', 1)[0].split('.h264-', 1)[0].replace(".", " ").replace(" ", "+")
        search_url = "http://www.movie-blog.org/search/" + search_title + "/feed/rss2/"
        # Nach diesem String (also Releasetitel) wird schlussendlich in den Suchergebnissen gesucht (. statt Leerzeichen)
        feedsearch_title = title.replace(".German.720p.", ".German.DL.1080p.").replace(".German.DTS.720p.", ".German.DTS.DL.1080p.").replace(".German.AC3.720p.", ".German.AC3.DL.1080p.").replace(".German.AC3LD.720p.", ".German.AC3LD.DL.1080p.").replace(".German.AC3.Dubbed.720p.", ".German.AC3.Dubbed.DL.1080p.").split('.x264-', 1)[0].split('.h264-', 1)[0]
        if not '.dl.' in feedsearch_title.lower():
            self.log_debug("%s - Release ignoriert (nicht zweisprachig, da wahrscheinlich nicht Retail)" %feedsearch_title)
            return
        
        # Suche nach title im Ergebnisfeed der obigen Suche (nicht nach dem fuer die suche genutzten search_title)
        for (key, value, pattern) in self.dl_search(feedparser.parse(search_url), feedsearch_title, title):
            # Wenn das Release als bereits hinzugefuegt in der Datenbank vermerkt wurde, logge dies und breche ab
            if self.db.retrieve(key) == 'added' or self.db.retrieve(key) == 'dl':
                self.log_debug("%s - zweisprachiges Release ignoriert (bereits hinzugefuegt)" % key)
            # Ansonsten speichere das Release als hinzugefuegt in der Datenbank
            else:
                self.db.store(
                    key,
                    # Vermerke zweisprachiges Release entsprechend in der Datenbank
                    'dl' if self.config.get('enforcedl') and '.dl.' in key.lower() else 'added',
                    pattern
                    )
                
                # Logge gefundenes Release auch im RSScrawler (Konsole/Logdatei)
                self.log_info(key + " - zweisprachiges Release hinzugefuegt")
                # Pruefe ob bereits fuer die aktuelle Version ein Readme im JDownloader hinterlegt/heruntergeladen wurde:
                if not os.path.exists(jdownloaderpath + '/folderwatch/rsscrawler.' + version + '.readme-rix.crawljob'):
                    if not os.path.exists(jdownloaderpath + '/folderwatch/added/rsscrawler.' + version + '.readme-rix.crawljob.1'):
                        # Erzeuge Crawljob um Readme ueber JDownloader zur Verfuegung zu stellen (einmaliger Vorgang pro Version, solange .crawljob nicht geloescht wird). Diese Zeilen duerfen nicht entfernt werden!
                        write_crawljob_file("rsscrawler." + version + ".readme-rix", "RSSCrawler." + version + ".README-RiX", ["https://github.com/rix1337/RSScrawler/archive/master.zip"], jdownloaderpath + "/folderwatch", "")
                # Nimm nur den ersten validen Downloadlink der auf der Unterseite eines jeden Releases gefunden wurde
                download_link = [common.get_first(self._get_download_links(value[0], self._hosters_pattern))]
                # Fuege Release nur hinzu, wenn ueberhaupt ein Link gefunden wurde (erzeuge hierfuer einen crawljob)
                if any(download_link):
                    write_crawljob_file(
                        key,
                        key,
                        download_link,
                        jdownloaderpath + "/folderwatch",
                        "RSScrawler/Remux"
                    ) and text.append(key)
            # Wenn zuvor ein key dem Text hinzugefuegt wurde (also ein Release gefunden wurde):
            if len(text) > 0:
                # Loese Pushbullet-Benachrichtigung aus
                notifyPushbulletMB(rsscrawler.get("pushbulletapi"),text)
                return True
                
    def dl_search(self, feed, title, notdl_title):
        ignore = "|".join(["\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if not self.config.get("ignore") == "" else "^unmatchable$"
            
        s = re.sub(self.SUBSTITUTE,".",title).lower()
        for post in feed.entries:
            """Suche nach Titel"""
            found = re.search(s,post.title.lower())
            if found:
                """Pruefe ob Release ignoriert werden soll (basierend auf ignore-Einstellung)"""
                found = re.search(ignore,post.title.lower())
                if found:
                    # Wenn zu ignorierender Eintrag, logge diesen
                    self.log_debug("%s - zweisprachiges Release ignoriert (basierend auf ignore-Einstellung)" %post.title)
                    continue
                yield (post.title, [post.link], title)
                                

    # Suchfunktion fuer Downloadlinks (auf der zuvor gefundenen Unterseite):
    def _get_download_links(self, url, hosters_pattern=None):
        # Definiere die zu durchsuchende Baumstruktur (auf Basis der Unterseite)
        tree = html.fromstring(requests.get(url).content)
        # Genaue Anweisung, wo die Links zu finden sind (Unterhalb des Download:/Mirror # Textes)
        xpath = '//*[@id="content"]/span/div/div[2]//strong[contains(text(),"Download:") or contains(text(),"Mirror #")]/following-sibling::a[1]'
        # Jeder link wird zurueck gegeben, wenn kein Wunschhoster festgelegt wurde. Ansonsten werden nur Links zum Wunschhoster weitergegeben.
        return [common.get_first(link.xpath('./@href')) for link in tree.xpath(xpath) if hosters_pattern is None or re.search(hosters_pattern, link.text, flags=re.IGNORECASE)]

    # Periodische Aufgabe
    @_restart_timer
    def periodical_task(self):
        # Leere/Definiere interne URL/Text-Arrays
        urls = []
        text = []
            
        # Definiere interne Suchliste auf Basis der MB_Serien, MB_Staffeln (und notdl) Listen
        self.allInfos = dict(
            # Fuege der Suche saemtliche Titel aus der MB_Filme Liste hinzu
            set({key: value for (key, value) in self.getPatterns(
                    self.readInput(self.filme),
                    self.config.get('quality'),
                    '.*',
                    None
                ).items()}.items()
            ) |
            # Fuege weiterhin alle Titel aus der MB_Staffeln Liste (inklusive der Qulitaets-/Quell-Einstellungen) hinzu
            set(self.getPatterns(
                    self.readInput(self.staffeln),
                    self.config.get('seasonsquality'),
                    '.*',
                    ('.complete.','.' + self.config.get('seasonssource') + '.')
            ).items() if self.config.get('crawlseasons') else [])
        )
        
        # Stoppe Suche wenn Platzhalter aktiv
        if placeholder_filme and placeholder_staffeln:
            return

        # Wenn historical aktiv ist nutzt RSScrawler die Suchfunktion von MB, statt nur den (zeitlich begrenzten) Feed zu nutzen. Dies dauert etwas laenger, durchsucht aber den kompletten MB!
        if self.config.get("historical"):
            # Suche nach jeder Zeile in der internen Suchliste
            for xline in self.allInfos.keys():
                # Wenn die Zeile nicht leer ist bzw. keine Raute (fuer Kommentare) enthaelt:
                if len(xline) > 0 and not xline.startswith("#"):
                    # Entferne Zusatzinfos der obsoleten Funktion, die Listeneintraege wie folgt erwartet: Titel,Aufloesung,Gruppe
                    # Die Suche Benoetigt nur den Titel vor dem ersten Komma. Ersetze Weiterhin Punkte durch Leerzeichen und diese fuer die Suche durch ein +
                    xn = xline.split(",")[0].replace(".", " ").replace(" ", "+")
                    # Generiere aus diesen Suchurl-kompatiblen String als Seitenaufruf (entspricht einer Suche auf MB nach dem entsprechenden Titel) eine Liste an Suchanfragen-URLs (Anzahl entspricht Eintraegen der internen Suchliste)
                    urls.append('http://www.movie-blog.org/search/%s/feed/rss2/' %xn)
        # Nutze ansonsten den Feed (und dessen Inhalt) als Grundlage zur Suche
        else:
            # Hierfuer wird nur eine einzelne URL (die oben vergebene) benoetigt
            urls.append(self.FEED_URL)

        # Suchfunktion fuer valide Releases (und deren Downloadlinks) wird fuer jede URL durchgefuehrt:
        for url in urls:
            # Fuehre fuer jeden Eintrag auf der URL eine Suche nach Releases durch:
            for (key, value, pattern) in self.searchLinks(feedparser.parse(url)):
                # Suche nach zweisprachigem Release, sollte das aktuelle nicht zweisprachig sein:
                if self.config.get('enforcedl') and '.dl.' not in key.lower():
                    # Wenn die Suche fuer zweisprachige Releases nichts findet (wird zugleich ausgefuehrt)
                    if not self.download_dl(key):
                        # Logge nicht gefundenes zweisprachiges Release
                        self.log_debug("%s - Kein zweisprachiges Release gefunden" %key)
                            
                # Wenn das Release als bereits hinzugefuegt in der Datenbank vermerkt wurde, logge dies und breche ab
                if self.db.retrieve(key) == 'added' or self.db.retrieve(key) == 'notdl':
                    self.log_debug("%s - Release ignoriert (bereits hinzugefuegt)" % key)
                # Ansonsten speichere das Release als hinzugefuegt in der Datenbank
                else:
                    self.db.store(
                        key,
                        # Vermerke Releases, die nicht zweisprachig sind in der Datenbank (falls enforcedl aktiv ist). Speichere jedes gefundene Release
                        'notdl' if self.config.get('enforcedl') and '.dl.' not in key.lower() else 'added',
                        pattern
                    )
                    
                    # Logge gefundenes Release auch im RSScrawler (Konsole/Logdatei)
                    self.log_info(key + " - Release hinzugefuegt")
                    # Pruefe ob bereits fuer die aktuelle Version ein Readme im JDownloader hinterlegt/heruntergeladen wurde:
                    if not os.path.exists(jdownloaderpath + '/folderwatch/rsscrawler.' + version + '.readme-rix.crawljob'):
                        if not os.path.exists(jdownloaderpath + '/folderwatch/added/rsscrawler.' + version + '.readme-rix.crawljob.1'):
                            # Erzeuge Crawljob um Readme ueber JDownloader zur Verfuegung zu stellen (einmaliger Vorgang pro Version, solange .crawljob nicht geloescht wird). Diese Zeilen duerfen nicht entfernt werden!
                            write_crawljob_file("rsscrawler." + version + ".readme-rix", "RSSCrawler." + version + ".README-RiX", ["https://github.com/rix1337/RSScrawler/archive/master.zip"], jdownloaderpath + "/folderwatch", "")
                    # Nimm nur den ersten validen Downloadlink der auf der Unterseite eines jeden Releases gefunden wurde
                    download_link = [common.get_first(self._get_download_links(value[0], self._hosters_pattern))]
                    # Fuege Release nur hinzu, wenn ueberhaupt ein Link gefunden wurde (erzeuge hierfuer einen crawljob)
                    if any(download_link):
                        write_crawljob_file(
                            key,
                            key,
                            download_link,
                            jdownloaderpath + "/folderwatch",
                            "RSScrawler"
                        ) and text.append(key)
        # Wenn zuvor ein key dem Text hinzugefuegt wurde (also ein Release gefunden wurde):
        if len(text) > 0:
            # Loese Pushbullet-Benachrichtigung aus
            notifyPushbulletMB(rsscrawler.get("pushbulletapi"),text)

# Serienjunkies
def getSeriesList(file):
    global placeholder_serien
    if not os.path.isfile(file):
        open(file, "a").close()
        placeholder = open(file, 'w')
        placeholder.write('RSSCRAWLER VON RIX - Ein Titel Pro Zeile - BEACHTE DIE README.md')
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
        if titles[0] == "RSSCRAWLER.VON.RIX.-.Ein.Titel.Pro.Zeile.-.BEACHTE.DIE.README.md":
            logging.debug("Liste enthaelt Platzhalter. Stoppe Suche fuer SJ_Serien!")
            placeholder_serien = True
        return titles
    except UnicodeError:
        logging.error("ANGEHALTEN, ungueltiges Zeichen in SJ_Serien Liste!")
    except IOError:
        logging.error("ANGEHALTEN, SJ_Serien nicht gefunden!")
    except Exception, e:
        logging.error("Unbekannter Fehler: %s" %e)

def getRegexSeriesList(file):
    global placeholder_regex
    if not os.path.isfile(file):
        open(file, "a").close()
        placeholder = open(file, 'w')
        placeholder.write('RSSCRAWLER VON RIX - Ein Titel Pro Zeile - BEACHTE DAS REGEX FORMAT UND DIE README.md')
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
        if titles[0] == "RSSCRAWLER.VON.RIX.-.Ein.Titel.Pro.Zeile.-.BEACHTE.DAS.REGEX.FORMAT.UND.DIE.README.md":
            logging.debug("Liste enthaelt Platzhalter. Stoppe Suche fuer SJ_Serien_Regex!")
            placeholder_regex = True
        return titles
    except UnicodeError:
        logging.error("ANGEHALTEN, ungueltiges Zeichen in SJ_Serien_Regex Liste!")
    except IOError:
        logging.error("ANGEHALTEN, SJ_Serien_Regex nicht gefunden!")
    except Exception, e:
        logging.error("Unbekannter Fehler: %s" %e)

def notifyPushbulletSJ(api='', msg=''):
    data = urllib.urlencode({
        'type': 'note',
        'title': 'RSScrawler:',
        'body': "\n\n".join(msg)
    })
    auth = base64.encodestring('%s:' %api).replace('\n', '')
    try:
        req = urllib2.Request('https://api.pushbullet.com/v2/pushes', data)
        req.add_header('Authorization', 'Basic %s' % auth)
        response = urllib2.urlopen(req)
    except urllib2.HTTPError:
        logging.debug('FEHLER - Konnte Pushbullet API nicht erreichen')
        return False
    res = json.load(response)
    if res['sender_name']:
        logging.debug('Pushbullet Erfolgreich versendet')
    else:
        logging.debug('FEHLER - Konnte nicht an Pushbullet Senden')


def getURL(url):
    try:
        req = urllib2.Request(
            url,
            None,
            {'User-agent' : 'Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5'}
        )
        return urllib2.urlopen(req).read()
    except urllib2.HTTPError as e:
        logging.debug('Bei der HTTP-Anfrage ist ein Fehler Aufgetreten: Fehler: %s Grund: %s' % (e.code, e.reason))
        return ''
    except urllib2.URLError as e:
        logging.debug('Bei der HTTP-Anfrage ist ein Fehler Aufgetreten: Grund: %s' %  e.reason)
        return ''

class SJ():
    MIN_CHECK_INTERVAL = 2 * 60 # Minimales Intervall: 2 Minuten
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

    @_restart_timer
    def periodical_task(self):
        feed = feedparser.parse('http://serienjunkies.org/xml/feeds/episoden.xml')
        self.pattern = "|".join(getSeriesList(os.path.join(os.path.dirname(sys.argv[0]), "Einstellungen/Listen/SJ_Serien.txt"))).lower()
        # Stoppe Suche wenn Platzhalter aktiv
        if placeholder_serien:
            return
        reject = self.config.get("rejectlist").replace(";","|").lower() if len(self.config.get("rejectlist")) > 0 else "^unmatchable$"
        self.quality = self.config.get("quality")
        self.hoster = rsscrawler.get("hoster")
        # Ersetze die Hosterbezeichnung fuer weitere Verwendung im Script
        if self.hoster == "Uploaded":
            # Auf SJ wird Uploaded als Teil der url gefuehrt: ul
            self.hoster = "ul"
        if self.hoster == "Share-Online":
            # Auf SJ wird Uploaded als Teil der url gefuehrt: so
            self.hoster = "so"
        # Lege Array als Typ fuer die added_items fest (Liste bereits hinzugefuegter Releases)
        self.added_items = []

        for post in feed.entries:
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
            notifyPushbulletSJ(rsscrawler.get("pushbulletapi"),self.added_items) if len(self.added_items) > 0 else True

    def range_checkr(self, link, title):
        pattern = re.match(".*S\d{2}E\d{2}-\w?\d{2}.*", title)
        if pattern is not None:
            range0 = re.sub(r".*S\d{2}E(\d{2}-\w?\d{2}).*",r"\1", title).replace("E","")
            number1 = re.sub(r"(\d{2})-\d{2}",r"\1", range0)
            number2 = re.sub(r"\d{2}-(\d{2})",r"\1", range0)
            title_cut = re.findall(r"(.*S\d{2}E)(\d{2}-\w?\d{2})(.*)",title)
            try:
                for count in range(int(number1),(int(number2)+1)):
                    NR = re.match("d\{2}", str(count))
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
        escape_brackets = search_title.replace("(", ".*").replace(")", ".*")

        title = soup.find(text=re.compile(escape_brackets))
        if title:
            items = []
            links = title.parent.parent.findAll('a')
            for link in links:
                url = link['href']
                pattern = '.*%s_.*' % self.hoster
                if re.match(pattern, url):
                    items.append(url)
            self.send_package(title,items) if len(items) > 0 else True

    def send_package(self, title, link):
        try:
            storage = self.db.retrieve(title)
        except Exception as e:
            self.log_debug("Fehler bei Datenbankzugriff: %s, Grund: %s" % (e,title))
        if storage == 'downloaded':
            self.log_debug(title + " - Release ignoriert (bereits hinzugefuegt)")
        else:
            self.log_info(title + " - Release hinzugefuegt")
            self.db.store(title, 'downloaded')
            if not os.path.exists(jdownloaderpath + '/folderwatch/rsscrawler.' + version + '.readme-rix.crawljob'):
                if not os.path.exists(jdownloaderpath + '/folderwatch/added/rsscrawler.' + version + '.readme-rix.crawljob.1'):
                    write_crawljob_file("rsscrawler." + version + ".readme-rix", "RSSCrawler." + version + ".README-RiX", ["https://github.com/rix1337/RSScrawler/archive/master.zip"], jdownloaderpath + "/folderwatch", "")
            write_crawljob_file(title, title, link,
                                jdownloaderpath + "/folderwatch", "RSScrawler") and self.added_items.append(title.encode("utf-8"))

class SJregex():
    MIN_CHECK_INTERVAL = 2 * 60 # Minimales Intervall: 2 Minuten
    _INTERNAL_NAME = 'SJ'

    def __init__(self):
        self.config = RssConfig(self._INTERNAL_NAME)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        if self.config.get("regex"):
            self.db = RssDb(os.path.join(os.path.dirname(sys.argv[0]), "Einstellungen/Downloads/SJ_Downloads.db"))
            self._periodical_active = False
            self.periodical = RepeatableTimer(
                int(rsscrawler.get('interval')) * 60,
                self.periodical_task
            )

    def activate(self):
        self._periodical_active = True
        self.periodical.start()

    @_restart_timer
    def periodical_task(self):
        feed = feedparser.parse('http://serienjunkies.org/xml/feeds/episoden.xml')
        self.pattern = "|".join(getRegexSeriesList(os.path.join(os.path.dirname(sys.argv[0]), "Einstellungen/Listen/SJ_Serien_Regex.txt"))).lower()
        # Stoppe Suche wenn Platzhalter aktiv
        if placeholder_regex:
            return
        reject = self.config.get("rejectlist").replace(";","|").lower() if len(self.config.get("rejectlist")) > 0 else "^unmatchable$"
        self.quality = self.config.get("quality")
        self.hoster = rsscrawler.get("hoster")
        # Ersetze die Hosterbezeichnung fuer weitere Verwendung im Script
        if self.hoster == "Uploaded":
            # Auf SJ wird Uploaded als Teil der url gefuehrt: ul
            self.hoster = "ul"
        if self.hoster == "Share-Online":
            # Auf SJ wird Uploaded als Teil der url gefuehrt: so
            self.hoster = "so"
        # Lege Array als Typ fuer die added_items fest (Liste bereits hinzugefuegter Releases)
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
                        self.log_debug(title + " - Release durch Regex hinzugefuegt (trotz rejectlist-Einstellung)")
                    title = re.sub('\[.*\] ', '', post.title)
                    self.range_checkr(link,title)

            else:
                continue
            
        if len(rsscrawler.get('pushbulletapi')) > 2:
            notifyPushbulletSJ(rsscrawler.get("pushbulletapi"),self.added_items) if len(self.added_items) > 0 else True

    def range_checkr(self, link, title):
        pattern = re.match(".*S\d{2}E\d{2}-\w?\d{2}.*", title)
        if pattern is not None:
            range0 = re.sub(r".*S\d{2}E(\d{2}-\w?\d{2}).*",r"\1", title).replace("E","")
            number1 = re.sub(r"(\d{2})-\d{2}",r"\1", range0)
            number2 = re.sub(r"\d{2}-(\d{2})",r"\1", range0)
            title_cut = re.findall(r"(.*S\d{2}E)(\d{2}-\w?\d{2})(.*)",title)
            try:
                for count in range(int(number1),(int(number2)+1)):
                    NR = re.match("d\{2}", str(count))
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
        escape_brackets = search_title.replace("(", ".*").replace(")", ".*")
        
        title = soup.find(text=re.compile(escape_brackets))
        if title:
            items = []
            links = title.parent.parent.findAll('a')
            for link in links:
                url = link['href']
                pattern = '.*%s_.*' % self.hoster
                if re.match(pattern, url):
                    items.append(url)
            self.send_package(title,items) if len(items) > 0 else True

    def send_package(self, title, link):
        try:
            storage = self.db.retrieve(title)
        except Exception as e:
            self.log_debug("Fehler bei Datenbankzugriff: %s, Grund: %s" % (e,title))
        if storage == 'downloaded':
            self.log_debug(title + " - Release ignoriert (bereits hinzugefuegt)")
        else:
            self.log_info(title + " - Release hinzugefuegt")
            self.db.store(title, 'downloaded')
            if not os.path.exists(jdownloaderpath + '/folderwatch/rsscrawler.' + version + '.readme-rix.crawljob'):
                if not os.path.exists(jdownloaderpath + '/folderwatch/added/rsscrawler.' + version + '.readme-rix.crawljob.1'):
                    write_crawljob_file("rsscrawler." + version + ".readme-rix", "RSSCrawler." + version + ".README-RiX", ["https://github.com/rix1337/RSScrawler/archive/master.zip"], jdownloaderpath + "/folderwatch", "")
            write_crawljob_file(title, title, link,
                                jdownloaderpath + "/folderwatch", "RSScrawler") and self.added_items.append(title.encode("utf-8"))

## Hauptsektion
if __name__ == "__main__":
    arguments = docopt(__doc__, version='RSScrawler')

    # Deaktiviere HTTP requests im log
    urllib3_logger = logging.getLogger('urllib3')
    urllib3_logger.setLevel(logging.CRITICAL)
    
    # Lege loglevel ueber Startparameter fest
    logging.basicConfig(
        filename=os.path.join(os.path.dirname(sys.argv[0]), 'RSScrawler.log'), format='RSScrawler: %(asctime)s - %(message)s', level=logging.__dict__[arguments['--log-level']] if arguments['--log-level'] in logging.__dict__ else logging.INFO
    )
    console = logging.StreamHandler()
    console.setLevel(logging.__dict__[arguments['--log-level']] if arguments['--log-level'] in logging.__dict__ else logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    #  Zeige Programminformationen in der Konsole
    print("RSScrawler " + version + " von RiX")
    print("Originalseite: https://github.com/rix1337/RSScrawler/")
    
    # Erstelle fehlenden Einstellungen Ordner
    if not os.path.exists(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen')):
        _mkdir_p(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen'))
    # Erstelle fehlenden Downloads Ordner
    if not os.path.exists(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Downloads')):
        _mkdir_p(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Downloads'))
    # Erstelle fehlenden Listen Ordner
    if not os.path.exists(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen')):
        _mkdir_p(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen'))
    # Erstelle fehlenden Listen mit Platzhaltertexten (diese werden in separaten Funktionen abgefragt!)
    if not os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/MB_Filme.txt')):
        open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/MB_Filme.txt'), "a").close()
        placeholder = open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/MB_Filme.txt'), 'w')
        placeholder.write('RSSCRAWLER VON RIX - Ein Titel Pro Zeile - BEACHTE DIE README.md')
        placeholder.close()
    if not os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/MB_Staffeln.txt')):
        open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/MB_Staffeln.txt'), "a").close()
        placeholder = open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/MB_Staffeln.txt'), 'w')
        placeholder.write('RSSCRAWLER VON RIX - Ein Titel Pro Zeile - BEACHTE DIE README.md')
        placeholder.close()
    if not os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/SJ_Serien.txt')):
        open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/SJ_Serien.txt'), "a").close()
        placeholder = open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/SJ_Serien.txt'), 'w')
        placeholder.write('RSSCRAWLER VON RIX - Ein Titel Pro Zeile - BEACHTE DIE README.md')
        placeholder.close()
    if not os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/SJ_Serien_Regex.txt')):
        open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/SJ_Serien_Regex.txt'), "a").close()
        placeholder = open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/SJ_Serien_Regex.txt'), 'w')
    # Platzhalterzeile weicht bei Regex Liste ab
        placeholder.write('RSSCRAWLER VON RIX - Ein Titel Pro Zeile - BEACHTE DAS REGEX FORMAT UND DIE README.md')
        placeholder.close()
            
    # Setze relativen Dateinamen der Einstellungsdatei    
    einstellungen = os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/RSScrawler.ini')
    # Erstelle RSScrawler.ini, wenn nicht bereits vorhanden
    # Wenn jd-pfad Startparameter existiert, erstelle ini mit diesem Parameter
    if not arguments['--jd-pfad']:
        if not os.path.exists(einstellungen):
            open(einstellungen, "a").close()
            einsteller = open(einstellungen, 'w')
            einsteller.write('# Hier werden saemtliche Einstellungen von RSScrawler hinterlegt\n# Dieses Script funktioniert nur sinnvoll, wenn Ordnerueberwachung im JDownloader aktiviert ist.\n# Es muss weiterhin unten der richtige JDownloader Pfad gesetzt werden!\n# Zur automatischen Captcha-Loesung empfehle ich:\n# https://www.9kw.eu/register_87296.html\n# Des weiteren empfehle ich einen Premium-Account bei Uploaded:\n# http://ul.to/ref/14406819\n\n# Diese allgemeinen Einstellungen muessen korrekt sein:\n[RSScrawler]\n# Dieser Pfad muss das exakte Verzeichnis des JDownloaders sein, sonst funktioniert das Script nicht!\njdownloader = Muss unbedingt vergeben werden!\n# Das Suchintervall in Minuten sollte nicht zu niedrig angesetzt werden um keinen Ban zu riskieren\ninterval = 10\n# Um ueber hinzugefuegte Releases informiert zu werden hier den Pushbullet API-Key eintragen\npushbulletapi = \n# Hier den gewuenschten Hoster eintragen (Uploaded oder Share-Online)\nhoster = Uploaded\n\n# Dieser Bereich ist fuer die Suche auf Movie-Blog.org zustaendig:\n[MB]\n# Die Qualitaet, nach der Gesucht wird (1080p, 720p oder 480p)\nquality = 720p\n# Releases mit diesen Begriffen werden nicht hinzugefuegt (durch Kommas getrennt)\nignore = cam,subbed,xvid,dvdr,untouched,remux,pal,md,ac3md,mic,xxx,hou,h-ou\n# Wenn aktiviert wird die MB-Suchfunktion genutzt (langsamer), da der Feed nur wenige Stunden abbildet\nhistorical = True\n# Wenn aktiviert sucht das Script nach 3D Releases (in 1080p), unabhaengig von der oben gesetzten Qualitaet\ncrawl3d = False\n# Wenn aktiviert sucht das Script zu jedem nicht-zweisprachigen Release (kein DL-Tag im Titel) ein passendes Release\n# in 1080p mit DL Tag. Findet das Script kein Release wird dies im Log vermerkt. Bei der naechsten Ausfuehrung versucht\n# das Script dann erneut ein passendes Release zu finden. Diese Funktion ist nuetzlich um (durch spaeteres Remuxen) eine\n# zweisprachige Bibliothek in 720p zu halten.\nenforcedl = False\n# Komplette Staffeln von Serien landen zuverlaessiger auf MB als auf SJ. Diese Option erlaubt die entsprechende Suche\ncrawlseasons = True\n# Die Qualitaet, nach der Staffeln gesucht werden (1080p, 720p oder 480p)\nseasonsquality = 720p\n# Der Staffel-Releasetyp nach dem gesucht wird\nseasonssource = bluray\n\n# Dieser Bereich ist fuer die Suche auf Serienjunkies.org zustaendig:\n[SJ]\n# Die Qualitaet, nach der Gesucht wird (1080p, 720p oder 480p)\nquality = 720p\n# Releases mit diesen Begriffen werden nicht hinzugefuegt (durch Semikola getrennt)\nrejectlist = XviD;Subbed;HDTV\n# Wenn aktiviert werden in einer zweiten Suchdatei Serien nach Regex-Regeln gesucht\nregex = False\n\n# Die Listen (MB_Filme, MB_Serien, SJ_Serien, SJ_Serien_Regex:\n# 1. MB_Filme enthaelt pro Zeile den Titel eines Films (Film Titel), um auf MB nach Filmen zu suchen\n# 2. MB_Serien enthaelt pro Zeile den Titel einer Serie (Serien Titel), um auf MB nach kompletten Staffeln zu suchen\n# 3. SJ_Serien enthaelt pro Zeile den Titel einer Serie (Serien Titel), um auf SJ nach Serien zu suchen\n# 4. SJ_Serien_Regex enthaelt pro Zeile den Titel einer Serie in einem speziellen Format, wobei die Filter ignoriert werden:\n#    DEUTSCH.*Serien.Titel.*.S01.*.720p.*-GROUP sucht nach Releases der Gruppe GROUP von Staffel 1 der Serien Titel in 720p auf Deutsch\n#    Serien.Titel.* sucht nach allen Releases von Serien Titel (nuetzlich, wenn man sonst HDTV aussortiert)\n#    Serien.Titel.*.DL.*.720p.* sucht nach zweisprachigen Releases in 720p von Serien Titel\n#    ENGLISCH.*Serien.Titel.*.1080p.* sucht nach englischen Releases in Full-HD von Serien Titel')
            einsteller.close()
            print('Die Einstellungsdatei wurde erstellt. Der Pfad des JDownloaders muss jetzt unbedingt in der RSScrawler.ini hinterlegt werden.')
            print('Weiterhin sollten die Listen entsprechend der README.md gefuellt werden!')
            # Warte 10 Sekunden, damit Windows-Nutzer die Warnung lesen koennen
            time.sleep(10)
            print('Viel Spass! Beende RSScrawler!')
            sys.exit(0)
    # Ansonsten erstelle ini ohne vergebenen JDownloader Pfad
    else:
        if not os.path.exists(einstellungen):
            open(einstellungen, "a").close()
            einsteller = open(einstellungen, 'w')
            einsteller.write('# Hier werden saemtliche Einstellungen von RSScrawler hinterlegt\n# Dieses Script funktioniert nur sinnvoll, wenn Folder Watch im JDownloader aktiviert ist.\n# Es muss weiterhin unten der richtige JDownloader Pfad gesetzt werden!\n# Zur automatischen Captcha-Loesung empfehle ich:\n# https://www.9kw.eu/register_87296.html\n# Des weiteren empfehle ich einen Premium-Account bei Uploaded:\n# http://ul.to/ref/14406819\n\n# Diese allgemeinen Einstellungen muessen korrekt sein:\n[RSScrawler]\n# Dieser Pfad muss das exakte Verzeichnis des JDownloaders sein, sonst funktioniert das Script nicht!\njdownloader = ' + arguments['--jd-pfad'] + '\n# Das Suchintervall in Minuten sollte nicht zu niedrig angesetzt werden um keinen Ban zu riskieren\ninterval = 10\n# Um ueber hinzugefuegte Releases informiert zu werden hier den Pushbullet API-Key eintragen\npushbulletapi = \n# Hier den gewuenschten Hoster eintragen (Uploaded oder Share-Online)\nhoster = Uploaded\n\n# Dieser Bereich ist fuer die Suche auf Movie-Blog.org zustaendig:\n[MB]\n# Die Qualitaet, nach der Gesucht wird (1080p, 720p oder 480p)\nquality = 720p\n# Releases mit diesen Begriffen werden nicht hinzugefuegt (durch Kommas getrennt)\nignore = cam,subbed,xvid,dvdr,untouched,remux,pal,md,ac3md,mic,xxx,hou,h-ou\n# Wenn aktiviert wird die MB-Suchfunktion genutzt (langsamer), da der Feed nur wenige Stunden abbildet\nhistorical = True\n# Wenn aktiviert sucht das Script nach 3D Releases (in 1080p), unabhaengig von der oben gesetzten Qualitaet\ncrawl3d = False\n# Wenn aktiviert sucht das Script zu jedem nicht-zweisprachigen Release (kein DL-Tag im Titel) ein passendes Release\n# in 1080p mit DL Tag. Findet das Script kein Release wird dies im Log vermerkt. Bei der naechsten Ausfuehrung versucht\n# das Script dann erneut ein passendes Release zu finden. Diese Funktion ist nuetzlich um (durch spaeteres Remuxen) eine\n# zweisprachige Bibliothek in 720p zu halten.\nenforcedl = False\n# Komplette Staffeln von Serien landen zuverlaessiger auf MB als auf SJ. Diese Option erlaubt die entsprechende Suche\ncrawlseasons = True\n# Die Qualitaet, nach der Staffeln gesucht werden (1080p, 720p oder 480p)\nseasonsquality = 720p\n# Der Staffel-Releasetyp nach dem gesucht wird\nseasonssource = bluray\n\n# Dieser Bereich ist fuer die Suche auf Serienjunkies.org zustaendig:\n[SJ]\n# Die Qualitaet, nach der Gesucht wird (1080p, 720p oder 480p)\nquality = 720p\n# Releases mit diesen Begriffen werden nicht hinzugefuegt (durch Semikola getrennt)\nrejectlist = XviD;Subbed;HDTV\n# Wenn aktiviert werden in einer zweiten Suchdatei Serien nach Regex-Regeln gesucht\nregex = False\n\n# Die Listen (MB_Filme, MB_Serien, SJ_Serien, SJ_Serien_Regex:\n# 1. MB_Filme enthaelt pro Zeile den Titel eines Films (Film Titel), um auf MB nach Filmen zu suchen\n# 2. MB_Serien enthaelt pro Zeile den Titel einer Serie (Serien Titel), um auf MB nach kompletten Staffeln zu suchen\n# 3. SJ_Serien enthaelt pro Zeile den Titel einer Serie (Serien Titel), um auf SJ nach Serien zu suchen\n# 4. SJ_Serien_Regex enthaelt pro Zeile den Titel einer Serie in einem speziellen Format, wobei die Filter ignoriert werden:\n#    DEUTSCH.*Serien.Titel.*.S01.*.720p.*-GROUP sucht nach Releases der Gruppe GROUP von Staffel 1 der Serien Titel in 720p auf Deutsch\n#    Serien.Titel.* sucht nach allen Releases von Serien Titel (nuetzlich, wenn man sonst HDTV aussortiert)\n#    Serien.Titel.*.DL.*.720p.* sucht nach zweisprachigen Releases in 720p von Serien Titel\n#    ENGLISCH.*Serien.Titel.*.1080p.* sucht nach englischen Releases in Full-HD von Serien Titel')
            einsteller.close()
            print('Die Einstellungsdatei wurde erstellt. Der Pfad des JDownloaders muss jetzt unbedingt in der RSScrawler.ini hinterlegt werden.')
            print('Weiterhin sollten die Listen entsprechend der README.md gefuellt werden!')
            # Warte 10 Sekunden, damit Windows-Nutzer die Warnung lesen koennen
            time.sleep(10)
            print('Viel Spass! Beende RSScrawler!')
            sys.exit(0)
            
    # Definiere die allgemeinen Einstellungen global
    rsscrawler = RssConfig('RSScrawler')

    # Wenn JDPFAD als Argument vergeben wurde, ignoriere Konfigurationseintrag
    if arguments['--jd-pfad']:
    	jdownloaderpath = arguments['--jd-pfad']
    else:
    	jdownloaderpath = rsscrawler.get("jdownloader")
    # Ersetze Backslash durch Slash (fuer Windows)
    jdownloaderpath = jdownloaderpath.replace("\\", "/")
    # Entferne Slash, wenn jdownloaderpath darauf endet
    jdownloaderpath = jdownloaderpath[:-1] if jdownloaderpath.endswith('/') else jdownloaderpath
    print("Nutze das folderwatch Unterverzeichnis von " + jdownloaderpath + " fuer Crawljobs")

    # Abbrechen, wenn JDownloader Pfad nicht vergeben wurde
    if jdownloaderpath == 'Muss unbedingt vergeben werden!':
        print('Der Pfad des JDownloaders muss unbedingt in der RSScrawler.ini hinterlegt werden.')
        print('Weiterhin sollten die Listen entsprechend der README.md gefuellt werden!')
        # Warte 5 Sekunden, damit Windows-Nutzer die Warnung lesen koennen
        time.sleep(5)
        print('Beende RSScrawler...')
        sys.exit(0)
        
    # Abbrechen, wenn JDownloader Pfad nicht existiert
    if not os.path.exists(jdownloaderpath):
        print('Der Pfad des JDownloaders existiert nicht.')
        # Warte 5 Sekunden, damit Windows-Nutzer die Warnung lesen koennen
        time.sleep(5)
        print('Beende RSScrawler...')
        sys.exit(0)

    # Abbrechen, wenn folderwatch Pfad im JDownloader Pfad nicht existiert
    if not os.path.exists(jdownloaderpath + "/folderwatch"):
        print('Der Pfad des JDownloaders enthaelt nicht das folderwatch Verzeichnis. Sicher, dass der Pfad stimmt?')
        # Warte 5 Sekunden, damit Windows-Nutzer die Warnung lesen koennen
        time.sleep(5)
        print('Beende RSScrawler...')
        sys.exit(0)
    
    # Diese Klassen werden periodisch ausgefuehrt    
    pool = [
        MB(),
        SJ(),
        SJregex(),
    ]

    # Sauberes Beenden (ueber STRG+C) ermoeglichen
    def signal_handler(signal, frame):
        list([el.periodical.cancel() for el in pool])
        print('Beende RSScrawler...')
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    print('Druecke Strg+C zum Beenden')

    # Wenn testlauf gesetzt ist, fuehre RSScrawler einmalig aus:
    for el in pool:
        # Wenn also testlauf nicht gesetzt ist, aktiviere die wiederholte Ausfuehrung
        if not arguments['--testlauf']:
            el.activate()
        # Starte unabhaengig von testlauf das Script
        el.periodical_task()

    # Pausiere das Script fuer die festgelegte Zeit, nachdem es ausgefuehrt werde (bis zur naechsten Ausfuehrung)
    if not arguments['--testlauf']:
        try:
            while True:
                signal.pause()
        except AttributeError:
            # signal.pause() fehlt in Windows. Schlafe daher fuer eine Sekunde
            while True:
              time.sleep(1)
