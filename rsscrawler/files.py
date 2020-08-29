# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import os
import sys

from rsscrawler.myjd import get_device
from rsscrawler.myjd import get_if_one_device
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
        print(u"Wo sollen Einstellungen und Logs abgelegt werden? Leer lassen, um den aktuellen Pfad zu nutzen.")
        configpath = input("Pfad angeben:")
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


def hostnames():
    return


def myjd_input(configfile, port, user, password, device):
    if user and password and device:
        print(u"Zugangsdaten aus den Parametern übernommen.")
    elif user and password and not device:
        device = get_if_one_device(user, password)
        if device:
            print(u"Gerätename " + device + " automatisch ermittelt.")
    else:
        print(u"Bitte die Zugangsdaten für My JDownloader angeben:")
        user = input("Nutzername/Email:")
        password = input("Passwort:")
        device = get_if_one_device(user, password)
        if device:
            print(u"Gerätename " + device + " automatisch ermittelt.")
        else:
            device = input(u"Gerätename:")
    if not port:
        port = '9090'

    sections = ['RSScrawler', 'MB', 'SJ', 'DD', 'Notifications', 'Crawljobs']
    for section in sections:
        RssConfig(section, configfile)
    if port:
        RssConfig('RSScrawler', configfile).save("port", port)

    RssConfig('RSScrawler', configfile).save("myjd_user", user)
    RssConfig('RSScrawler', configfile).save("myjd_pass", password)
    RssConfig('RSScrawler', configfile).save("myjd_device", device)
    device = get_device(configfile)
    if device:
        return device
    else:
        return False
