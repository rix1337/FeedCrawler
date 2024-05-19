# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul initialisiert die globalen Parameter und starte alle parallel laufenden Threads des FeedCrawlers.

import argparse
import logging
import multiprocessing
import os
import re
import signal
import sys
import time

from feedcrawler.jobs.feed_search import feed_crawler
from feedcrawler.jobs.package_watcher import watch_packages
from feedcrawler.providers import gui
from feedcrawler.providers import shared_state
from feedcrawler.providers import version
from feedcrawler.providers.common_functions import Unbuffered, check_ip, configpath
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.myjd_connection import set_device_from_config, get_if_one_device, myjd_input
from feedcrawler.providers.sqlite_database import FeedDb, remove_redundant_db_tables
from feedcrawler.web_interface.web_server import web_server

version = "v." + version.get_version()


def main():
    with multiprocessing.Manager() as manager:
        shared_state_dict = manager.dict()
        shared_state_lock = manager.Lock()
        shared_state.set_state(shared_state_dict, shared_state_lock)

        parser = argparse.ArgumentParser()
        parser.add_argument("--log-level", help="Legt fest, wie genau geloggt wird (INFO, DEBUG)")
        parser.add_argument("--config", help="Legt den Ablageort für Einstellungen und Logs fest")
        parser.add_argument("--port", help="Legt den Port des Webservers fest")
        parser.add_argument("--jd-user", help="Legt den Nutzernamen für My JDownloader fest")
        parser.add_argument("--jd-pass", help="Legt das Passwort für My JDownloader fest")
        parser.add_argument("--jd-device", help="Legt den Gerätenamen für My JDownloader fest")
        parser.add_argument("--delay", help="Verzögere Suchlauf nach Start um ganze Zahl in Sekunden")
        parser.add_argument("--no-gui", action='store_true', help="Startet FeedCrawler ohne GUI")
        parser.add_argument("--keep-cdc", action='store_true',
                            help="Intern: Vergisst 'Feed ab hier bereits gecrawlt' nicht vor dem ersten Suchlauf")
        parser.add_argument("--remove_cloudflare_time", action='store_true',
                            help="Intern: Leere die Zeit des letzten Cloudflare-Umgehungs-Laufes vor dem ersten Suchlauf")
        parser.add_argument("--test_run", action='store_true', help="Intern: Führt einen Testlauf durch")
        parser.add_argument("--docker", action='store_true',
                            help="Intern: Sperre Pfad und Port auf Docker-Standardwerte")
        arguments = parser.parse_args()

        shared_state.set_initial_values(arguments.docker,
                                        arguments.no_gui,
                                        arguments.test_run,
                                        arguments.remove_cloudflare_time
                                        )

        if shared_state.values["gui"]:
            window, icon = gui.create_main_window()
            sys.stdout = gui.PrintToConsoleAndGui(window)
        else:
            sys.stdout = Unbuffered(sys.stdout)

        print("┌──────────────────────────────────────────────┐")
        print("  FeedCrawler " + version + " von RiX")
        print("  https://github.com/rix1337/FeedCrawler")
        print("└──────────────────────────────────────────────┘")

        if shared_state.values["docker"]:
            config_path = "/config"
        else:
            config_path = configpath(arguments.config)

        shared_state.set_files(config_path)

        print('Nutze das Verzeichnis "' + config_path + '" für Einstellungen/Logs')

        log_level = logging.__dict__[
            arguments.log_level] if arguments.log_level in logging.__dict__ else logging.INFO

        shared_state.update("log_level", log_level)
        shared_state.set_logger()

        hostnames = CrawlerConfig('Hostnames')

        def clean_up_hostname(host, string):
            if string and '/' in string:
                string = string.replace('https://', '').replace('http://', '')
                string = re.findall(r'([a-z-.]*\.[a-z]*)', string)[0]
                hostnames.save(host, string)
            if string and re.match(r'.*[A-Z].*', string):
                hostnames.save(host, string.lower())
            if string:
                print('Hostname für ' + host.upper() + ": " + string)
            return string

        set_hostnames = {}
        shared_state.set_sites()
        for name in shared_state.values["sites"]:
            name = name.lower()
            hostname = clean_up_hostname(name, hostnames.get(name))
            if hostname:
                set_hostnames[name] = hostname

        if not shared_state.values["test_run"] and not set_hostnames:
            if shared_state.values["gui"]:
                gui.no_hostnames_gui(shared_state.values["configfile"])
            else:
                print('Keine Hostnamen in der FeedCrawler.ini gefunden! Beende FeedCrawler!')
                time.sleep(10)
            sys.exit(1)

        if not shared_state.values["test_run"]:
            if not os.path.exists(shared_state.values["configfile"]):
                if shared_state.values["docker"]:
                    if arguments.jd_user and arguments.jd_pass:
                        myjd_input(arguments.port, arguments.jd_user, arguments.jd_pass, arguments.jd_device)
                else:
                    myjd_input(arguments.port, arguments.jd_user, arguments.jd_pass, arguments.jd_device)
            else:
                feedcrawler = CrawlerConfig('FeedCrawler')
                user = feedcrawler.get('myjd_user')
                password = feedcrawler.get('myjd_pass')
                if user and password:
                    if not set_device_from_config():
                        device_set = feedcrawler.get('myjd_device')
                        if not device_set:
                            one_device = get_if_one_device(user, password)
                            if one_device:
                                print('Gerätename "' + one_device + '" automatisch ermittelt.')
                                feedcrawler.save('myjd_device', one_device)
                                set_device_from_config()
                else:
                    myjd_input(arguments.port, arguments.jd_user, arguments.jd_pass,
                               arguments.jd_device)

        if not shared_state.values["test_run"]:
            if shared_state.get_device() and shared_state.get_device().name:
                success = True
            else:
                success = False
                feedcrawler = CrawlerConfig('FeedCrawler')

                device_name = feedcrawler.get('myjd_device')
                if not device_name:
                    user = feedcrawler.get('myjd_user')
                    password = feedcrawler.get('myjd_pass')
                    one_device = get_if_one_device(user, password)
                    if one_device:
                        print('Gerätename "' + one_device + '" automatisch ermittelt.')
                        feedcrawler.save('myjd_device', one_device)
                        set_device_from_config()
                        success = shared_state.get_device() and shared_state.get_device().name
                if not success:
                    i = 0
                    while i < 10:
                        i += 1
                        print(
                            'Verbindungsversuch %s mit My JDownloader gescheitert. Gerätename: "%s"' % (
                                i, device_name))
                        time.sleep(60)
                        set_device_from_config()
                        success = shared_state.get_device() and shared_state.get_device().name
                        if success:
                            break
            if success:
                print('Erfolgreich mit My JDownloader verbunden. Gerätename: "' + shared_state.get_device().name + '"')
            else:
                print('My JDownloader Zugangsversuche nicht erfolgreich! Beende FeedCrawler!')
                sys.exit(1)

        feedcrawler = CrawlerConfig('FeedCrawler')
        port = int(feedcrawler.get("port"))
        docker = False
        if shared_state.values["docker"]:
            port = int('9090')
            docker = True
        elif arguments.port:
            port = int(arguments.port)

        if feedcrawler.get("prefix"):
            prefix = '/' + feedcrawler.get("prefix")
        else:
            prefix = ''
        local_address = 'http://' + check_ip() + ':' + str(port) + prefix
        if not shared_state.values["docker"]:
            print('Der Webserver ist erreichbar unter "' + local_address + '"')

        shared_state.set_connection_info(local_address, port, prefix, docker)

        CrawlerConfig("FeedCrawler").remove_redundant_entries()
        remove_redundant_db_tables(shared_state.values["dbfile"])

        if arguments.keep_cdc:
            print("CDC-Tabelle nicht geleert!")
        else:
            FeedDb('cdc').reset()

        process_web_server = multiprocessing.Process(target=web_server, args=(shared_state_dict, shared_state_lock,))
        process_web_server.start()

        if arguments.delay:
            delay = int(arguments.delay)
            print("Verzögere den ersten Suchlauf um " + str(delay) + " Sekunden")
            time.sleep(delay)

        if not shared_state.values["test_run"]:
            process_feed_crawler = multiprocessing.Process(target=feed_crawler,
                                                           args=(shared_state_dict, shared_state_lock,))
            process_feed_crawler.start()

            process_watch_packages = multiprocessing.Process(target=watch_packages,
                                                             args=(shared_state_dict, shared_state_lock,))
            process_watch_packages.start()

            if shared_state.values["gui"]:
                gui.main_gui(window, icon, shared_state_dict, shared_state_lock)

                sys.stdout = sys.__stdout__
                process_web_server.terminate()
                process_feed_crawler.terminate()
                process_watch_packages.terminate()
                sys.exit(0)

            else:  # regular console
                def signal_handler(sig, frame):
                    process_web_server.terminate()
                    process_feed_crawler.terminate()
                    process_watch_packages.terminate()
                    sys.exit(0)

                signal.signal(signal.SIGINT, signal_handler)
                print('Drücke [Strg] + [C] zum Beenden')
                try:
                    while True:
                        signal.pause()
                except AttributeError:
                    while True:
                        time.sleep(1)
        else:
            feed_crawler(shared_state_dict, shared_state_lock)
            process_web_server.terminate()
            sys.exit(0)


if __name__ == "__main__":
    main()
