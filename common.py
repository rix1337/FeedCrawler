# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337
# Enthält Code von:
# https://github.com/dmitryint (im Auftrag von https://github.com/rix1337)
# https://github.com/bharnett/Infringer/blob/master/LinkRetrieve.py

import base64
import files
import logging
import os
import re
import socket
import sys
import urllib
import urllib2
from rssconfig import RssConfig

try:
    import simplejson as json
except ImportError:
    import json

log_info = logging.info
log_error = logging.error
log_debug = logging.debug

def get_first(iterable):
    return iterable and list(iterable[:1]).pop() or None
    
def write_crawljob_file(package_name, folder_name, link_text, crawljob_dir, subdir):
    # Crawljobs enden auf .crawljob
    crawljob_file = crawljob_dir + '/%s.crawljob' % unicode(
        # Windows-inkompatible Sonderzeichen/Leerzeichen werden ersetzt
        re.sub('[^\w\s\.-]', '', package_name.replace(' ', '')).strip().lower()
    )
    # Versuche .crawljob zu schreiben
    crawljobs = RssConfig('Crawljobs')
    autostart = crawljobs.get("autostart")
    usesubdir = crawljobs.get("subdir")
    if usesubdir == "False":
      subdir = ""
    if autostart == "True":
        autostart = "TRUE"
    else:
        autostart = "FALSE"
    try:
        # Öffne Crawljob mit Schreibzugriff
        file = open(crawljob_file, 'w')
        # Optionen für Paketeigenschaften im JDownloader:
        # Paket ist aktiviert
        file.write('enabled=TRUE\n')
        # Download startet automatisch
        file.write('autoStart=' + autostart + '\n')
        # Passwörter hinzufügen
        file.write('extractPasswords=["' + "bW92aWUtYmxvZy5vcmc=".decode('base64') + '","' + "c2VyaWVuanVua2llcy5vcmc=".decode('base64') + '"]\n')
        file.write('downloadPassword=' + "c2VyaWVuanVua2llcy5vcmc=".decode('base64') + '\n')
        # Archive automatisch entpacken
        file.write('extractAfterDownload=TRUE\n')
        # Erzwinge automatischen Start
        file.write('forcedStart=' + autostart + '\n')
        # Bestätige Fragen des JDownloaders automatisch
        file.write('autoConfirm=' + autostart + '\n')
        # Unterverzeichnis des Downloads ist folder_name & subdir wird wenn es nicht leer ist mit angegeben. Subdir hilft bei der Automatisierung (bspw. über Filebot).
        if not subdir == "":
            file.write('downloadFolder=' + subdir + "/" + '%s\n' % folder_name)
            # Niedrige Priorität für erzwungene zweisprachige Downloads
            if subdir == "RSScrawler/Remux":
                file.write('priority=Lower\n')
        else:
            file.write('downloadFolder=' + '%s\n' % folder_name)
        # Name des Pakets im JDownloader ist package_name (ohne Leerzeichen!)
        file.write('packageName=%s\n' % package_name.replace(' ', ''))
        # Nutze ersten Eintrag (lt. Code einzigen!) des link_text Arrays als Downloadlink
        file.write('text=%s\n' % link_text)
        # Beende Schreibvorgang
        file.close()
        # Bestätige erfolgreichen Schreibvorgang
        return True
    # Bei Fehlern:
    except UnicodeEncodeError as e:
        # Beende Schreibvorgang
        file.close()
        # Erläutere den Fehler im Log inkl. Dateipfad des Crawljobs und Fehlerbericht
        logging.error("Beim Schreibversuch des Crawljobs: %s FEHLER: %s" %(crawljob_file, e.message))
        # Wenn hiernach ein fehlerhafter Crawljob zurück bleibt
        if os.path.isfile(crawljob_file):
            # Logge das weitere Vorgehen
            logging.info("Entferne defekten Crawljob: %s" % crawljob_file)
            # Entferne den Crawljob
            os.remove(crawljob_file)
        # Vermerke fehlgeschlagenen Schreibvorgang
        return False

def checkIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 0))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP
                
