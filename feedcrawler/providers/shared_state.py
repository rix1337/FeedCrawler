# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt alle globalen Parameter für die verschiedenen parallel laufenden Threads bereit.

import logging
import os
import sys
import time
from logging import handlers

from feedcrawler.external_tools.myjd_api import Jddevice, Myjdapi
from feedcrawler.external_tools.myjd_api import TokenExpiredException, RequestTimeoutException, MYJDException
from feedcrawler.providers.config import CrawlerConfig

values = {}
logger = None


def set_shared_dict(manager_dict):
    global values
    values = manager_dict


def set_initial_values(test_run, remove_cloudflare_time):
    global values
    values["test_run"] = test_run
    values["remove_cloudflare_time"] = remove_cloudflare_time
    values["ww_blocked"] = False
    values["sf_blocked"] = False
    values["user_agent"] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                           'Chrome/111.0.0.0 Safari/537.36'


def set_files(configpath):
    global values
    values["configfile"] = os.path.join(configpath, "FeedCrawler.ini")
    values["dbfile"] = os.path.join(configpath, "FeedCrawler.db")
    values["log_file"] = os.path.join(configpath, 'FeedCrawler.log')
    values["log_file_debug"] = os.path.join(configpath, 'FeedCrawler_DEBUG.log')


def set_log_level(log_level):
    global values
    values["log_level"] = log_level


def set_logger():
    global logger

    log_level = values["log_level"]

    logger = logging.getLogger('feedcrawler')
    logger.setLevel(log_level)

    console = logging.StreamHandler(stream=sys.stdout)
    log_format = '%(asctime)s - %(message)s'
    formatter = logging.Formatter(log_format)
    console.setLevel(log_level)

    logfile = logging.handlers.RotatingFileHandler(values["log_file"])
    logfile.setFormatter(formatter)
    logfile.setLevel(logging.INFO)

    if not len(logger.handlers):
        logger.addHandler(logfile)
        logger.addHandler(console)

        if log_level == 10:
            logfile_debug = logging.handlers.RotatingFileHandler(values["log_file_debug"])
            logfile_debug.setFormatter(formatter)
            logfile_debug.setLevel(10)
            logger.addHandler(logfile_debug)


def set_sites():
    global values
    values["sites"] = ["FX", "SF", "DW", "HW", "FF", "BY", "NK", "NX", "WW", "SJ", "DJ", "DD"]


def set_device(new_device):
    global values
    values["device"] = new_device


def check_device(device):
    try:
        valid = isinstance(device, (type, Jddevice)) and device.downloadcontroller.get_current_state()
    except (AttributeError, KeyError, TokenExpiredException, RequestTimeoutException, MYJDException):
        valid = False
    return valid


def connect_device():
    global values

    device = False
    conf = CrawlerConfig('FeedCrawler')
    myjd_user = str(conf.get('myjd_user'))
    myjd_pass = str(conf.get('myjd_pass'))
    myjd_device = str(conf.get('myjd_device'))

    jd = Myjdapi()
    jd.set_app_key('FeedCrawler')

    if myjd_user and myjd_pass and myjd_device:
        try:
            jd.connect(myjd_user, myjd_pass)
            jd.update_devices()
            device = jd.get_device(myjd_device)
        except (TokenExpiredException, RequestTimeoutException, MYJDException):
            pass

    if check_device(device):
        values["device"] = device
        return True
    else:
        return False


def get_device():
    global values
    attempts = 0

    while True:
        try:
            if check_device(values["device"]):
                break
        except (AttributeError, KeyError, TokenExpiredException, RequestTimeoutException, MYJDException):
            pass
        attempts += 1

        values["device"] = False

        if attempts % 10 == 0:
            print(
                f"WARNUNG: {attempts} aufeinanderfolgende My JDownloader Verbindungsfehler. Bitte prüfen und ggf. neu starten!")
        time.sleep(3)

        if connect_device():
            break

    return values["device"]


def set_connection_info(local_address, port, prefix, docker):
    global values
    values["local_address"] = local_address
    values["port"] = port
    values["prefix"] = prefix
    values["docker"] = docker


def clear_request_cache():
    global values
    for key in list(values.keys()):
        if key.startswith('request_'):
            values.pop(key)
    values["request_cache_hits"] = 0
