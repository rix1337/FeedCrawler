# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337

import logging
import os
import sys
from logging import handlers

from feedcrawler.config import CrawlerConfig
from feedcrawler.myjd import get_device
from feedcrawler.myjd import get_if_one_device

configfile = False
dbfile = False
log_file = False
log_file_debug = False
device = False
local_address = False
port = False
prefix = False
docker = False
logger = False


def config(configpath):
    pathfile = "FeedCrawler.conf"
    if configpath:
        f = open(pathfile, "w")
        f.write(configpath)
        f.close()
    elif os.path.exists(pathfile):
        f = open(pathfile, "r")
        configpath = f.readline()
    else:
        print(u"Wo sollen Einstellungen und Logs abgelegt werden? Leer lassen, um den aktuellen Pfad zu nutzen.")
        configpath = input("Pfad angeben:")
        if len(configpath) > 0:
            f = open(pathfile, "w")
            f.write(configpath)
            f.close()
    if len(configpath) == 0:
        configpath = os.path.dirname(sys.argv[0])
        configpath = configpath.replace("\\", "/")
        configpath = configpath[:-1] if configpath.endswith('/') else configpath
        f = open(pathfile, "w")
        f.write(configpath)
        f.close()
    configpath = configpath.replace("\\", "/")
    configpath = configpath[:-1] if configpath.endswith('/') else configpath
    if not os.path.exists(configpath):
        os.makedirs(configpath)
    return configpath


def myjd_input(port, user, password, device):
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

    sections = ['FeedCrawler', 'Hostnames', 'Crawljobs', 'Notifications', 'Hosters', 'Ombi', 'ContentAll',
                'ContentShows', 'CustomDJ']
    for section in sections:
        CrawlerConfig(section, configfile)
    if port:
        CrawlerConfig('FeedCrawler', configfile).save("port", port)

    CrawlerConfig('FeedCrawler', configfile).save("myjd_user", user)
    CrawlerConfig('FeedCrawler', configfile).save("myjd_pass", password)
    CrawlerConfig('FeedCrawler', configfile).save("myjd_device", device)
    device = get_device(configfile)
    if device:
        return device
    else:
        return False


def set_files(configpath):
    global configfile
    global dbfile
    global log_file
    global log_file_debug
    configfile = os.path.join(configpath, "FeedCrawler.ini")
    dbfile = os.path.join(configpath, "FeedCrawler.db")
    log_file = os.path.join(configpath, 'FeedCrawler.log')
    log_file_debug = os.path.join(configpath, 'FeedCrawler_DEBUG.log')


def set_device(set_device):
    global device
    device = set_device


def set_connection_info(set_local_address, set_port, set_prefix, set_docker):
    global local_address
    global port
    global prefix
    global docker
    local_address = set_local_address
    port = set_port
    prefix = set_prefix
    docker = set_docker


def set_logger(set_log_level):
    global logger

    if log_file and log_file_debug:
        logger = logging.getLogger('feedcrawler')
        logger.setLevel(set_log_level)

        console = logging.StreamHandler(stream=sys.stdout)
        log_format = '%(asctime)s - %(message)s'
        formatter = logging.Formatter(log_format)
        console.setLevel(set_log_level)

        logfile = logging.handlers.RotatingFileHandler(log_file)
        logfile.setFormatter(formatter)
        logfile.setLevel(logging.INFO)

        logger.addHandler(logfile)
        logger.addHandler(console)

        if set_log_level == 10:
            logfile_debug = logging.handlers.RotatingFileHandler(log_file_debug)
            logfile_debug.setFormatter(formatter)
            logfile_debug.setLevel(10)
            logger.addHandler(logfile_debug)

        logger = set_logger
    else:
        return False
