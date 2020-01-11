# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337
# Enthält Code von:
# https://github.com/bharnett/Infringer/blob/master/LinkRetrieve.py


import base64
import datetime
import logging
import re
import socket

from rsscrawler import myjdapi
from rsscrawler.rssconfig import RssConfig
from rsscrawler.rssdb import ListDb
from rsscrawler.rssdb import RssDb

log_info = logging.info
log_error = logging.error
log_debug = logging.debug


def check_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 0))
        ip = s.getsockname()[0]
    except:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def entfernen(retailtitel, identifier, dbfile):
    titles = retail_sub(retailtitel)
    retail = titles[0]
    retailyear = titles[1]
    if identifier == '2':
        liste = "MB_3D"
    else:
        liste = "MB_Filme"
    cont = ListDb(dbfile, liste).retrieve()
    new_cont = []
    if cont:
        for line in cont:
            if line.lower() == retailyear.lower() or line.lower() == retail.lower():
                line = re.sub(r'^(' + re.escape(retailyear.lower()) + '|' + re.escape(retail.lower()) + ')', '',
                              line.lower())
            if line:
                new_cont.append(line)
    ListDb(dbfile, liste).store_list(new_cont)
    RssDb(dbfile, "retail").store(retail, "retail")
    RssDb(dbfile, "retail").store(retailyear, "retail")
    log_debug(retail + " durch Cutoff aus " + liste + " entfernt.")


def retail_sub(title):
    simplified = title.replace(".", " ")
    retail = re.sub(
        r'(|.UNRATED.*|.Unrated.*|.Uncut.*|.UNCUT.*)(|.Directors.Cut.*|.Final.Cut.*|.DC.*|.EXTENDED.*|.Extended.*|.Theatrical.*|.THEATRICAL.*)(|.3D.*|.3D.HSBS.*|.3D.HOU.*|.HSBS.*|.HOU.*)(|.)\d{4}(|.)(|.UNRATED.*|.Unrated.*|.Uncut.*|.UNCUT.*)(|.Directors.Cut.*|.Final.Cut.*|.DC.*|.EXTENDED.*|.Extended.*|.Theatrical.*|.THEATRICAL.*)(|.3D.*|.3D.HSBS.*|.3D.HOU.*|.HSBS.*|.HOU.*).(German|GERMAN)(|.AC3|.DTS|.DTS-HD)(|.DL)(|.AC3|.DTS).(2160|1080|720)p.(UHD.|Ultra.HD.|)(HDDVD|BluRay)(|.HDR)(|.AVC|.AVC.REMUX|.x264|.x265)(|.REPACK|.RERiP|.REAL.RERiP)-.*',
        "", simplified)
    retailyear = re.sub(
        r'(|.UNRATED.*|.Unrated.*|.Uncut.*|.UNCUT.*)(|.Directors.Cut.*|.Final.Cut.*|.DC.*|.EXTENDED.*|.Extended.*|.Theatrical.*|.THEATRICAL.*)(|.3D.*|.3D.HSBS.*|.3D.HOU.*|.HSBS.*|.HOU.*).(German|GERMAN)(|.AC3|.DTS|.DTS-HD)(|.DL)(|.AC3|.DTS|.DTS-HD).(2160|1080|720)p.(UHD.|Ultra.HD.|)(HDDVD|BluRay)(|.HDR)(|.AVC|.AVC.REMUX|.x264|.x265)(|.REPACK|.RERiP|.REAL.RERiP)-.*',
        "", simplified)
    return retail, retailyear


def cutoff(key, identifier, dbfile):
    retailfinder = re.search(
        r'(|.UNRATED.*|.Unrated.*|.Uncut.*|.UNCUT.*)(|.Directors.Cut.*|.Final.Cut.*|.DC.*|.EXTENDED.*|.Extended.*|.Theatrical.*|.THEATRICAL.*)(|.3D.*|.3D.HSBS.*|.3D.HOU.*|.HSBS.*|.HOU.*).(German|GERMAN)(|.AC3|.DTS|.DTS-HD)(|.DL)(|.AC3|.DTS|.DTS-HD).(2160|1080|720)p.(UHD.|Ultra.HD.|)(HDDVD|BluRay)(|.HDR)(|.AVC|.AVC.REMUX|.x264|.x265)(|.REPACK|.RERiP|.REAL.RERiP)-.*',
        key)
    if retailfinder:
        entfernen(key, identifier, dbfile)
        return True
    else:
        return False


def sanitize(key):
    key = key.replace('.', ' ').replace(';', '').replace(',', '').replace(u'Ä', 'Ae').replace(u'ä', 'ae').replace('ä',
                                                                                                                  'ae').replace(
        u'Ö', 'Oe').replace(u'ö', 'oe').replace(u'Ü', 'Ue').replace(u'ü', 'ue').replace(u'ß', 'ss').replace('(',
                                                                                                            '').replace(
        ')', '').replace('*', '').replace('|', '').replace('\\', '').replace('/', '').replace('?', '').replace('!',
                                                                                                               '').replace(
        ':', '').replace('  ', ' ').replace("'", '').replace("- ", "")
    return key


def fullhd_title(key):
    return key.replace("720p", "DL.1080p")


def decode_base64(value):
    value = value.replace("-", "/")
    return base64.b64decode(value).decode()


def encode_base64(value):
    return base64.b64encode(value.encode("utf-8")).decode().replace("/", "-")


def readable_size(size):
    if size:
        power = 2 ** 10
        n = 0
        powers = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
        while size > power:
            size /= power
            n += 1
        size = round(size, 2)
        size = str(size) + " " + powers[n] + 'B'
        return size
    else:
        return ""


def readable_time(time):
    try:
        if not time:
            time = 0
    except:
        time = 0
    time = str(datetime.timedelta(seconds=int(time)))
    if len(time) == 7:
        time = "0" + time
    return time


def is_device(device):
    return isinstance(device, (type, myjdapi.Jddevice))


def longest_substr(data):
    substr = ''
    if len(data) > 1 and len(data[0]) > 0:
        for i in range(len(data[0])):
            for j in range(len(data[0]) - i + 1):
                if j > len(substr) and all(data[0][i:i + j] in x for x in data):
                    substr = data[0][i:i + j]
    return substr


def check_hoster(to_check, configfile):
    hosters = RssConfig("Hosters", configfile).get_section()
    for hoster in hosters:
        if hosters[hoster] == "True":
            if hoster in to_check.lower():
                return True
    return False


class Unbuffered(object):
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def writelines(self, datas):
        self.stream.writelines(datas)
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)
