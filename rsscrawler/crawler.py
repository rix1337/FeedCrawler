# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337


"""RSScrawler.

Usage:
  crawler.py [--config="<CFGPFAD>"]
                [--testlauf]
                [--docker]
                [--port=<PORT>]
                [--jd-user=<NUTZERNAME>]
                [--jd-pass=<PASSWORT>]
                [--jd-device=<GERÄTENAME>]
                [--keep-cdc]
                [--log-level=<LOGLEVEL>]

Options:
  --log-level=<LOGLEVEL>    Legt fest, wie genau geloggt wird (CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET )
  --config="<CFGPFAD>"      Legt den Ablageort für Einstellungen und Logs fest
  --port=<PORT>             Legt den Port des Webservers fest
  --jd-user=NUTZERNAME      Legt den Nutzernamen für My JDownloader fest
  --jd-pass=PASSWORT        Legt das Passwort für My JDownloader fest
  --jd-device=GERÄTENAME    Legt den Gerätenamen für My JDownloader fest
  --keep-cdc                Leere die CDC-Tabelle (Feed ab hier bereits gecrawlt) nicht vor dem ersten Suchlauf
  --testlauf                Intern: Einmalige Ausführung von RSScrawler (ohne auf MyJDownloader-Konto zu achten)
  --docker                  Intern: Sperre Pfad und Port auf Docker-Standardwerte (um falsche Einstellungen zu vermeiden)
"""

import logging
import os
import random
import re
import signal
import sys
import time
import traceback
import warnings
from logging import handlers
import multiprocessing

from docopt import docopt

from rsscrawler import common
from rsscrawler import files
from rsscrawler import version
from rsscrawler.common import is_device
from rsscrawler.common import readable_time
from rsscrawler.myjd import get_device
from rsscrawler.myjd import get_if_one_device
from rsscrawler.myjd import get_info
from rsscrawler.myjd import hoster_check
from rsscrawler.myjd import move_to_downloads
from rsscrawler.myjd import package_merge
from rsscrawler.myjd import retry_decrypt
from rsscrawler.notifiers import notify
from rsscrawler.ombi import ombi
from rsscrawler.output import Unbuffered
from rsscrawler.rssconfig import RssConfig
from rsscrawler.rssdb import RssDb
from rsscrawler.sites.bl import BL
from rsscrawler.sites.dd import DD
from rsscrawler.sites.dj import DJ
from rsscrawler.sites.sj import SJ
from rsscrawler.sites.yt import YT
from rsscrawler.url import check_url
from rsscrawler.web import start

version = "v." + version.get_version()


