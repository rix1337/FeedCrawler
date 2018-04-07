# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337
# Enthält Code von:
# https://github.com/bharnett/Infringer/blob/master/LinkRetrieve.py

import files
import logging
import os
import re
import socket
import sys
from rssconfig import RssConfig

log_info = logging.info
log_error = logging.error
log_debug = logging.debug


def write_crawljob_file(package_name, folder_name, link_text, crawljob_dir, subdir):
    crawljob_file = crawljob_dir + '/%s.crawljob' % unicode(
        re.sub('[^\w\s\.-]', '', package_name.replace(' ', '')).strip().lower())
    crawljobs = RssConfig('Crawljobs')
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
        file.write('extractPasswords=["' + "bW92aWUtYmxvZy5vcmc=".decode('base64') + '","' + "c2VyaWVuanVua2llcy5vcmc=".decode('base64') + '","' +
                   "aGQtYXJlYS5vcmc=".decode('base64') + '","' + "aGQtd29ybGQub3Jn".decode('base64') + '","' + "d2FyZXotd29ybGQub3Jn".decode('base64') + '"]\n')
        file.write('downloadPassword=' +
                   "c2VyaWVuanVua2llcy5vcmc=".decode('base64') + '\n')
        file.write('extractAfterDownload=TRUE\n')
        file.write('forcedStart=' + autostart + '\n')
        file.write('autoConfirm=' + autostart + '\n')
        if not subdir == "":
            file.write('downloadFolder=' + subdir + "/" + '%s\n' % folder_name)
            if subdir == "RSScrawler/Remux":
                file.write('priority=Lower\n')
        else:
            file.write('downloadFolder=' + '%s\n' % folder_name)
        file.write('packageName=%s\n' % package_name.replace(' ', ''))
        file.write('text=%s\n' % link_text)
        file.close()
        return True
    except UnicodeEncodeError as e:
        file.close()
        log_error("Beim Schreibversuch des Crawljobs: %s FEHLER: %s" %
                  (crawljob_file, e.message))
        if os.path.isfile(crawljob_file):
            log_info("Entferne defekten Crawljob: %s" % crawljob_file)
            os.remove(crawljob_file)
        return False


def checkIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 0))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def entfernen(retailtitel, identifier):
    def capitalize(line):
        line = line.rstrip()
        return ' '.join(s[0].upper() + s[1:] for s in line.split(' '))
    simplified = retailtitel.replace(".", " ")
    retail = re.sub(
        r'(|.UNRATED|.Unrated|.Uncut|.UNCUT)(|.Directors.Cut|.DC|.EXTENDED|.Extended|.Theatrical|.THEATRICAL)(|.3D|.3D.HSBS|.3D.HOU|.HSBS|.HOU)(|.)\d{4}(|.)(|.UNRATED|.Unrated|.Uncut|.UNCUT)(|.Directors.Cut|.DC|.EXTENDED|.Extended|.Theatrical|.THEATRICAL)(|.3D|.3D.HSBS|.3D.HOU|.HSBS|.HOU).(German|GERMAN)(|.AC3|.DTS|.DTS-HD)(|.DL)(|.AC3|.DTS).(2160|1080|720)p.(UHD.|Ultra.HD.|)(HDDVD|BluRay)(|.HDR)(|.AVC|.AVC.REMUX|.x264|.x265)(|.REPACK|.RERiP)-.*', "", simplified)
    retailyear = re.sub(r'(|.UNRATED|.Unrated|.Uncut|.UNCUT)(|.Directors.Cut|.DC|.EXTENDED|.Extended|.Theatrical|.THEATRICAL)(|.3D|.3D.HSBS|.3D.HOU|.HSBS|.HOU).(German|GERMAN)(|.AC3|.DTS|.DTS-HD)(|.DL)(|.AC3|.DTS|.DTS-HD).(2160|1080|720)p.(UHD.|Ultra.HD.|)(HDDVD|BluRay)(|.HDR)(|.AVC|.AVC.REMUX|.x264|.x265)(|.REPACK|.RERiP)-.*', "", simplified)
    if identifier == '2':
        liste = "MB_3D"
    else:
        liste = "MB_Filme"
    with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/' + liste + '.txt'), 'r') as l:
        content = []
        for line in l:
            content.append(re.sub(r'^(' + re.escape(retailyear) + '|' + re.escape(retail) + '|' + re.escape(retailyear.lower()) + '|' + re.escape(retail.lower()) + '|' +
                                  re.escape(retailyear.upper()) + '|' + re.escape(retail.upper()) + '|' + re.escape(capitalize(retailyear)) + '|' + re.escape(capitalize(retail)) + ')', '', line))
        l.close()
    with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/' + liste + '.txt'), 'w') as w:
        w.write(''.join(content))
    log_debug(retail + " durch Cutoff aus " + liste + " entfernt.")


def cutoff(key, identifier):
    retailfinder = re.search("(|.UNRATED|Uncut|UNCUT)(|.Directors.Cut|.DC|.EXTENDED|.Extended|.Theatrical|.THEATRICAL)(|.3D|.3D.HSBS|.3D.HOU|.HSBS|.HOU).(German|GERMAN)(|.AC3|.DTS|.DTS-HD)(|.DL)(|.AC3|.DTS|.DTS-HD).(2160|1080|720)p.(UHD.|Ultra.HD.|)(HDDVD|BluRay)(|.HDR)(|.AVC|.AVC.REMUX|.x264|.x265)(|.REPACK|.RERiP)-.*", key)
    if retailfinder:
        entfernen(key, identifier)
        return True
    else:
        return False
