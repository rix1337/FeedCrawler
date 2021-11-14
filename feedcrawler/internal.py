# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337

import logging
import os
import sys
from logging import handlers

configpath = False
log_level = False
sites = False
device = False
configfile = False
dbfile = False
log_file = False
log_file_debug = False
local_address = False
port = False
prefix = False
docker = False
logger = False
ww_blocked = False
sf_blocked = False


def get_globals():
    return {
        "configpath": configpath,
        "log_level": log_level,
        "sites": sites,
        "device": device,
        "local_address": local_address,
        "port": port,
        "prefix": prefix,
        "docker": docker
    }


def set_globals(global_variables):
    set_files(global_variables["configpath"])
    set_sites()
    set_logger(global_variables["log_level"])
    set_device(global_variables["device"])
    set_connection_info(global_variables["local_address"], global_variables["port"], global_variables["prefix"],
                        global_variables["docker"])


def set_files(set_configpath):
    global configpath
    global configfile
    global dbfile
    global log_file
    global log_file_debug
    configpath = set_configpath
    configfile = os.path.join(configpath, "FeedCrawler.ini")
    dbfile = os.path.join(configpath, "FeedCrawler.db")
    log_file = os.path.join(configpath, 'FeedCrawler.log')
    log_file_debug = os.path.join(configpath, 'FeedCrawler_DEBUG.log')


def set_sites():
    global sites
    sites = ["SJ", "DJ", "SF", "BY", "FX", "NK", "WW"]


def set_device(set_device):
    global device
    device = set_device


def set_logger(set_log_level):
    global log_level
    global logger
    log_level = set_log_level

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

        if not len(logger.handlers):
            logger.addHandler(logfile)
            logger.addHandler(console)

            if set_log_level == 10:
                logfile_debug = logging.handlers.RotatingFileHandler(log_file_debug)
                logfile_debug.setFormatter(formatter)
                logfile_debug.setLevel(10)
                logger.addHandler(logfile_debug)


def set_connection_info(set_local_address, set_port, set_prefix, set_docker):
    global local_address
    global port
    global prefix
    global docker
    local_address = set_local_address
    port = set_port
    prefix = set_prefix
    docker = set_docker