def crawler(configfile, dbfile, device, rsscrawler, log_level, log_file, log_format):
    sys.stdout = Unbuffered(sys.stdout)

    logger = logging.getLogger('')
    logger.setLevel(log_level)

    console = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter(log_format)
    console.setLevel(log_level)

    logfile = logging.handlers.RotatingFileHandler(log_file)
    logfile.setFormatter(formatter)
    logfile.setLevel(logging.INFO)

    logger.addHandler(logfile)
    logger.addHandler(console)

    if log_level == 10:
        logfile_debug = logging.handlers.RotatingFileHandler(
            log_file.replace("RSScrawler.log", "RSScrawler_DEBUG.log"))
        logfile_debug.setFormatter(formatter)
        logfile_debug.setLevel(10)
        logger.addHandler(logfile_debug)

    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    warnings.simplefilter("ignore", UnicodeWarning)

    log_debug = logging.debug

    arguments = docopt(__doc__, version='RSScrawler')
    if not arguments['--testlauf']:
        while True:
            try:
                if not device or not is_device(device):
                    device = get_device(configfile)
                check_url(configfile, dbfile)
                start_time = time.time()
                log_debug("--------Alle Suchfunktion gestartet.--------")
                if device:
                    device = ombi(configfile, dbfile, device, log_debug)
                for task in search_pool(configfile, dbfile, device, logging):
                    name = task._INTERNAL_NAME
                    try:
                        file = " - Liste: " + task.filename
                    except AttributeError:
                        file = ""
                    log_debug("-----------Suchfunktion (" + name + file + ") gestartet!-----------")
                    device = task.periodical_task()
                    log_debug("-----------Suchfunktion (" + name + file + ") ausgeführt!-----------")
                end_time = time.time()
                total_time = end_time - start_time
                interval = int(rsscrawler.get('interval')) * 60
                random_range = random.randrange(0, interval // 4)
                wait = interval + random_range
                log_debug(
                    "-----Alle Suchfunktion ausgeführt (Dauer: " + readable_time(
                        total_time) + ")! Wartezeit bis zum nächsten Suchlauf: " + readable_time(wait))
                print(time.strftime("%Y-%m-%d %H:%M:%S") +
                      u" - Alle Suchfunktion ausgeführt (Dauer: " + readable_time(
                    total_time) + u")! Wartezeit bis zum nächsten Suchlauf: " + readable_time(wait))
                time.sleep(wait)
                log_debug("-------------Wartezeit verstrichen-------------")
            except Exception:
                traceback.print_exc()
                time.sleep(10)
    else:
        try:
            if not device or not is_device(device):
                device = get_device(configfile)
            check_url(configfile, dbfile)
            start_time = time.time()
            log_debug("--------Testlauf gestartet.--------")
            if device:
                device = ombi(configfile, dbfile, device, log_debug)
            for task in search_pool(configfile, dbfile, device, logging):
                name = task._INTERNAL_NAME
                try:
                    file = " - Liste: " + task.filename
                except AttributeError:
                    file = ""
                log_debug("-----------Suchfunktion (" + name + file + ") gestartet!-----------")
                task.periodical_task()
                log_debug("-----------Suchfunktion (" + name + file + ") ausgeführt!-----------")
            end_time = time.time()
            total_time = end_time - start_time
            log_debug(
                "---Testlauf ausgeführt (Dauer: " + readable_time(total_time) + ")!---")
            print(time.strftime("%Y-%m-%d %H:%M:%S") +
                  u" - Testlauf ausgeführt (Dauer: " + readable_time(total_time) + ")!")
        except Exception:
            traceback.print_exc()
            time.sleep(10)


def web_server(port, docker, configfile, dbfile, log_level, log_file, log_format, device):
    start(port, docker, configfile, dbfile, log_level, log_file, log_format, device)


def crawldog(configfile, dbfile):
    crawljobs = RssConfig('Crawljobs', configfile)
    autostart = crawljobs.get("autostart")
    db = RssDb(dbfile, 'crawldog')

    device = False

    while True:
        try:
            if not device or not is_device(device):
                device = get_device(configfile)

            myjd_packages = get_info(configfile, device)

            grabber_collecting = myjd_packages[2]
            packages_in_downloader_decrypted = myjd_packages[4][0]
            packages_in_linkgrabber_decrypted = myjd_packages[4][1]
            offline_packages = myjd_packages[4][2]
            encrypted_packages = myjd_packages[4][3]

            try:
                watched_titles = db.retrieve_all_titles()
            except:
                watched_titles = False

            notify_list = []

            if packages_in_downloader_decrypted or packages_in_linkgrabber_decrypted or offline_packages or encrypted_packages:

                if watched_titles:
                    for title in watched_titles:
                        is_episode = re.findall(r'[\w.\s]*S\d{1,2}(E\d{1,2})[\w.\s]*', title[0])

                        if packages_in_downloader_decrypted:
                            for package in packages_in_downloader_decrypted:
                                if title[0] == package['name'] or title[0].replace(".", " ") == package['name']:
                                    removed_links = False
                                    if is_episode:
                                        check = package_merge(configfile, device, [package], title[0], [0])
                                        device = check[0]
                                        removed_links = check[1]
                                    check = hoster_check(configfile, device, [package], title[0], [0])
                                    device = check[0]
                                    if not removed_links:
                                        removed_links = check[1]
                                    if autostart:
                                        device = move_to_downloads(configfile, device, package['linkids'],
                                                                   [package['uuid']])
                                    if not removed_links:
                                        db.delete(title[0])
                        if packages_in_linkgrabber_decrypted:
                            for package in packages_in_linkgrabber_decrypted:
                                if title[0] == package['name'] or title[0].replace(".", " ") == package['name']:
                                    removed_links = False
                                    if is_episode:
                                        check = package_merge(configfile, device, [package], title[0], [0])
                                        device = check[0]
                                        removed_links = check[1]
                                    check = hoster_check(configfile, device, [package], title[0], [0])
                                    device = check[0]
                                    if not removed_links:
                                        removed_links = check[1]
                                    if autostart:
                                        device = move_to_downloads(configfile, device, package['linkids'],
                                                                   [package['uuid']])
                                    if not removed_links:
                                        db.delete(title[0])

                        if offline_packages:
                            for package in offline_packages:
                                if title[0] == package['name'] or title[0].replace(".", " ") == package['name']:
                                    notify_list.append("[Offline] - " + title[0])
                                    print((u"[Offline] - " + title[0]))
                                    db.delete(title[0])
                        if encrypted_packages:
                            for package in encrypted_packages:
                                if title[0] == package['name'] or title[0].replace(".", " ") == package['name']:
                                    if title[1] == 'added':
                                        if retry_decrypt(configfile, dbfile, device, package['linkids'],
                                                         [package['uuid']],
                                                         package['urls']):
                                            db.delete(title[0])
                                            db.store(title[0], 'retried')
                                    else:
                                        notify_list.append("[Click'n'Load notwendig] - " + title[0])
                                        print(u"[Click'n'Load notwendig] - " + title[0])
                                        db.delete(title[0])
            else:
                if not grabber_collecting:
                    if watched_titles:
                        for title in watched_titles:
                            notify_list.append("[Verschwundenes Paket] - " + title[0])
                            print(u"[Verschwundenes Paket] - " + title[0])
                    db.reset()

            if notify_list:
                notify(notify_list, configfile)

            time.sleep(30)
        except Exception:
            traceback.print_exc()
            time.sleep(10)


def search_pool(configfile, dbfile, device, logging):
    return [
        YT(configfile, dbfile, device, logging),
        DD(configfile, dbfile, device, logging),
        DJ(configfile, dbfile, device, logging, filename='DJ_Dokus', internal_name='DJ'),
        DJ(configfile, dbfile, device, logging, filename='DJ_Dokus_Regex', internal_name='DJ'),
        SJ(configfile, dbfile, device, logging, filename='SJ_Serien', internal_name='SJ'),
        SJ(configfile, dbfile, device, logging, filename='SJ_Serien_Regex', internal_name='SJ'),
        SJ(configfile, dbfile, device, logging, filename='SJ_Staffeln_Regex', internal_name='SJ'),
        SJ(configfile, dbfile, device, logging, filename='MB_Staffeln', internal_name='MB'),
        BL(configfile, dbfile, device, logging, filename='MB_Regex'),
        BL(configfile, dbfile, device, logging, filename='IMDB'),
        BL(configfile, dbfile, device, logging, filename='MB_Filme'),
        BL(configfile, dbfile, device, logging, filename='MB_Staffeln'),
        BL(configfile, dbfile, device, logging, filename='MB_3D')
    ]


def main():
    arguments = docopt(__doc__, version='RSScrawler')

    print(u"┌──────────────────────────────────────────────┐")
    print(u"  RSScrawler " + version + " von RiX")
    print(u"  https://github.com/rix1337/RSScrawler")
    print(u"└──────────────────────────────────────────────┘")

    if arguments['--docker']:
        configpath = "/config"
    else:
        configpath = files.config(arguments['--config'])
    configfile = os.path.join(configpath, "RSScrawler.ini")
    dbfile = os.path.join(configpath, "RSScrawler.db")

    print(u"Nutze das Verzeichnis " + configpath + u" für Einstellungen/Logs")

    log_level = logging.__dict__[
        arguments['--log-level']] if arguments['--log-level'] in logging.__dict__ else logging.INFO
    log_file = os.path.join(configpath, 'RSScrawler.log')
    log_format = '%(asctime)s - %(message)s'

    if arguments['--testlauf']:
        device = False
    else:
        if not os.path.exists(configfile):
            if arguments['--docker']:
                if arguments['--jd-user'] and arguments['--jd-pass']:
                    device = files.myjd_input(configfile, arguments['--port'], arguments['--jd-user'],
                                              arguments['--jd-pass'], arguments['--jd-device'])
                else:
                    device = False
            else:
                device = files.myjd_input(configfile, arguments['--port'], arguments['--jd-user'],
                                          arguments['--jd-pass'],
                                          arguments['--jd-device'])
        else:
            rsscrawler = RssConfig('RSScrawler', configfile)
            user = rsscrawler.get('myjd_user')
            password = rsscrawler.get('myjd_pass')
            if user and password:
                device = get_device(configfile)
                if not device:
                    device = get_if_one_device(user, password)
                    if device:
                        print(u"Gerätename " + device + " automatisch ermittelt.")
                        rsscrawler.save('myjd_device', device)
                        device = get_device(configfile)
            else:
                device = files.myjd_input(configfile, arguments['--port'], arguments['--jd-user'],
                                          arguments['--jd-pass'], arguments['--jd-device'])

        if not device and not arguments['--testlauf']:
            print(u'My JDownloader Zugangsdaten fehlerhaft! Beende RSScrawler!')
            time.sleep(10)
            sys.exit(1)
        else:
            print(u"Erfolgreich mit My JDownloader verbunden. Gerätename: " + device.name)

    rsscrawler = RssConfig('RSScrawler', configfile)

    port = int(rsscrawler.get("port"))
    docker = False
    if arguments['--docker']:
        port = int('9090')
        docker = True
    elif arguments['--port']:
        port = int(arguments['--port'])

    if rsscrawler.get("prefix"):
        prefix = '/' + rsscrawler.get("prefix")
    else:
        prefix = ''
    if not arguments['--docker']:
        print(u'Der Webserver ist erreichbar unter http://' +
              common.check_ip() + ':' + str(port) + prefix)

    if arguments['--keep-cdc']:
        print(u"CDC-Tabelle nicht geleert!")
    else:
        RssDb(dbfile, 'cdc').reset()

    p = multiprocessing.Process(target=web_server, args=(port, docker, configfile, dbfile, log_level, log_file, log_format, device))
    p.start()

    if not arguments['--testlauf']:
        c = multiprocessing.Process(target=crawler, args=(configfile, dbfile, device, rsscrawler, log_level, log_file, log_format))
        c.start()

        w = multiprocessing.Process(target=crawldog, args=(configfile, dbfile))
        w.start()

        print(u'Drücke [Strg] + [C] zum Beenden')

        def signal_handler(signal, frame):
            print(u'Beende RSScrawler...')
            p.terminate()
            c.terminate()
            w.terminate()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        try:
            while True:
                signal.pause()
        except AttributeError:
            while True:
                time.sleep(1)
    else:
        crawler(configfile, dbfile, device, rsscrawler, log_level, log_file, log_format)
        p.terminate()
        sys.exit(0)


if __name__ == "__main__":
    main()
