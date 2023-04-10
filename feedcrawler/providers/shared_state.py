# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt alle globalen Parameter für die verschiedenen parallel laufenden Threads bereit.

import logging
import os
import sys
from logging import handlers

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
