# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337


"""RSScrawler.

Usage:
  RSScrawler.py [--config="<CFGPFAD>"]
                [--testlauf]
                [--docker]
                [--port=<PORT>]
                [--jd-user=<NUTZERNAME>]
                [--jd-pass=<PASSWORT>]
                [--jd-device=<GERÄTENAME>]
                [--jd-pfad="<JDPATH>"]
                [--cdc-reset]
                [--log-level=<LOGLEVEL>]

Options:
  --config="<CFGPFAD>"      Legt den Ablageort für Einstellungen und Logs fest
  --testlauf                Einmalige Ausführung von RSScrawler
  --docker                  Sperre Pfad und Port auf Docker-Standardwerte (um falsche Einstellungen zu vermeiden)
  --port=<PORT>             Legt den Port des Webservers fest
  --jd-user=NUTZERNAME      Legt den Nutzernamen für My JDownloader fest
  --jd-pass=PASSWORT        Legt das Passwort für My JDownloader fest
  --jd-device=GERÄTENAME    Legt den Gerätenamen für My JDownloader fest
  --jd-pfad="<JDPFAD>"      Legt den Pfad von JDownloader fest um nicht die RSScrawler.ini direkt bearbeiten zu müssen
  --cdc-reset               Leert die CDC-Tabelle (Feed ab hier bereits gecrawlt) vor dem ersten Suchlauf
  --log-level=<LOGLEVEL>    Legt fest, wie genau geloggt wird (CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET )
"""

import logging
import os
import random
import signal
import sys
import time
import traceback
import warnings
from logging import handlers
from multiprocessing import Process

from docopt import docopt

from rsscrawler import common
from rsscrawler import files
from rsscrawler import version
from rsscrawler.myjd import get_device
from rsscrawler.myjd import get_if_one_device
from rsscrawler.notifiers import notify
from rsscrawler.ombi import ombi
from rsscrawler.output import Unbuffered
from rsscrawler.rssconfig import RssConfig
from rsscrawler.rssdb import RssDb
from rsscrawler.sites.bl import BL
from rsscrawler.sites.dd import DD
from rsscrawler.sites.sj import SJ
from rsscrawler.sites.yt import YT
from rsscrawler.url import check_url
from rsscrawler.web import start