def entfernen(retailtitel, identifier):
    # Funktion um Listen einheitlich groß zu schreiben (vorraussetzung für einheitliches CutOff)
    def capitalize(line):
        return ' '.join(s[0].upper() + s[1:] for s in line.split(' '))
    log_info = logging.info
    log_debug = logging.debug
    # Retail Titel auf Listenformat kürzen und Zusatztags entfernen
    simplified = retailtitel.replace(".", " ")
    # Abgefahrener RegEx-String, der Retail-Releases identifiziert
    retail = re.sub(r'(|.UNRATED|Uncut|UNCUT)(|.Directors.Cut|.DC|.EXTENDED|.THEATRICAL)(|.3D|.3D.HSBS|.3D.HOU|.HSBS|.HOU).\d{4}(|.UNRATED|Uncut|UNCUT)(|.Directors.Cut|.DC|.EXTENDED|.THEATRICAL)(|.3D|.3D.HSBS|.3D.HOU|.HSBS|.HOU).(German|GERMAN)(|.AC3|.DTS)(|.DL)(|.AC3|.DTS).(1080|720)p.(HDDVD|BluRay)(|.AVC|.AVC.REMUX|.x264)(|.REPACK|.RERiP)-.*', "", simplified)
    # Obiger RegEx-String, der nicht das Jahr entfernt, falls in der Liste eine Jahreszahl angegeben wurde
    retailyear = re.sub(r'(|.UNRATED|Uncut|UNCUT)(|.Directors.Cut|.DC|.EXTENDED|.THEATRICAL)(|.3D|.3D.HSBS|.3D.HOU|.HSBS|.HOU).(German|GERMAN)(|.AC3|.DTS)(|.DL)(|.AC3|.DTS).(1080|720)p.(HDDVD|BluRay)(|.AVC|.AVC.REMUX|.x264)(|.REPACK|.RERiP)-.*', "", simplified)
    if identifier == '2':
        liste = "MB_3D"
    else:
        liste = "MB_Filme"
    with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/' + liste + '.txt'), 'r') as l:
        content = l.read()
        l.close()
    # Inhalt der liste Schreiben, wobei der Retail-Titel entfernt wird    
    with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/' + liste + '.txt'), 'w') as w:
        w.write(content.replace(retailyear, "").replace(retail, "").replace(retailyear.lower(), "").replace(retail.lower(), "").replace(retailyear.upper(), "").replace(retail.upper(), "").replace(capitalize(retailyear), "").replace(capitalize(retail), ""))
    # Leerzeilen und Eingabefehler entfernen
    files.check()
    log_debug(retail + " durch Cutoff aus " + liste + " entfernt.")
    log_info(retail + (" [3D]" if identifier == "2" else "") + " [Retail]")

def cutoff(key, identifier):
    retailfinder = re.search("(|.UNRATED|Uncut|UNCUT)(|.Directors.Cut|.DC|.EXTENDED|.THEATRICAL)(|.3D|.3D.HSBS|.3D.HOU|.HSBS|.HOU).(German|GERMAN)(|.AC3|.DTS)(|.DL)(|.AC3|.DTS).(1080|720)p.(HDDVD|BluRay)(|.AVC|.AVC.REMUX|.x264)(|.REPACK|.RERiP)-.*",key)
    if retailfinder:
      entfernen(key, identifier)

def Pushbullet(api='', msg=''):
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
        
