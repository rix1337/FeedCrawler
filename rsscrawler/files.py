# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import os
import sys

import six

from rsscrawler.rssconfig import RssConfig


def config(configpath):
    configfile = "RSScrawler.conf"
    if configpath:
        f = open(configfile, "w")
        f.write(configpath)
        f.close()
    elif os.path.exists(configfile):
        f = open(configfile, "r")
        configpath = f.readline()
    else:
        print("Wo sollen Einstellungen und Logs abgelegt werden? Leer lassen, um den aktuellen Pfad zu nutzen.")
        configpath = six.moves.input("Pfad angeben:")
        if len(configpath) > 0:
            f = open(configfile, "w")
            f.write(configpath)
            f.close()
    if len(configpath) == 0:
        configpath = os.path.dirname(sys.argv[0])
        configpath = configpath.replace("\\", "/")
        configpath = configpath[:-1] if configpath.endswith('/') else configpath
        f = open(configfile, "w")
        f.write(configpath)
        f.close()
    configpath = configpath.replace("\\", "/")
    configpath = configpath[:-1] if configpath.endswith('/') else configpath
    if not os.path.exists(configpath):
        os.makedirs(configpath)
    return configpath


def startup(configfile, jdownloader=None, port=None):
    if jdownloader or port:
        sections = ['RSScrawler', 'MB', 'SJ', 'DD',
                    'YT', 'Notifications', 'Crawljobs']
        for section in sections:
            RssConfig(section, configfile)
        if jdownloader:
            RssConfig('RSScrawler', configfile).save("jdownloader", jdownloader)
        if port:
            RssConfig('RSScrawler', configfile).save("port", port)
