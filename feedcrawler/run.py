# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul initialisiert die globalen Parameter und starte alle parallel laufenden Threads des FeedCrawlers.

import argparse
import logging
import multiprocessing
import os
import signal
import sys
import tempfile
import time

from feedcrawler.jobs.feed_search import feed_crawler
from feedcrawler.jobs.package_watcher import watch_packages
from feedcrawler.providers import gui
from feedcrawler.providers import shared_state
from feedcrawler.providers import version
from feedcrawler.providers.common_functions import Unbuffered, check_ip, get_clean_hostnames
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.myjd_connection import set_device_from_config
from feedcrawler.providers.sqlite_database import remove_redundant_db_tables
from feedcrawler.web_interface.feedcrawler_api import web_server
from feedcrawler.web_interface.feedcrawler_setup import hostnames_config, myjd_config, path_config

version = f"v.{version.get_version()}"


def main():
    with multiprocessing.Manager() as manager:
        shared_state_dict = manager.dict()
        shared_state_lock = manager.Lock()
        shared_state.set_state(shared_state_dict, shared_state_lock)

        parser = argparse.ArgumentParser()
        parser.add_argument("--log-level", help="Legt fest, wie genau geloggt wird (INFO, DEBUG)")
        parser.add_argument("--port", help="Legt den Port des Webservers fest")
        parser.add_argument("--delay", help="Verzögere Suchlauf nach Start um ganze Zahl in Sekunden")
        arguments = parser.parse_args()

        shared_state.set_initial_values()

        if shared_state.values["gui"]:
            window = gui.create_main_window()
            sys.stdout = gui.PrintToConsoleAndGui(window)
        else:
            sys.stdout = Unbuffered(sys.stdout)

        print(f"""┌──────────────────────────────────────────────┐
  FeedCrawler {version} von RiX
  https://github.com/rix1337/FeedCrawler
└──────────────────────────────────────────────┘""")

        local_address = f'http://{check_ip()}'
        port = int('9090')
        if arguments.port:
            port = int(arguments.port)

        if os.environ.get('DOCKER'):
            config_path = "/config"
            local_address = f'http://[HOST_IP]'
        elif os.environ.get('GITHUB_ACTION_PR'):
            config_path = "/home/runner/work/_temp/feedcrawler"
        else:
            config_path_file = "FeedCrawler.conf"
            if not os.path.exists(config_path_file):
                path_config(port, local_address, shared_state)
            with open(config_path_file, "r") as f:
                config_path = f.readline()

        os.makedirs(config_path, exist_ok=True)

        try:
            temp_file = tempfile.TemporaryFile(dir=config_path)
            temp_file.close()
        except Exception as e:
            print(f'Auf das Verzeichnis "{config_path}" konnte nicht zugegriffen werden: {e}"'
                  f'Beende FeedCrawler!')
            sys.exit(1)

        shared_state.set_files(config_path)

        print(f'Nutze das Verzeichnis "{config_path}" für Einstellungen/Logs')

        log_level = logging.DEBUG if arguments.log_level == "DEBUG" else logging.INFO

        shared_state.update("log_level", log_level)
        shared_state.set_logger()
        shared_state.set_sites()

        if not os.environ.get('GITHUB_ACTION_PR') and not get_clean_hostnames(shared_state):
            hostnames_config(port, local_address, shared_state)
            get_clean_hostnames(shared_state)

        if not os.environ.get('GITHUB_ACTION_PR'):
            feedcrawler = CrawlerConfig('FeedCrawler')
            user = feedcrawler.get('myjd_user')
            password = feedcrawler.get('myjd_pass')
            device = feedcrawler.get('myjd_device')

            if user and password and device:
                set_device_from_config()
            else:
                myjd_config(port, local_address, shared_state)

        process_jdownloader = multiprocessing.Process(target=jdownloader_connection,
                                                      args=(shared_state_dict, shared_state_lock))
        process_jdownloader.start()

        feedcrawler = CrawlerConfig('FeedCrawler')
        if not os.environ.get('DOCKER') and not arguments.port:
            port = int(feedcrawler.get("port"))

        if feedcrawler.get("prefix"):
            prefix = f"/{feedcrawler.get('prefix')}"
        else:
            prefix = ''

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
                gui.main_gui(window, shared_state_dict, shared_state_lock)

                sys.stdout = sys.__stdout__
                process_jdownloader.terminate()
                process_web_server.terminate()
                process_feed_crawler.terminate()
                process_watch_packages.terminate()
                sys.exit(0)

            else:  # regular console
                def signal_handler(sig, frame):
                    process_jdownloader.terminate()
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


def jdownloader_connection(shared_state_dict, shared_state_lock):
    shared_state.set_state(shared_state_dict, shared_state_lock)

    shared_state.set_device_from_config()
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


if __name__ == "__main__":
    main()