def load(dockerglobal):
    main = RssConfig('RSScrawler')
    jdownloader = main.get("jdownloader")
    port = main.get("port")
    prefix = main.get("prefix")
    interval = main.get("interval")
    hoster = main.get("hoster")
    pushbulletapi = main.get("pushbulletapi")
    # MB-Bereich
    mb = RssConfig('MB')
    mbquality = mb.get("quality")
    ignore = mb.get("ignore")
    historical = str(mb.get("historical"))
    mbregex = str(mb.get("regex"))
    cutoff = str(mb.get("cutoff"))
    crawl3d = str(mb.get("crawl3d"))
    enforcedl = str(mb.get("enforcedl"))
    crawlseasons = str(mb.get("crawlseasons"))
    seasonsquality = mb.get("seasonsquality")
    seasonpacks = str(mb.get("seasonpacks"))
    seasonssource = mb.get("seasonssource")
    # SJ-Bereich
    sj = RssConfig('SJ')
    sjquality = sj.get("quality")
    rejectlist = sj.get("rejectlist")
    sjregex = str(sj.get("regex"))
    # YT-Bereich
    yt = RssConfig('YT')
    youtube = str(yt.get("youtube"))
    maxvideos = str(yt.get("maxvideos"))
    ytignore = str(yt.get("ignore"))
    # Wandle Werte für HTML um
    if hoster == 'Share-Online':
      hosterso = ' selected'
      hosterul = ''
    else:
      hosterso = ''
      hosterul = ' selected'
    if mbquality == '1080p':
      mbq1080 = ' selected'
      mbq720 = ''
      mbq480 = ''
    if mbquality == '720p':
      mbq1080 = ''
      mbq720 = ' selected'
      mbq480 = ''
    if mbquality == '480p':
      mbq1080 = ''
      mbq720 = ''
      mbq480 = ' selected'
    if seasonsquality == '1080p':
      msq1080 = ' selected'
      msq720 = ''
      msq480 = ''
    if seasonsquality == '720p':
      msq1080 = ''
      msq720 = ' selected'
      msq480 = ''
    if seasonsquality == '480p':
      msq1080 = ''
      msq720 = ''
      msq480 = ' selected'
    if sjquality == '1080p':
      sjq1080 = ' selected'
      sjq720 = ''
      sjq480 = ''
    if sjquality == '720p':
      sjq1080 = ''
      sjq720 = ' selected'
      sjq480 = ''
    if sjquality == '480p':
      sjq1080 = ''
      sjq720 = ''
      sjq480 = ' selected'
    if historical == 'True':
      historicaltrue = ' selected'
      historicalfalse = ''
    else:
      historicaltrue = ''
      historicalfalse = ' selected'
    if mbregex == 'True':
      mbregextrue = ' selected'
      mbregexfalse = ''
      mrdiv = "block"
    else:
      mbregextrue = ''
      mbregexfalse = ' selected'
      mrdiv = "none"
    if cutoff == 'True':
      cutofftrue = ' selected'
      cutofffalse = ''
    else:
      cutofftrue = ''
      cutofffalse = ' selected'
    if crawl3d == 'True':
      crawl3dtrue = ' selected'
      crawl3dfalse = ''
      tddiv = "block"
    else:
      crawl3dtrue = ''
      crawl3dfalse = ' selected'
      tddiv = "none"
    if enforcedl == 'True':
      enforcedltrue = ' selected'
      enforcedlfalse = ''
    else:
      enforcedltrue = ''
      enforcedlfalse = ' selected'
    if crawlseasons == 'True':
      crawlseasonstrue = ' selected'
      crawlseasonsfalse = ''
      ssdiv = "block"
    else:
      crawlseasonstrue = ''
      crawlseasonsfalse = ' selected'
      ssdiv = "none"
    if seasonpacks == 'True':
      spacktrue = ' selected'
      spackfalse = ''
    else:
      spacktrue = ''
      spackfalse = ' selected'
    if seasonssource == "hdtv|hdtvrip|tvrip":
      shdtv = ' selected'
      shdtvweb = ''
      sweb = ''
      sbluray = ''
      swebbluray = ''
      shdtvwebbluray = ''
    elif seasonssource == "web-dl|webrip|webhd":
      shdtv = ''
      shdtvweb = ''
      sweb = ' selected'
      sbluray = ''
      swebbluray = ''
      shdtvwebbluray = ''
    elif seasonssource == "hdtv|hdtvrip|tvrip|web-dl|webrip|webhd":
      shdtv = ''
      shdtvweb = ' selected'
      sweb = ''
      sbluray = ''
      swebbluray = ''
      shdtvwebbluray = ''
    elif seasonssource == "bluray|bd|bdrip":
      shdtv = ''
      shdtvweb = ''
      sweb = ''
      sbluray = ' selected'
      swebbluray = ''
      shdtvwebbluray = ''
    elif seasonssource == "web-dl|webrip|webhd|bluray|bd|bdrip":
      shdtv = ''
      shdtvweb = ''
      sweb = ''
      sbluray = ''
      swebbluray = ' selected'
      shdtvwebbluray = ''
    elif seasonssource == "hdtv|hdtvrip|tvrip|web-dl|webrip|webhd|bluray|bd|bdrip":
      shdtv = ''
      shdtvweb = ''
      sweb = ''
      sbluray = ''
      swebbluray = ''
      shdtvwebbluray = ' selected'
    else:
      shdtv = ''
      shdtvweb = ''
      sweb = ''
      sbluray = ''
      swebbluray = ''
      shdtvwebbluray = ' selected'
    if sjregex == 'True':
      sjregextrue = ' selected'
      sjregexfalse = ''
      srdiv = "block"
    else:
      sjregextrue = ''
      sjregexfalse = ' selected'
      srdiv = "none"
    # Erkenne Prefix
    if prefix:
      prefix = '/' + prefix
    # Erkenne Docker Umgebung
    if dockerglobal == '1':
      dockerblocker = ' readonly="readonly"'
      dockerhint = 'Docker-Modus: Kann nur per Docker-Run angepasst werden! '
    else:
      dockerblocker = ''
      dockerhint = ''
    if youtube == 'True':
      youtubetrue = ' selected'
      youtubefalse = ''
      ytdiv = "block"
    else:
      youtubetrue = ''
      youtubefalse = ' selected'
      ytdiv = "none"
    return (jdownloader, port, prefix, interval, hoster, pushbulletapi, mbquality, ignore, historical, mbregex, cutoff, crawl3d, enforcedl, crawlseasons, seasonsquality, seasonssource, sjquality, rejectlist, sjregex, hosterso, hosterul, mbq1080, mbq720, mbq480, msq1080, msq720, msq480, sjq1080, sjq720, sjq480, historicaltrue, historicalfalse, mbregextrue, mbregexfalse, mrdiv, cutofftrue, cutofffalse, crawl3dtrue, crawl3dfalse, tddiv, enforcedltrue, enforcedlfalse, crawlseasonstrue, crawlseasonsfalse, ssdiv, sjregextrue, sjregexfalse, srdiv, dockerblocker, ytdiv, youtubetrue, youtubefalse, spacktrue, spackfalse, shdtv, shdtvweb, sweb, sbluray, swebbluray, shdtvwebbluray, maxvideos, ytignore, dockerhint)
