# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import codecs
import logging
import os
import shutil
import sys

import rssdb
from rssconfig import RssConfig
from rssdb import ListDb


def startup(jdownloader=None, port=None):
    # Merge Pre-v.4.1.x-Databases into v.4.1.x-Database
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

    # Move Pre-v.4.2.x-Settings to Base dir
    if os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Downloads/Downloads.db')):
        os.rename(os.path.join(os.path.dirname(
            sys.argv[0]), 'Einstellungen/Downloads/Downloads.db'),
            os.path.join(os.path.dirname(sys.argv[0]), 'RSScrawler.db'))

    old_config = os.path.join(os.path.join(os.path.dirname(
        sys.argv[0]), 'Einstellungen/RSScrawler.ini'))
    if os.path.isfile(old_config):
        with open(old_config, 'r') as f:
            content = f.read().replace("hoster = Share-Online\n",
                                       "").replace("hoster = Uploaded\n", "").replace("historical = True\n",
                                                                                      "").replace(
                "historical = False\n", "")
            f.close()
        with open(old_config, 'w') as f:
            f.write(content)

        os.rename(os.path.join(os.path.dirname(
            sys.argv[0]), 'Einstellungen/RSScrawler.ini'), os.path.join(os.path.dirname(sys.argv[0]), 'RSScrawler.ini'))

    # Move Pre-v.4.2.x-Lists to Database
    lists = ["MB_3D", "MB_Filme", "MB_Staffeln", "SJ_Serien",
             "MB_Regex", "SJ_Serien_Regex", "SJ_Staffeln_Regex", "YT_Channels"]
    for l in lists:
        liste = os.path.join(os.path.dirname(
            sys.argv[0]), 'Einstellungen/Listen/' + l + '.txt')
        if os.path.isfile(liste):
            f = codecs.open(liste, "rb")
            items = f.read().replace("XXXXXXXXXX", "").splitlines()
            f.close()
            for item in items:
                ListDb(os.path.join(os.path.dirname(
                    sys.argv[0]), "RSScrawler.db"), l).store(item)

    # Delete old Settings dir
    if os.path.exists(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen')):
        shutil.rmtree(os.path.join(
            os.path.dirname(sys.argv[0]), 'Einstellungen'))

    if jdownloader or port:
        sections = ['RSScrawler', 'MB', 'SJ', 'DD',
                    'YT', 'Notifications', 'Crawljobs']
        for section in sections:
            RssConfig(section)
        if jdownloader:
            RssConfig('RSScrawler').save("jdownloader", jdownloader)
        if port:
            RssConfig('RSScrawler').save("port", port)
