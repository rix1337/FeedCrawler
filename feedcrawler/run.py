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
from feedcrawler.providers.myjd_connection import set_device_from_config
from feedcrawler.providers.sqlite_database import remove_redundant_db_tables
from feedcrawler.web_interface.web_server import hostnames_config, myjd_config, web_server

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
        parser.add_argument("--delay", help="Verzögere Suchlauf nach Start um ganze Zahl in Sekunden")
        parser.add_argument("--no-gui", action='store_true', help="Startet FeedCrawler ohne GUI")
        arguments = parser.parse_args()

        shared_state.set_initial_values(arguments.no_gui)

        if shared_state.values["gui"]:
            window, icon = gui.create_main_window()
            sys.stdout = gui.PrintToConsoleAndGui(window)
        else:
            sys.stdout = Unbuffered(sys.stdout)

        print(f"""
        ┌──────────────────────────────────────────────┐
          FeedCrawler {version} von RiX
          https://github.com/rix1337/FeedCrawler
        └──────────────────────────────────────────────┘
        """)

        if os.environ.get('DOCKER'):
            config_path = "/config"
        elif os.environ.get('GITHUB_ACTION_PR'):
            config_path = "/home/runner/work/_temp/_github_home"
        else:
            config_path = configpath(arguments.config)

        shared_state.set_files(config_path)

        print(f'Nutze das Verzeichnis "{config_path}" für Einstellungen/Logs')

        log_level = logging.__dict__[
            arguments.log_level] if arguments.log_level in logging.__dict__ else logging.INFO

        shared_state.update("log_level", log_level)
        shared_state.set_logger()

        local_address = 'http://' + check_ip()
        port = int('9090')
        if arguments.port:
            port = int(arguments.port)

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

        if not os.environ.get('GITHUB_ACTION_PR') and not set_hostnames:
            if shared_state.values["gui"]:
                gui.no_hostnames_gui(shared_state.values["configfile"])
                sys.exit(1)
            else:
                if not hostnames_config(port, local_address):
                    print('Keine Hostnamen in der FeedCrawler.ini gefunden! Beende FeedCrawler!')
                    time.sleep(10)
                    sys.exit(1)

        if not os.environ.get('GITHUB_ACTION_PR'):
            set_device_from_config()
            if not shared_state.get_device() and not shared_state.get_device().name:
                myjd_config(port, local_address)

            connection_established = False

            feedcrawler = CrawlerConfig('FeedCrawler')
            device = feedcrawler.get('myjd_device')

            if device:
                shared_state.set_device(device)
                connection_established = shared_state.get_device() and shared_state.get_device().name
                if not connection_established:
                    i = 0
                    while i < 10:
                        i += 1
                        print(f'Verbindungsversuch {i} mit My JDownloader gescheitert. Gerätename: "{device}"')
                        time.sleep(60)
                        set_device_from_config()
                        connection_established = shared_state.get_device() and shared_state.get_device().name
                        if connection_established:
                            break

            if connection_established:
                print(f'Erfolgreich mit My JDownloader verbunden. Gerätename: "{shared_state.get_device().name}"')
            else:
                print('My JDownloader Zugangsversuche nicht erfolgreich! Beende FeedCrawler!')
                sys.exit(1)

        feedcrawler = CrawlerConfig('FeedCrawler')
        if not os.environ.get('DOCKER') and not arguments.port:
            port = int(feedcrawler.get("port"))

        if feedcrawler.get("prefix"):
            prefix = '/' + feedcrawler.get("prefix")
        else:
            prefix = ''

        if not os.environ.get('DOCKER'):
            print(f'Der Webserver ist erreichbar unter "{local_address}:{port}{prefix}"')

        shared_state.set_connection_info(local_address, port, prefix)

        CrawlerConfig("FeedCrawler").remove_redundant_entries()
        remove_redundant_db_tables(shared_state.values["dbfile"])

        process_web_server = multiprocessing.Process(target=web_server, args=(shared_state_dict, shared_state_lock,))
        process_web_server.start()

        if arguments.delay:
            delay = int(arguments.delay)
            print(f"Verzögere den ersten Suchlauf um {delay} Sekunden")
            time.sleep(delay)

        if not os.environ.get('GITHUB_ACTION_PR'):
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
