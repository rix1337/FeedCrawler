# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import errno
import logging
import os
import sys

log_error = logging.error

def check():
    # Aktualisiere Prä-v.2.0 ini
    with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/RSScrawler.ini'), 'r+') as f:
        content = f.read()
        f.seek(0)
        f.truncate()
        f.write(content.replace(';', ','))
		
	lists_nonregex = [ "MB_3D", "MB_Filme", "MB_Staffeln", "SJ_Serien", "YT_Channels"]
	lists_regex = ["MB_Regex", "SJ_Serien_Regex"]
	
    for nrlist in lists_nonregex:
	    with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/' + nrlist + '.txt'), 'r+') as f:
                content = f.read()
                f.seek(0)
                f.truncate()

                # Verhindere Leere Listen
                if content == '':
                    content = 'XXXXXXXXXX'
                content = "".join([s for s in content.strip().splitlines(True) if s.strip()])
                f.write(content.replace('.', ' ').replace(';', ',').replace('Ä', 'Ae').replace('ä', 'ae').replace('Ö', 'Oe').replace('ö', 'oe').replace('Ü', 'Ue').replace('ü', 'ue').replace('ß', 'ss').replace('(', '').replace(')', '').replace('(', '').replace('*', '').replace('(', '').replace('|', '').replace('\\', '').replace('/', '').replace('?', '').replace('!', '').replace('  ', ' '))

    for rlist in lists_regex:
	    with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/' + rlist + '.txt'), 'r+') as f:
                content = f.read()
                f.seek(0)
                f.truncate()
                # Verhindere Leere Listen
                if content == '':
                    content = 'XXXXXXXXXX'
                content = "".join([s for s in content.strip().splitlines(True) if s.strip()])
                f.write(content)
                
# Versuche Ordner anzulegen um Ordner zu erstellen (mit Fehlererkennung)
def _mkdir_p(path):
    # Versuche Ordner anzulegen:
    try:
        os.makedirs(path)
    except OSError as e:
        # Kein Fehler, wenn Pfad bereits existiert
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        # Ansonsten zeige Fehler in Konsole
        else:
            logging.error("Kann Pfad nicht anlegen: %s" % path)
            raise
        
def startup():
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
    lists = [ "MB_3D", "MB_Filme", "MB_Staffeln", "SJ_Serien", "MB_Regex", "SJ_Serien_Regex", "YT_Channels"]
    for l in lists:
        if not os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/' + l + '.txt')):
            open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/MB_Filme.txt'), "a").close()
            placeholder = open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/' + l + '.txt'), 'w')
            placeholder.write('XXXXXXXXXX')
            placeholder.close()
    # Cherrypy Konfigurationsdatei
    if not os.path.exists(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Web')):
        _mkdir_p(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Web'))
    if not os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Web/cherry.conf')):
        open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Web/cherry.conf'), "a").close()
        cherryconf = open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Web/cherry.conf'), 'w')
    # Platzhalterzeile weicht bei Regex Liste ab
        cherryconf.write("[global]\nserver.socket_host: '0.0.0.0'\nlog.screen: False\n\nlog.access_file: ''\nlog.error_file: ''\n\n[/]\ntools.gzip.on: True")
        cherryconf.close()

def einsteller(einstellungen, version, jdpfad, port):
    open(einstellungen, "a").close()
    einsteller = open(einstellungen, 'w')
    einsteller.write('# RSScrawler.ini (Stand: RSScrawler ' + version + ')\n\n[RSScrawler]\njdownloader = ' + jdpfad + '\nport = ' + port + '\nprefix = \ninterval = 10\nhoster = Uploaded\npushbulletapi = \n\n[MB]\nquality = 720p\nignore = cam,subbed,xvid,dvdr,untouched,remux,pal,md,ac3md,mic,xxx,hou,h-ou\nhistorical = True\nregex = False\ncutoff = False\ncrawl3d = False\nenforcedl = False\ncrawlseasons = True\nseasonsquality = 720p\nseasonpacks = False\nseasonssource = bluray\n\n[SJ]\nquality = 720p\nrejectlist = XviD,Subbed,HDTV\nregex = False\n\n[YT]\nyoutube = False\nmaxvideos = 10\nignore = \n\n[Crawljobs]\nautostart = True\nsubdir = True')
    einsteller.close()
