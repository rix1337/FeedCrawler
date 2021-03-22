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

import traceback
from logging import handlers

import logging
import multiprocessing
import os
import random
import re
import signal
import sys
import time
from docopt import docopt
from requests.packages.urllib3 import disable_warnings as disable_request_warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from rsscrawler import common
from rsscrawler import files
from rsscrawler import version
from rsscrawler.common import Unbuffered
from rsscrawler.common import add_decrypt
from rsscrawler.common import is_device
from rsscrawler.common import longest_substr
from rsscrawler.common import readable_time
from rsscrawler.config import RssConfig
from rsscrawler.db import RssDb
from rsscrawler.myjd import get_device
from rsscrawler.myjd import get_if_one_device
from rsscrawler.myjd import get_info
from rsscrawler.myjd import hoster_check
from rsscrawler.myjd import move_to_downloads
from rsscrawler.myjd import remove_from_linkgrabber
from rsscrawler.myjd import retry_decrypt
from rsscrawler.notifiers import notify
from rsscrawler.ombi import ombi
from rsscrawler.sites.by import BL as BY
from rsscrawler.sites.dd import DD
from rsscrawler.sites.dj import DJ
from rsscrawler.sites.dw import BL as DW
from rsscrawler.sites.fx import BL as FX
from rsscrawler.sites.nk import BL as NK
from rsscrawler.sites.sf import SF
from rsscrawler.sites.sj import SJ
from rsscrawler.sites.ww import BL as WW
from rsscrawler.url import check_url
from rsscrawler.web import start

version = "v." + version.get_version()


def crawler(configfile, dbfile, device, rsscrawler, log_level, log_file, log_format):
    sys.stdout = Unbuffered(sys.stdout)

    logger = logging.getLogger('rsscrawler')
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

    disable_request_warnings(InsecureRequestWarning)

    log_debug = logger.debug

    ombi_first_launch = True

    crawltimes = RssDb(dbfile, "crawltimes")

    arguments = docopt(__doc__, version='RSScrawler')
    if not arguments['--testlauf']:
        while True:
            try:
                if not device or not is_device(device):
                    device = get_device(configfile)
                scraper = check_url(configfile, dbfile)
                start_time = time.time()
                crawltimes.update_store("active", "True")
                crawltimes.update_store("start_time", start_time * 1000)
                log_debug("--------Alle Suchfunktion gestartet.--------")
                requested_movies = 0
                requested_shows = 0
                ombi_string = ""
                if device:
                    ombi_results = ombi(configfile, dbfile, device, log_debug, ombi_first_launch)
                    device = ombi_results[0]
                    ombi_results = ombi_results[1]
                    requested_movies = ombi_results[0]
                    requested_shows = ombi_results[1]
                    ombi_first_launch = False
                if requested_movies or requested_shows:
                    ombi_string = " - Ombi suchte: "
                    if requested_movies:
                        ombi_string = ombi_string + str(requested_movies) + " Filme"
                        if requested_shows:
                            ombi_string = ombi_string + " und "
                    if requested_shows:
                        ombi_string = ombi_string + str(requested_shows) + " Serien"
                for task in search_pool(configfile, dbfile, device, logger, scraper):
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
                next_start = end_time + wait
                log_debug(
                    "-----Alle Suchfunktion ausgeführt (Dauer: " + readable_time(
                        total_time) + ")! Wartezeit bis zum nächsten Suchlauf: " + readable_time(wait) + ombi_string)
                print(time.strftime("%Y-%m-%d %H:%M:%S") +
                      u" - Alle Suchfunktion ausgeführt (Dauer: " + readable_time(
                    total_time) + u")! Wartezeit bis zum nächsten Suchlauf: " + readable_time(wait) + ombi_string)
                crawltimes.update_store("end_time", end_time * 1000)
                crawltimes.update_store("total_time", readable_time(total_time))
                crawltimes.update_store("next_start", next_start * 1000)
                crawltimes.update_store("active", "False")

                wait_chunks = wait // 10
                start_now_triggered = False
                while wait_chunks:
                    time.sleep(10)
                    if RssDb(dbfile, 'crawltimes').retrieve("startnow"):
                        RssDb(dbfile, 'crawltimes').delete("startnow")
                        start_now_triggered = True
                        break

                    wait_chunks -= 1

                if start_now_triggered:
                    log_debug("----------Wartezeit vorzeitig beendet----------")
                else:
                    log_debug("-------------Wartezeit verstrichen-------------")
            except Exception:
                traceback.print_exc()
                time.sleep(10)
    else:
        try:
            if not device or not is_device(device):
                device = get_device(configfile)
            scraper = check_url(configfile, dbfile)
            start_time = time.time()
            log_debug("--------Testlauf gestartet.--------")
            requested_movies = 0
            requested_shows = 0
            ombi_string = ""
            if device:
                ombi_results = ombi(configfile, dbfile, device, log_debug, ombi_first_launch)
                device = ombi_results[0]
                ombi_results = ombi_results[1]
                requested_movies = ombi_results[0]
                requested_shows = ombi_results[1]
            if requested_movies or requested_shows:
                ombi_string = " - Ombi suchte: "
                if requested_movies:
                    ombi_string = ombi_string + str(requested_movies) + " Filme"
                    if requested_shows:
                        ombi_string = ombi_string + " und "
                if requested_shows:
                    ombi_string = ombi_string + str(requested_shows) + " Serien"
            for task in search_pool(configfile, dbfile, device, logger, scraper):
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
                "---Testlauf ausgeführt (Dauer: " + readable_time(total_time) + ")!---" + ombi_string)
            print(time.strftime("%Y-%m-%d %H:%M:%S") +
                  u" - Testlauf ausgeführt (Dauer: " + readable_time(total_time) + ")!" + ombi_string)
        except Exception:
            traceback.print_exc()
            time.sleep(10)


