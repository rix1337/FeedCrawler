# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import errno
import logging
import os
import sys
import rssdb


def check():
    lists_nonregex = ["MB_3D", "MB_Filme",
                      "MB_Staffeln", "SJ_Serien", "YT_Channels"]
    lists_regex = ["MB_Regex", "SJ_Serien_Regex", "SJ_Staffeln_Regex"]

    for nrlist in lists_nonregex:
        with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/' + nrlist + '.txt'), 'r+') as f:
            content = f.read()
            f.seek(0)
            f.truncate()
            if content == '':
                content = 'XXXXXXXXXX'
            content = "".join(
                [s for s in content.strip().splitlines(True) if s.strip()])
            f.write(content.replace('.', ' ').replace(';', '').replace(',', '').replace('Ä', 'Ae').replace('ä', 'ae').replace('Ö', 'Oe').replace('ö', 'oe').replace('Ü', 'Ue').replace('ü', 'ue').replace(
                'ß', 'ss').replace('(', '').replace(')', '').replace('*', '').replace('|', '').replace('\\', '').replace('/', '').replace('?', '').replace('!', '').replace(':', '').replace('  ', ' '))

    for rlist in lists_regex:
        with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/' + rlist + '.txt'), 'r+') as f:
            content = f.read()
            f.seek(0)
            f.truncate()
            if content == '':
                content = 'XXXXXXXXXX'
            content = "".join(
                [s for s in content.strip().splitlines(True) if s.strip()])
            f.write(content)


def _mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            logging.error("Kann Pfad nicht anlegen: %s" % path)
            raise


def startup():
    if not os.path.exists(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen')):
        _mkdir_p(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen'))
    if not os.path.exists(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Downloads')):
        _mkdir_p(os.path.join(os.path.dirname(
            sys.argv[0]), 'Einstellungen/Downloads'))
    if not os.path.exists(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen')):
        _mkdir_p(os.path.join(os.path.dirname(
            sys.argv[0]), 'Einstellungen/Listen'))
    lists = ["MB_3D", "MB_Filme", "MB_Staffeln", "SJ_Serien",
             "MB_Regex", "SJ_Serien_Regex", "SJ_Staffeln_Regex", "YT_Channels"]
    for l in lists:
        if not os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/' + l + '.txt')):
            open(os.path.join(os.path.dirname(
                sys.argv[0]), 'Einstellungen/Listen/MB_Filme.txt'), "a").close()
            placeholder = open(os.path.join(os.path.dirname(
                sys.argv[0]), 'Einstellungen/Listen/' + l + '.txt'), 'w')
            placeholder.write('XXXXXXXXXX')
            placeholder.close()
    if os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Downloads/MB_Downloads.db')):
        if rssdb.merge_old():
            os.remove(os.path.join(os.path.dirname(
                sys.argv[0]), 'Einstellungen/Downloads/MB_Downloads.db'))
            os.remove(os.path.join(os.path.dirname(
                sys.argv[0]), 'Einstellungen/Downloads/SJ_Downloads.db'))
            os.remove(os.path.join(os.path.dirname(
                sys.argv[0]), 'Einstellungen/Downloads/YT_Downloads.db'))
        else:
            logging.error("Kann alte Downloads-Datenbanken nicht verbinden!")


def einsteller(einstellungen, version, jdpfad, port):
    open(einstellungen, "a").close()
    einsteller = open(einstellungen, 'w')
    einsteller.write('# RSScrawler.ini (Stand: RSScrawler ' + version + ')\n\n[RSScrawler]\njdownloader = ' + jdpfad + '\nport = ' + port + '\nprefix = \ninterval = 10\nenglish = False\nsurround = \nproxy = \nhoster = Share-Online\n\n[MB]\nquality = 720p\nignore = cam,subbed,xvid,dvdr,untouched,remux,avc,pal,md,ac3md,mic,xxx\nhistorical = False\nregex = False\ncutoff = False\ncrawl3d = False\ncrawl3dtype = hsbs\nenforcedl = False\ncrawlseasons = True\nseasonsquality = 720p\nseasonpacks = False\nseasonssource = web-dl.*-(tvs|4sj)|webrip.*-(tvs|4sj)|webhd.*-(tvs|4sj)|netflix.*-(tvs|4sj)|amazon.*-(tvs|4sj)|itunes.*-(tvs|4sj)|bluray|bd|bdrip\nimdbyear = 2010\nimdb = 0.0\n\n[SJ]\nquality = 720p\nrejectlist = XviD,Subbed,HDTV\nregex = False\n\n[YT]\nyoutube = False\nmaxvideos = 10\nignore = \n\n[Notifications]\npushbullet = \npushover = \nhomeassistant = \n\n[Crawljobs]\nautostart = True\nsubdir = True\n')
    einsteller.close()
