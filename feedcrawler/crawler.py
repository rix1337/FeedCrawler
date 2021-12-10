# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337


"""FeedCrawler.

Usage:
  crawler.py [--config="<CFGPFAD>"]
                [--test_run]
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
  --test_run                Intern: Führt einen Testlauf durch
  --docker                  Intern: Sperre Pfad und Port auf Docker-Standardwerte (um falsche Einstellungen zu vermeiden)
"""

import logging
import multiprocessing
import os
import random
import re
import signal
import sys
import time
import traceback

from docopt import docopt
from requests.packages.urllib3 import disable_warnings as disable_request_warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from feedcrawler import common
from feedcrawler import internal
from feedcrawler import myjd
from feedcrawler import version
from feedcrawler.common import Unbuffered
from feedcrawler.common import is_device
from feedcrawler.common import longest_substr
from feedcrawler.common import readable_time
from feedcrawler.config import CrawlerConfig
from feedcrawler.db import FeedDb
from feedcrawler.flaresolverr import clean_flaresolverr_sessions
from feedcrawler.myjd import add_decrypt
from feedcrawler.myjd import get_device
from feedcrawler.myjd import get_if_one_device
from feedcrawler.myjd import get_info
from feedcrawler.myjd import hoster_check
from feedcrawler.myjd import move_to_downloads
from feedcrawler.myjd import remove_from_linkgrabber
from feedcrawler.myjd import rename_package_in_linkgrabber
from feedcrawler.myjd import retry_decrypt
from feedcrawler.notifiers import notify
from feedcrawler.ombi import ombi
from feedcrawler.sites.content_all_by import BL as BY
from feedcrawler.sites.content_all_fx import BL as FX
from feedcrawler.sites.content_all_nk import BL as NK
from feedcrawler.sites.content_all_ww import BL as WW
from feedcrawler.sites.content_shows_dj import DJ
from feedcrawler.sites.content_shows_sf import SF
from feedcrawler.sites.content_shows_sj import SJ
from feedcrawler.url import check_url
from feedcrawler.web import start

version = "v." + version.get_version()