def web_server(port, local_address, docker, configfile, dbfile, log_level, log_file, log_format, device):
    start(port, local_address, docker, configfile, dbfile, log_level, log_file, log_format, device)


def crawldog(configfile, dbfile):
    disable_request_warnings(InsecureRequestWarning)
    crawljobs = RssConfig('Crawljobs', configfile)
    autostart = crawljobs.get("autostart")
    db = RssDb(dbfile, 'crawldog')

    grabber_was_collecting = False
    device = False

    while True:
        try:
            if not device or not is_device(device):
                device = get_device(configfile)

            myjd_packages = get_info(configfile, device)
            grabber_collecting = myjd_packages[2]

            if grabber_was_collecting or grabber_collecting:
                grabber_was_collecting = grabber_collecting
                time.sleep(5)
            else:
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
                            if packages_in_downloader_decrypted:
                                for package in packages_in_downloader_decrypted:
                                    if title[0] in package['name'] or title[0].replace(".", " ") in package['name']:
                                        check = hoster_check(configfile, device, [package], title[0], [0])
                                        device = check[0]
                                        if device:
                                            db.delete(title[0])

                            if packages_in_linkgrabber_decrypted:
                                for package in packages_in_linkgrabber_decrypted:
                                    if title[0] in package['name'] or title[0].replace(".", " ") in package['name']:
                                        check = hoster_check(configfile, device, [package], title[0], [0])
                                        device = check[0]
                                        episode = RssDb(dbfile, 'episode_remover').retrieve(title[0])
                                        if episode:
                                            filenames = package['filenames']
                                            if len(filenames) > 1:
                                                fname_episodes = []
                                                for fname in filenames:
                                                    try:
                                                        if re.match(r'.*S\d{1,3}E\d{1,3}.*', fname,
                                                                    flags=re.IGNORECASE):
                                                            fname = re.findall(r'S\d{1,3}E(\d{1,3})', fname,
                                                                               flags=re.IGNORECASE).pop()
                                                        else:
                                                            fname = fname.replace("hddl8", "").replace("dd51",
                                                                                                       "").replace(
                                                                "264", "").replace("265",
                                                                                   "")
                                                    except:
                                                        fname = fname.replace("hddl8", "").replace("dd51", "").replace(
                                                            "264", "").replace("265", "")
                                                    fname_episode = "".join(re.findall(r'\d+', fname.split(".part")[0]))
                                                    try:
                                                        fname_episodes.append(str(int(fname_episode)))
                                                    except:
                                                        pass
                                                replacer = longest_substr(fname_episodes)

                                                new_fname_episodes = []
                                                for new_ep_fname in fname_episodes:
                                                    try:
                                                        new_fname_episodes.append(
                                                            str(int(new_ep_fname.replace(replacer, ""))))
                                                    except:
                                                        pass
                                                replacer = longest_substr(new_fname_episodes)

                                                newer_fname_episodes = []
                                                for new_ep_fname in new_fname_episodes:
                                                    try:
                                                        newer_fname_episodes.append(
                                                            str(int(re.sub(replacer, "", new_ep_fname, 1))))
                                                    except:
                                                        pass

                                                replacer = longest_substr(newer_fname_episodes)

                                                even_newer_fname_episodes = []
                                                for newer_ep_fname in newer_fname_episodes:
                                                    try:
                                                        even_newer_fname_episodes.append(
                                                            str(int(re.sub(replacer, "", newer_ep_fname, 1))))
                                                    except:
                                                        pass

                                                if even_newer_fname_episodes:
                                                    fname_episodes = even_newer_fname_episodes
                                                elif newer_fname_episodes:
                                                    fname_episodes = newer_fname_episodes
                                                elif new_fname_episodes:
                                                    fname_episodes = new_fname_episodes

                                                delete_linkids = []
                                                pos = 0
                                                for delete_id in package['linkids']:
                                                    if str(episode) != str(fname_episodes[pos]):
                                                        delete_linkids.append(delete_id)
                                                    pos += 1
                                                if delete_linkids:
                                                    delete_uuids = [package['uuid']]
                                                    RssDb(dbfile, 'episode_remover').delete(title[0])
                                                    device = remove_from_linkgrabber(configfile, device, delete_linkids,
                                                                                     delete_uuids)
                                        if autostart:
                                            device = move_to_downloads(configfile, device, package['linkids'],
                                                                       [package['uuid']])
                                        if device:
                                            db.delete(title[0])

                            if offline_packages:
                                for package in offline_packages:
                                    if title[0] in package['name'] or title[0].replace(".", " ") in package['name']:
                                        notify_list.append("[Offline] - " + title[0])
                                        print((u"[Offline] - " + title[0]))
                                        db.delete(title[0])

                            if encrypted_packages:
                                for package in encrypted_packages:
                                    if title[0] in package['name'] or title[0].replace(".", " ") in package['name']:
                                        if title[1] == 'added':
                                            if retry_decrypt(configfile, dbfile, device, package['linkids'],
                                                             [package['uuid']],
                                                             package['urls']):
                                                db.delete(title[0])
                                                db.store(title[0], 'retried')
                                        else:
                                            add_decrypt(package['name'], package['url'], "", dbfile)
                                            device = remove_from_linkgrabber(configfile, device, package['linkids'],
                                                                             [package['uuid']])
                                            notify_list.append("[Click'n'Load notwendig] - " + title[0])
                                            print(u"[Click'n'Load notwendig] - " + title[0])
                                            db.delete(title[0])
                else:
                    if not grabber_collecting:
                        db.reset()

                if notify_list:
                    notify(notify_list, configfile)

                time.sleep(30)
        except Exception:
            traceback.print_exc()
            time.sleep(30)


