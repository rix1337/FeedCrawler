# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt alle globalen Parameter für die verschiedenen parallel laufenden Threads bereit.

import logging
import os
import platform
import sys
import time
from logging import handlers

from feedcrawler.external_tools.myjd_api import Jddevice, Myjdapi
from feedcrawler.external_tools.myjd_api import TokenExpiredException, RequestTimeoutException, MYJDException
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.gui import message_box_open_browser

values = {}
lock = None
logger = None


def set_state(manager_dict, manager_lock):
    global values
    global lock
    values = manager_dict
    lock = manager_lock


def update(key, value):
    global values
    global lock
    lock.acquire()
    try:
        values[key] = value
    finally:
        lock.release()


def set_initial_values():
    if (os.environ.get('DOCKER') or (
            not platform.system() == 'Windows' and not platform.system() == 'Darwin' and not os.environ.get(
        'DISPLAY'))):
        gui_enabled = False
    else:
        gui_enabled = True
    update("connected", False)
    update("exiting", False)
    update("gui", gui_enabled)
    update("gui_active_in_tray_and_browser_opened_for_config_once", False)
    update("ww_blocked", False)
    update("sf_blocked", False)
    update("user_agent",
           "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


def set_files(config_path):
    update("configfile", os.path.join(config_path, "FeedCrawler.ini"))
    update("dbfile", os.path.join(config_path, "FeedCrawler.db"))
    update("log_file", os.path.join(config_path, 'FeedCrawler.log'))
    update("log_file_debug", os.path.join(config_path, 'FeedCrawler_DEBUG.log'))


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
    update("sites", ["FX", "SF", "DW", "HW", "FF", "BY", "NK", "NX", "WW", "SJ", "DJ", "DD"])


def gui_active_in_tray_and_browser_opened_for_config_once():
    if values["gui"] and not values["gui_active_in_tray_and_browser_opened_for_config_once"]:
        message_box_open_browser(f"http://localhost:9090?cache_bust={int(time.time())}")
        update("gui_active_in_tray_and_browser_opened_for_config_once", True)
        return True


def set_device(new_device):
    update("device", new_device)


def check_device(device):
    try:
        valid = isinstance(device, (type, Jddevice)) and device.downloadcontroller.get_current_state()
    except (AttributeError, KeyError, TokenExpiredException, RequestTimeoutException, MYJDException):
        valid = False
    return valid


def connect_device():
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
        update("device", device)
        return True
    else:
        return False


def get_device():
    attempts = 0

    while True:
        try:
            if check_device(values["device"]):
                break
        except (AttributeError, KeyError, TokenExpiredException, RequestTimeoutException, MYJDException):
            pass
        attempts += 1

        update("device", False)

        if attempts % 10 == 0:
            print(
                f"WARNUNG: {attempts} aufeinanderfolgende My-JDownloader-Verbindungsfehler. Bitte prüfen und ggf. neu starten!")
        time.sleep(3)

        if connect_device():
            break

    return values["device"]


def set_device_from_config():
    config = CrawlerConfig('FeedCrawler')
    myjd_user = str(config.get('myjd_user'))
    myjd_pass = str(config.get('myjd_pass'))
    myjd_device = str(config.get('myjd_device'))

    update("device", myjd_device)

    jd = Myjdapi()
    jd.set_app_key('FeedCrawler')

    if myjd_user and myjd_pass and myjd_device:
        try:
            jd.connect(myjd_user, myjd_pass)
            jd.update_devices()
            return jd.get_device(myjd_device)
        except (TokenExpiredException, RequestTimeoutException, MYJDException):
            pass
    return False


def set_connection_info(local_address, port, prefix):
    update("local_address", local_address)
    update("port", port)
    update("prefix", prefix)


def clear_request_cache():
    global values
    global lock
    lock.acquire()
    try:
        for key in list(values.keys()):
            if key.startswith('request_'):
                values.pop(key)
    finally:
        lock.release()
    update("request_cache_hits", 0)