def crawler(global_variables):
    internal.set_globals(global_variables)

    sys.stdout = Unbuffered(sys.stdout)
    logger = internal.logger
    disable_request_warnings(InsecureRequestWarning)

    ombi_first_launch = True
    crawltimes = FeedDb("crawltimes")
    feedcrawler = CrawlerConfig('FeedCrawler')

    try:
        clean_flaresolverr_sessions()
    except:
        pass

    arguments = docopt(__doc__, version='FeedCrawler')
    while True:
        try:
            if not internal.device or not is_device(internal.device):
                get_device()
            FeedDb('cached_requests').reset()
            FeedDb('cached_requests').cleanup()
            check_url()
            start_time = time.time()
            crawltimes.update_store("active", "True")
            crawltimes.update_store("start_time", start_time * 1000)
            logger.debug("--------Alle Suchfunktion gestartet.--------")
            ombi_string = ""
            ombi_results = ombi(ombi_first_launch)
            requested_movies = ombi_results[0]
            requested_shows = ombi_results[1]
            ombi_first_launch = False
            if requested_movies or requested_shows:
                ombi_string = u"Die Ombi-Suche lief für: "
                if requested_movies:
                    ombi_string = ombi_string + str(requested_movies) + " Filme"
                    if requested_shows:
                        ombi_string = ombi_string + " und "
                if requested_shows:
                    ombi_string = ombi_string + str(requested_shows) + " Serien"
            for task in search_pool():
                name = task._SITE
                try:
                    file = " - Liste: " + task.filename
                except AttributeError:
                    file = ""
                logger.debug("-----------Suchfunktion (" + name + file + ") gestartet!-----------")
                task.periodical_task()
                logger.debug("-----------Suchfunktion (" + name + file + ") ausgeführt!-----------")
            cached_requests = FeedDb('cached_requests').count()
            request_cache_string = u"Der FeedCrawler-Cache hat " + str(cached_requests) + " HTTP-Requests gespart!"
            end_time = time.time()
            total_time = end_time - start_time
            interval = int(feedcrawler.get('interval')) * 60
            random_range = random.randrange(0, interval // 4)
            wait = interval + random_range
            next_start = end_time + wait
            logger.debug(time.strftime("%Y-%m-%d %H:%M:%S") +
                         " - Alle Suchfunktion ausgeführt (Dauer: " + readable_time(
                total_time) + u")!")
            if ombi_string:
                logger.debug(time.strftime("%Y-%m-%d %H:%M:%S") + u" - " + ombi_string)
            logger.debug(time.strftime("%Y-%m-%d %H:%M:%S") + u" - " + request_cache_string)
            logger.debug("-----------Wartezeit bis zum nächsten Suchlauf: " + readable_time(wait) + '-----------')
            ombi_string = ""
            print(time.strftime("%Y-%m-%d %H:%M:%S") +
                  u" - Alle Suchfunktion ausgeführt (Dauer: " + readable_time(
                total_time) + u")!",
                  ombi_string + " - " + request_cache_string if ombi_string else request_cache_string)
            print(u"-----------Wartezeit bis zum nächsten Suchlauf: " + readable_time(wait) + '-----------')
            crawltimes.update_store("end_time", end_time * 1000)
            crawltimes.update_store("total_time", readable_time(total_time))
            crawltimes.update_store("next_start", next_start * 1000)
            crawltimes.update_store("active", "False")
            FeedDb('cached_requests').reset()
            FeedDb('cached_requests').cleanup()

            if arguments['--test_run']:
                logger.debug(u"-----------test_run beendet!-----------")
                print(u"-----------test_run beendet!-----------")
                return

            wait_chunks = wait // 10
            start_now_triggered = False
            while wait_chunks:
                time.sleep(10)
                if FeedDb('crawltimes').retrieve("startnow"):
                    FeedDb('crawltimes').delete("startnow")
                    start_now_triggered = True
                    break

                wait_chunks -= 1

            if start_now_triggered:
                logger.debug("----------Wartezeit vorzeitig beendet----------")
            else:
                logger.debug("-------------Wartezeit verstrichen-------------")
        except Exception:
            traceback.print_exc()
            time.sleep(10)


def web_server(global_variables):
    internal.set_globals(global_variables)
    start()


def crawldog(global_variables):
    internal.set_globals(global_variables)

    sys.stdout = Unbuffered(sys.stdout)
    disable_request_warnings(InsecureRequestWarning)

    crawljobs = CrawlerConfig('Crawljobs')
    autostart = crawljobs.get("autostart")
    db = FeedDb('crawldog')

    grabber_was_collecting = False

    while True:
        try:
            if not internal.device or not is_device(internal.device):
                get_device()

            myjd_packages = get_info()
            if myjd_packages:
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
                                            check = hoster_check([package], title[0], [0])
                                            remove = check[0]
                                            if remove:
                                                db.delete(title[0])

                                if packages_in_linkgrabber_decrypted:
                                    for package in packages_in_linkgrabber_decrypted:
                                        if title[0] in package['name'] or title[0].replace(".", " ") in package['name']:
                                            hoster_check([package], title[0], [0])
                                            episodes = FeedDb('episode_remover').retrieve(title[0])
                                            if episodes:
                                                try:
                                                    episodes = episodes.split("|")
                                                except:
                                                    episodes = [episodes]

                                                delete_linkids = []
                                                keep_linkids = []

                                                season_string = re.findall(r'.*(s\d{1,3}).*', title[0], re.IGNORECASE)[
                                                    0]
                                                if season_string:
                                                    if len(episodes) == 1:
                                                        episode_string = str(episodes[0])
                                                        if len(episodes[0]) == 1:
                                                            episode_string = "0" + episode_string
                                                        replace_string = season_string + "E" + episode_string
                                                        append_package_name = title[0].replace(season_string,
                                                                                               replace_string)
                                                    else:
                                                        episode_from_string = str(episodes[0])
                                                        if len(episodes[0]) == 1:
                                                            episode_from_string = "0" + episode_from_string
                                                        episode_to_string = str(episodes[-1])
                                                        if len(episodes[-1]) == 1:
                                                            episode_to_string = "0" + episode_to_string
                                                        replace_string = season_string + "E" + episode_from_string + "-E" + episode_to_string
                                                        append_package_name = title[0].replace(season_string,
                                                                                               replace_string)
                                                else:
                                                    append_package_name = title[0]

                                                for episode in episodes:
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
                                                                fname = fname.replace("hddl8", "").replace("dd51",
                                                                                                           "").replace(
                                                                    "264", "").replace("265", "")
                                                            fname_episode = "".join(
                                                                re.findall(r'\d+', fname.split(".part")[0]))
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

                                                        pos = 0
                                                        for keep_id in package['linkids']:
                                                            if str(episode) == str(fname_episodes[pos]):
                                                                keep_linkids.append(keep_id)
                                                            pos += 1

                                                for delete_id in package['linkids']:
                                                    if delete_id not in keep_linkids:
                                                        delete_linkids.append(delete_id)

                                                if delete_linkids:
                                                    delete_uuids = [package['uuid']]
                                                    FeedDb('episode_remover').delete(title[0])
                                                    remove_from_linkgrabber(delete_linkids, delete_uuids)
                                                    try:
                                                        new_myjd_packages = get_info()[4][1]
                                                        for new_myjd_package in new_myjd_packages:
                                                            if new_myjd_package["name"] == title[0]:
                                                                package = new_myjd_package
                                                                break
                                                    except:
                                                        pass
                                                rename_package_in_linkgrabber(package['uuid'], append_package_name)
                                            if autostart:
                                                move_to_downloads(package['linkids'],
                                                                  [package['uuid']])
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
                                                if retry_decrypt(package['linkids'],
                                                                 [package['uuid']],
                                                                 package['urls']):
                                                    db.delete(title[0])
                                                    db.store(title[0], 'retried')
                                            else:
                                                add_decrypt(package['name'], package['url'], "")
                                                remove_from_linkgrabber(package['linkids'],
                                                                        [package['uuid']])
                                                notify_list.append("[Click'n'Load notwendig] - " + title[0])
                                                print(u"[Click'n'Load notwendig] - " + title[0])
                                                db.delete(title[0])
                    else:
                        if not grabber_collecting:
                            db.reset()

                    if notify_list:
                        notify(notify_list)

                time.sleep(30)
            else:
                print(u"Scheinbar ist der JDownloader nicht erreichbar - bitte prüfen und neustarten!")
        except Exception:
            traceback.print_exc()
            time.sleep(30)


def search_pool():
    return [
        FX(filename='List_ContentAll_Movies_Regex'),
        FX(filename='IMDB'),
        FX(filename='List_ContentAll_Movies'),
        FX(filename='List_ContentAll_Seasons'),
        SJ(filename='List_ContentShows_Shows'),
        SJ(filename='List_ContentShows_Shows_Regex'),
        SJ(filename='List_ContentShows_Seasons_Regex'),
        SJ(filename='List_ContentAll_Seasons'),
        DJ(filename='List_CustomDJ_Documentaries'),
        DJ(filename='List_CustomDJ_Documentaries_Regex'),
        SF(filename='List_ContentShows_Shows'),
        SF(filename='List_ContentShows_Shows_Regex'),
        SF(filename='List_ContentShows_Seasons_Regex'),
        SF(filename='List_ContentAll_Seasons'),
        WW(filename='List_ContentAll_Movies_Regex'),
        WW(filename='IMDB'),
        WW(filename='List_ContentAll_Movies'),
        WW(filename='List_ContentAll_Seasons'),
        NK(filename='List_ContentAll_Movies_Regex'),
        NK(filename='IMDB'),
        NK(filename='List_ContentAll_Movies'),
        NK(filename='List_ContentAll_Seasons'),
        BY(filename='List_ContentAll_Movies_Regex'),
        BY(filename='IMDB'),
        BY(filename='List_ContentAll_Movies'),
        BY(filename='List_ContentAll_Seasons')
    ]


def main():
    arguments = docopt(__doc__, version='FeedCrawler')

    print(u"┌──────────────────────────────────────────────┐")
    print(u"  FeedCrawler " + version + " von RiX")
    print(u"  https://github.com/rix1337/FeedCrawler")
    print(u"└──────────────────────────────────────────────┘")

    if arguments['--docker']:
        configpath = "/config"
    else:
        configpath = common.configpath(arguments['--config'])

    internal.set_files(configpath)

    FeedDb('proxystatus').reset()
    FeedDb('normalstatus').reset()

    print(u"Nutze das Verzeichnis " + configpath + u" für Einstellungen/Logs")

    log_level = logging.__dict__[
        arguments['--log-level']] if arguments['--log-level'] in logging.__dict__ else logging.INFO

    internal.set_logger(log_level)

    hostnames = CrawlerConfig('Hostnames')

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
    internal.set_sites()
    for name in internal.sites:
        name = name.lower()
        hostname = clean_up_hostname(name, hostnames.get(name))
        if hostname:
            set_hostnames[name] = hostname

    if not arguments['--test_run'] and not set_hostnames:
        print(u'Keine Hostnamen in der FeedCrawler.ini gefunden! Beende FeedCrawler!')
        time.sleep(10)
        sys.exit(1)

    disable_request_warnings(InsecureRequestWarning)

    if not arguments['--test_run']:
        if not os.path.exists(internal.configfile):
            if arguments['--docker']:
                if arguments['--jd-user'] and arguments['--jd-pass']:
                    myjd.myjd_input(arguments['--port'], arguments['--jd-user'], arguments['--jd-pass'],
                                    arguments['--jd-device'])
            else:
                myjd.myjd_input(arguments['--port'], arguments['--jd-user'], arguments['--jd-pass'],
                                arguments['--jd-device'])
        else:
            feedcrawler = CrawlerConfig('FeedCrawler')
            user = feedcrawler.get('myjd_user')
            password = feedcrawler.get('myjd_pass')
            if user and password:
                if not get_device():
                    one_device = get_if_one_device(user, password)
                    if one_device:
                        print(u"Gerätename " + one_device + " automatisch ermittelt.")
                        feedcrawler.save('myjd_device', one_device)
                        get_device()
            else:
                myjd.myjd_input(arguments['--port'], arguments['--jd-user'], arguments['--jd-pass'],
                                arguments['--jd-device'])

    if not arguments['--test_run']:
        if not internal.device:
            print(u'My JDownloader Zugangsdaten fehlerhaft! Beende FeedCrawler!')
            time.sleep(10)
            sys.exit(1)
        else:
            print(u"Erfolgreich mit My JDownloader verbunden. Gerätename: " + internal.device.name)

    feedcrawler = CrawlerConfig('FeedCrawler')
    port = int(feedcrawler.get("port"))
    docker = False
    if arguments['--docker']:
        port = int('9090')
        docker = True
    elif arguments['--port']:
        port = int(arguments['--port'])

    if feedcrawler.get("prefix"):
        prefix = '/' + feedcrawler.get("prefix")
    else:
        prefix = ''
    local_address = 'http://' + common.check_ip() + ':' + str(port) + prefix
    if not arguments['--docker']:
        print(u'Der Webserver ist erreichbar unter ' + local_address)

    internal.set_connection_info(local_address, port, prefix, docker)

    if arguments['--keep-cdc']:
        print(u"CDC-Tabelle nicht geleert!")
    else:
        FeedDb('cdc').reset()

    global_variables = internal.get_globals()

    p = multiprocessing.Process(target=web_server, args=(global_variables,))
    p.start()

    if not arguments['--test_run']:
        c = multiprocessing.Process(target=crawler, args=(global_variables,))
        c.start()

        w = multiprocessing.Process(target=crawldog, args=(global_variables,))
        w.start()

        print(u'Drücke [Strg] + [C] zum Beenden')

        def signal_handler():
            print(u'Beende FeedCrawler...')
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
        crawler(global_variables)
        p.terminate()
        sys.exit(0)


if __name__ == "__main__":
    main()