def search_pool(configfile, dbfile, device, logger, scraper):
    return [
        SJ(configfile, dbfile, device, logger, scraper, filename='SJ_Serien'),
        SJ(configfile, dbfile, device, logger, scraper, filename='SJ_Serien_Regex'),
        SJ(configfile, dbfile, device, logger, scraper, filename='SJ_Staffeln_Regex'),
        SJ(configfile, dbfile, device, logger, scraper, filename='MB_Staffeln'),
        DJ(configfile, dbfile, device, logger, scraper, filename='DJ_Dokus', internal_name='DJ'),
        DJ(configfile, dbfile, device, logger, scraper, filename='DJ_Dokus_Regex', internal_name='DJ'),
        SF(configfile, dbfile, device, logger, scraper, filename='SJ_Serien', internal_name='SJ'),
        SF(configfile, dbfile, device, logger, scraper, filename='SJ_Serien_Regex', internal_name='SJ'),
        SF(configfile, dbfile, device, logger, scraper, filename='SJ_Staffeln_Regex', internal_name='SJ'),
        SF(configfile, dbfile, device, logger, scraper, filename='MB_Staffeln', internal_name='MB'),
        DW(configfile, dbfile, device, logger, scraper, filename='MB_Regex'),
        DW(configfile, dbfile, device, logger, scraper, filename='IMDB'),
        DW(configfile, dbfile, device, logger, scraper, filename='MB_Filme'),
        DW(configfile, dbfile, device, logger, scraper, filename='MB_Staffeln'),
        WW(configfile, dbfile, device, logger, scraper, filename='MB_Regex'),
        WW(configfile, dbfile, device, logger, scraper, filename='IMDB'),
        WW(configfile, dbfile, device, logger, scraper, filename='MB_Filme'),
        WW(configfile, dbfile, device, logger, scraper, filename='MB_Staffeln'),
        FX(configfile, dbfile, device, logger, scraper, filename='MB_Regex'),
        FX(configfile, dbfile, device, logger, scraper, filename='IMDB'),
        FX(configfile, dbfile, device, logger, scraper, filename='MB_Filme'),
        FX(configfile, dbfile, device, logger, scraper, filename='MB_Staffeln'),
        NK(configfile, dbfile, device, logger, scraper, filename='MB_Regex'),
        NK(configfile, dbfile, device, logger, scraper, filename='IMDB'),
        NK(configfile, dbfile, device, logger, scraper, filename='MB_Filme'),
        NK(configfile, dbfile, device, logger, scraper, filename='MB_Staffeln'),
        BY(configfile, dbfile, device, logger, scraper, filename='MB_Regex'),
        BY(configfile, dbfile, device, logger, scraper, filename='IMDB'),
        BY(configfile, dbfile, device, logger, scraper, filename='MB_Filme'),
        BY(configfile, dbfile, device, logger, scraper, filename='MB_Staffeln'),
        DD(configfile, dbfile, device, logger, scraper)
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

    hostnames = RssConfig('Hostnames', configfile)

    def clean_up_hostname(host, string):
        if '/' in string:
            string = string.replace('https://', '').replace('http://', '')
            string = re.findall(r'([a-z-.]*\.[a-z]*)', string)[0]
            hostnames.save(host, string)
        if re.match(r'.*[A-Z].*', string):
            hostnames.save(host, string.lower())
        if string:
            print(u'Hostname für ' + host.upper() + ": " + string)
        else:
            print(u'Hostname für ' + host.upper() + ': Nicht gesetzt!')
        return string

    set_hostnames = {}
    list_names = ['sj', 'dj', 'sf', 'by', 'dw', 'fx', 'nk', 'ww', 'dd']
    for name in list_names:
        hostname = clean_up_hostname(name, hostnames.get(name))
        if hostname:
            set_hostnames[name] = hostname

    if not arguments['--testlauf'] and not set_hostnames:
        print(u'Keine Hostnamen in der RSScrawler.ini gefunden! Beende RSScrawler!')
        time.sleep(10)
        sys.exit(1)

    disable_request_warnings(InsecureRequestWarning)

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
    local_address = 'http://' + common.check_ip() + ':' + str(port) + prefix
    if not arguments['--docker']:
        print(u'Der Webserver ist erreichbar unter ' + local_address)

    if arguments['--keep-cdc']:
        print(u"CDC-Tabelle nicht geleert!")
    else:
        RssDb(dbfile, 'cdc').reset()

    p = multiprocessing.Process(target=web_server,
                                args=(port, local_address, docker, configfile, dbfile, log_level, log_file, log_format,
                                      device))
    p.start()

    if not arguments['--testlauf']:
        c = multiprocessing.Process(target=crawler,
                                    args=(configfile, dbfile, device, rsscrawler, log_level, log_file, log_format))
        c.start()

        w = multiprocessing.Process(target=crawldog, args=(configfile, dbfile))
        w.start()

        print(u'Drücke [Strg] + [C] zum Beenden')

        def signal_handler():
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
