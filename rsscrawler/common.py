# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337
# Enthält Code von:
# https://github.com/bharnett/Infringer/blob/master/LinkRetrieve.py


import base64
import logging
import os
import re
import socket

import six

from rsscrawler.rssconfig import RssConfig
from rsscrawler.rssdb import ListDb
from rsscrawler.rssdb import RssDb

log_info = logging.info
log_error = logging.error
log_debug = logging.debug


def write_crawljob_file(configfile, package_name, subdir, link_text):
    crawljob_dir = RssConfig('RSScrawler', configfile).get('jdownloader') + '/folderwatch'
    try:
        crawljob_file = crawljob_dir + '/%s.crawljob' % unicode(
            re.sub(r'[^\w\s\.-]', '', package_name.replace(' ', '')).strip().lower())
    except NameError:
        crawljob_file = crawljob_dir + '/%s.crawljob' % (
            re.sub(r'[^\w\s\.-]', '', package_name.replace(' ', '')).strip().lower())

    crawljobs = RssConfig('Crawljobs', configfile)
    autostart = crawljobs.get("autostart")
    usesubdir = crawljobs.get("subdir")
    if not usesubdir:
        subdir = ""
    if autostart:
        autostart = "TRUE"
    else:
        autostart = "FALSE"
    try:
        file = open(crawljob_file, 'w')
        file.write('enabled=TRUE\n')
        file.write('autoStart=' + autostart + '\n')
        file.write(
            'extractPasswords=["' + decode_base64("bW92aWUtYmxvZy5vcmc=") + '","' + decode_base64(
                "c2VyaWVuanVua2llcy5vcmc=") + '","' +
            decode_base64("aGQtYXJlYS5vcmc=") + '","' + decode_base64("aGQtd29ybGQub3Jn") + '","' + decode_base64(
                "d2FyZXotd29ybGQub3Jn") + '"]\n')
        file.write('downloadPassword=' +
                   decode_base64("c2VyaWVuanVua2llcy5vcmc=") + '\n')

        file.write('extractAfterDownload=TRUE\n')
        file.write('forcedStart=' + autostart + '\n')
        file.write('autoConfirm=' + autostart + '\n')
        if not subdir == "":
            file.write('downloadFolder=' + subdir + "/" + '%s\n' % package_name)
            if subdir == "RSScrawler/Remux":
                file.write('priority=Lower\n')
        else:
            file.write('downloadFolder=' + '%s\n' % package_name)
        file.write('packageName=%s\n' % package_name.replace(' ', ''))
        file.write('text=%s\n' % link_text)
        file.close()
        return True
    except UnicodeEncodeError as e:
        log_error("Beim Schreibversuch des Crawljobs: %s FEHLER: %s" %
                  (crawljob_file, e.message))
        if os.path.isfile(crawljob_file):
            log_info("Entferne defekten Crawljob: %s" % crawljob_file)
            os.remove(crawljob_file)
        return False


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
    key = key.replace('.', ' ').replace(';', '').replace(',', '').replace(u'Ä', 'Ae').replace(u'ä', 'ae').replace(
        u'Ö', 'Oe').replace(u'ö', 'oe').replace(u'Ü', 'Ue').replace(u'ü', 'ue').replace(u'ß', 'ss').replace('(',
                                                                                                            '').replace(
        ')', '').replace('*', '').replace('|', '').replace('\\', '').replace('/', '').replace('?', '').replace('!',
                                                                                                               '').replace(
        ':', '').replace('  ', ' ').replace("'", '').replace("- ", "")
    return key


def fullhd_title(key):
    return key.replace("720p", "DL.1080p")


def decode_base64(value):
    if six.PY2:
        return value.decode("base64")
    else:
        return base64.b64decode(value).decode()


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
    if time < 0:
        return ""
    else:
        days = time // 86400
        hours = (time - days * 86400) // 3600
        minutes = (time - days * 86400 - hours * 3600) // 60
        seconds = round((time - days * 86400 - hours * 3600 - minutes * 60), 2)
        time = ("{}d:".format(days) if days else "") + \
               ("{}h:".format(hours) if hours else "") + \
               ("{}m:".format(minutes) if minutes else "") + \
               ("{}s".format(seconds) if seconds else "")
    return time
