# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import errno
import logging
import os
import sys
import rssdb
from rssconfig import RssConfig


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


def startup(jdownloader, port):
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

    sections = ['RSScrawler', 'MB', 'SJ', 'DD',
                'YT', 'Notifications', 'Crawljobs']
    for section in sections:
        if section == "RSScrawler":
            RssConfig(section, jdownloader, port)
        else:
            RssConfig(section)