version = version.get_version()


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
            log_file.replace("RSScrawler.log", "RSScrawler_DEBUG.log"), maxBytes=100000, backupCount=5)
        logfile_debug.setFormatter(formatter)
        logfile_debug.setLevel(10)
        logger.addHandler(logfile_debug)

    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    warnings.simplefilter("ignore", UnicodeWarning)

    log_debug = logging.debug

    search_pool = [
        YT(configfile, dbfile, device, logging),
        DD(configfile, dbfile, device, logging),
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

    added_items = []

    arguments = docopt(__doc__, version='RSScrawler')
    if not arguments['--testlauf']:
        while True:
            try:
                if not device:
                    device = get_device(configfile)
                check_url(configfile, dbfile)
                start_time = time.time()
                log_debug("--------Alle Suchfunktion gestartet.--------")
                ombi(configfile, dbfile, device, log_debug)
                for task in search_pool:
                    items = task.periodical_task()
                    if items:
                        for i in items:
                            added_items.append(i)
                    log_debug("-----------Suchfunktion ausgeführt!-----------")
                end_time = time.time()
                total_time = end_time - start_time
                total_unit = " Sekunden"
                if total_time > 60:
                    total_time = total_time / 60
                    total_unit = " Minuten"
                total_time = str(round(total_time, 1)) + total_unit
                notify(added_items, configfile)
                added_items = []
                interval = int(rsscrawler.get('interval')) * 60
                random_range = random.randrange(0, interval // 4)
                wait = interval + random_range
                log_debug(
                    "-----Alle Suchfunktion ausgeführt (Dauer: " + total_time + ")! Warte " + str(wait) + " Sekunden.")
                print(time.strftime("%Y-%m-%d %H:%M:%S") +
                      u" - Alle Suchfunktion ausgeführt (Dauer: " + total_time + ")! Warte " + str(wait) + " Sekunden.")
                time.sleep(wait)
                log_debug("-------------Wartezeit verstrichen-------------")
            except Exception:
                traceback.print_exc()
    else:
        try:
            if not device:
                device = get_device(configfile)
            check_url(configfile, dbfile)
            start_time = time.time()
            log_debug("--------Testlauf gestartet.--------")
            ombi(configfile, dbfile, device, log_debug)
            for task in search_pool:
                items = task.periodical_task()
                if items:
                    for i in items:
                        added_items.append(i)
                log_debug("-----------Suchfunktion ausgeführt!-----------")
            end_time = time.time()
            total_time = end_time - start_time
            total_unit = " Sekunden"
            if total_time > 60:
                total_time = total_time / 60
                total_unit = " Minuten"
            total_time = str(round(total_time, 1)) + total_unit
            notify(added_items, configfile)
            log_debug(
                "---Testlauf ausgeführt (Dauer: " + total_time + ")!---")
            print(time.strftime("%Y-%m-%d %H:%M:%S") +
                  u" - Testlauf ausgeführt (Dauer: " + total_time + ")!")
        except Exception:
            traceback.print_exc()


def web_server(port, docker, configfile, dbfile, log_level, log_file, log_format, device):
    start(port, docker, configfile, dbfile, log_level, log_file, log_format, device)


def main():
    arguments = docopt(__doc__, version='RSScrawler')

    print("┌──────────────────────────────────────────────┐")
    print("  RSScrawler " + version + " von RiX")
    print("  https://github.com/rix1337/RSScrawler")
    print("└──────────────────────────────────────────────┘")

    if arguments['--docker']:
        configpath = "/config"
    else:
        configpath = files.config(arguments['--config'])
    configfile = os.path.join(configpath, "RSScrawler.ini")
    dbfile = os.path.join(configpath, "RSScrawler.db")

    print("Nutze das Verzeichnis " + configpath + " für Einstellungen/Logs")

    log_level = logging.__dict__[
        arguments['--log-level']] if arguments['--log-level'] in logging.__dict__ else logging.INFO
    log_file = os.path.join(configpath, 'RSScrawler.log')
    log_format = '%(asctime)s - %(message)s'

    if not os.path.exists(configfile):
        # TODO travis needs to run the whole script without waiting for MyJD input + handle myjd arguments
        device = files.myjd_input(configfile, arguments['--port'])
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
                    print(u'My JDownloader Zugangsdaten fehlerhaft! Beende RSScrawler!')
                    sys.exit(0)
        else:
            device = None

    if not device:
        if not os.path.exists(configfile):
            if not arguments['--jd-pfad']:
                if files.jd_input(configfile, arguments['--port']):
                    print("Der Pfad wurde in der RSScrawler.ini gespeichert.")
                elif arguments['--port']:
                    files.startup(configfile,
                                  "Muss unbedingt vergeben werden!", arguments['--port'])
                else:
                    files.startup(configfile, "Muss unbedingt vergeben werden!", "9090")
                    print(
                        'Der Pfad des JDownloaders muss jetzt unbedingt in der RSScrawler.ini hinterlegt werden.')
                    print('Diese liegt unter ' + configfile)
                    print(u'Viel Spaß! Beende RSScrawler!')
                    sys.exit(0)
            else:
                if arguments['--port']:
                    files.startup(configfile, arguments['--jd-pfad'], arguments['--port'])
                else:
                    files.startup(configfile, arguments['--jd-pfad'], "9090")
                    print(
                        'Die Einstellungen und Listen sind jetzt im Webinterface anpassbar.')
        elif arguments['--jd-pfad'] and arguments['--port']:
            files.startup(configfile, arguments['--jd-pfad'], arguments['--port'])
        elif arguments['--jd-pfad']:
            files.startup(configfile, arguments['--jd-pfad'], None)
        elif arguments['--port']:
            files.startup(configfile, None, arguments['--port'])

        rsscrawler = RssConfig('RSScrawler', configfile)

        if arguments['--jd-pfad']:
            jdownloaderpath = arguments['--jd-pfad']
        else:
            jdownloaderpath = rsscrawler.get("jdownloader")
        if arguments['--docker']:
            jdownloaderpath = '/jd2'
            print(u'Docker-Modus: JDownloader-Pfad und Port können nur per Docker-Run angepasst werden!')
        elif jdownloaderpath == 'Muss unbedingt vergeben werden!':
            jdownloaderpath = files.jd_input(configfile, arguments['--port'])
            if jdownloaderpath:
                print("Der Pfad wurde in der RSScrawler.ini gespeichert.")
            else:
                print('Der Pfad des JDownloaders muss unbedingt in der RSScrawler.ini hinterlegt werden.')
                print('Diese liegt unter ' + configfile)
                print('Beende RSScrawler...')
                sys.exit(0)

        jdownloaderpath = jdownloaderpath.replace("\\", "/")
        jdownloaderpath = jdownloaderpath[:-1] if jdownloaderpath.endswith('/') else jdownloaderpath

        print('Nutze das "folderwatch" Unterverzeichnis von "' +
              jdownloaderpath + u'" für Crawljobs')

        if not os.path.exists(jdownloaderpath):
            print('Der Pfad des JDownloaders existiert nicht.')
            rsscrawler.save("jdownloader", "Muss unbedingt vergeben werden!")
            print('Beende RSScrawler...')
            sys.exit(0)

        if not os.path.exists(jdownloaderpath + "/folderwatch"):
            print(
                u'Der Pfad des JDownloaders enthält nicht das "folderwatch" Unterverzeichnis. Sicher, dass der Pfad stimmt?')
            rsscrawler.save("jdownloader", "Muss unbedingt vergeben werden!")
            print('Beende RSScrawler...')
            sys.exit(0)
    else:
        rsscrawler = RssConfig('RSScrawler', configfile)
        print("Erfolgreich mit My JDownloader verbunden. Gerätename: " + device.name)

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
        print('Der Webserver ist erreichbar unter http://' +
              common.check_ip() + ':' + str(port) + prefix)

    if arguments['--cdc-reset']:
        print("CDC-Tabelle geleert!")
        RssDb(dbfile, 'cdc').reset()

    p = Process(target=web_server, args=(port, docker, configfile, dbfile, log_level, log_file, log_format, device))
    p.start()

    if not arguments['--testlauf']:
        c = Process(target=crawler, args=(configfile, dbfile, device, rsscrawler, log_level, log_file, log_format))
        c.start()

        print(u'Drücke [Strg] + [C] zum Beenden')

        def signal_handler(signal, frame):
            print('Beende RSScrawler...')
            p.terminate()
            c.terminate()
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
