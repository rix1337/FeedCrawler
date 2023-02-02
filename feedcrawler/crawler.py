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

from feedcrawler.jobs.feed_search import crawler
from feedcrawler.jobs.package_watcher import watch_packages
from feedcrawler.providers import shared_state
from feedcrawler.providers import version
from feedcrawler.providers.common_functions import check_ip
from feedcrawler.providers.common_functions import configpath
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.myjd_connection import get_device
from feedcrawler.providers.myjd_connection import get_if_one_device
from feedcrawler.providers.myjd_connection import myjd_input
from feedcrawler.providers.sqlite_database import FeedDb
from feedcrawler.web_interface.web_server import web_server

version = "v." + version.get_version()


def start_feedcrawler():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-level", help="Legt fest, wie genau geloggt wird (INFO, DEBUG)")
    parser.add_argument("--config", help="Legt den Ablageort für Einstellungen und Logs fest")
    parser.add_argument("--port", help="Legt den Port des Webservers fest")
    parser.add_argument("--jd-user", help="Legt den Nutzernamen für My JDownloader fest")
    parser.add_argument("--jd-pass", help="Legt das Passwort für My JDownloader fest")
    parser.add_argument("--jd-device", help="Legt den Gerätenamen für My JDownloader fest")
    parser.add_argument("--keep-cdc", action='store_true',
                        help="Vergisst 'Feed ab hier bereits gecrawlt' nicht vor dem ersten Suchlauf")
    parser.add_argument("--remove_jf_time", action='store_true',
                        help="Leere die Zeit des letzten SJ/DJ/SF/FF-Laufes vor dem ersten Suchlauf")
    parser.add_argument("--test_run", action='store_true', help="Intern: Führt einen Testlauf durch")
    parser.add_argument("--docker", action='store_true', help="Intern: Sperre Pfad und Port auf Docker-Standardwerte")
    arguments = parser.parse_args()

    print(u"┌──────────────────────────────────────────────┐")
    print(u"  FeedCrawler " + version + " von RiX")
    print(u"  https://github.com/rix1337/FeedCrawler")
    print(u"└──────────────────────────────────────────────┘")

    if arguments.docker:
        config_path = "/config"
    else:
        config_path = configpath(arguments.config)

    shared_state.set_files(config_path)

    print(u"Nutze das Verzeichnis " + config_path + u" für Einstellungen/Logs")

    log_level = logging.__dict__[
        arguments.log_level] if arguments.log_level in logging.__dict__ else logging.INFO

    shared_state.set_logger(log_level)

    hostnames = CrawlerConfig('Hostnames')

    def clean_up_hostname(host, string):
        if string and '/' in string:
            string = string.replace('https://', '').replace('http://', '')
            string = re.findall(r'([a-z-.]*\.[a-z]*)', string)[0]
            hostnames.save(host, string)
        if string and re.match(r'.*[A-Z].*', string):
            hostnames.save(host, string.lower())
        if string:
            print(u'Hostname für ' + host.upper() + ": " + string)
        else:
            print(u'Hostname für ' + host.upper() + ': Nicht gesetzt!')
        return string

    set_hostnames = {}
    shared_state.set_sites()
    for name in shared_state.sites:
        name = name.lower()
        hostname = clean_up_hostname(name, hostnames.get(name))
        if hostname:
            set_hostnames[name] = hostname

    if not arguments.test_run and not set_hostnames:
        print(u'Keine Hostnamen in der FeedCrawler.ini gefunden! Beende FeedCrawler!')
        time.sleep(10)
        sys.exit(1)

    FeedDb('cached_internals').delete("device")

    if not arguments.test_run:
        if not os.path.exists(shared_state.configfile):
            if arguments.docker:
                if arguments.jd_user and arguments.jd_pass:
                    myjd_input(arguments.port, arguments.jd_user, arguments.jd_pass, arguments.jd_device)
            else:
                myjd_input(arguments.port, arguments.jd_user, arguments.jd_pass, arguments.jd_device)
        else:
            feedcrawler = CrawlerConfig('FeedCrawler')
            user = feedcrawler.get('myjd_user')
            password = feedcrawler.get('myjd_pass')
            if user and password:
                if not get_device():
                    device_set = feedcrawler.get('myjd_device')
                    if not device_set:
                        one_device = get_if_one_device(user, password)
                        if one_device:
                            print(u"Gerätename " + one_device + " automatisch ermittelt.")
                            feedcrawler.save('myjd_device', one_device)
                            get_device()
            else:
                myjd_input(arguments.port, arguments.jd_user, arguments.jd_pass,
                           arguments.jd_device)

    if not arguments.test_run:
        if shared_state.device and shared_state.device.name:
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
                    print(u"Gerätename " + one_device + " automatisch ermittelt.")
                    feedcrawler.save('myjd_device', one_device)
                    get_device()
                    success = shared_state.device and shared_state.device.name
            if not success:
                i = 0
                while i < 10:
                    i += 1
                    print(
                        u"Verbindungsversuch %s mit My JDownloader gescheitert. Gerätename: %s" % (i, device_name))
                    time.sleep(60)
                    get_device()
                    success = shared_state.device and shared_state.device.name
                    if success:
                        break
        if success:
            print(u"Erfolgreich mit My JDownloader verbunden. Gerätename: " + shared_state.device.name)
        else:
            print(u'My JDownloader Zugangsversuche nicht erfolgreich! Beende FeedCrawler!')
            sys.exit(1)

    feedcrawler = CrawlerConfig('FeedCrawler')
    port = int(feedcrawler.get("port"))
    docker = False
    if arguments.docker:
        port = int('9090')
        docker = True
    elif arguments.port:
        port = int(arguments.port)

    if feedcrawler.get("prefix"):
        prefix = '/' + feedcrawler.get("prefix")
    else:
        prefix = ''
    local_address = 'http://' + check_ip() + ':' + str(port) + prefix
    if not arguments.docker:
        print(u'Der Webserver ist erreichbar unter ' + local_address)

    shared_state.set_connection_info(local_address, port, prefix, docker)

    if arguments.keep_cdc:
        print(u"CDC-Tabelle nicht geleert!")
    else:
        FeedDb('cdc').reset()

    global_variables = shared_state.get_globals()

    p = multiprocessing.Process(target=web_server, args=(global_variables,))
    p.start()

    if not arguments.test_run:
        c = multiprocessing.Process(target=crawler,
                                    args=(global_variables, arguments.remove_jf_time, False,))
        c.start()

        w = multiprocessing.Process(target=watch_packages, args=(global_variables,))
        w.start()

        def signal_handler(sig, frame):
            print(u'Beende FeedCrawler...')
            p.terminate()
            c.terminate()
            w.terminate()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        print(u'Drücke [Strg] + [C] zum Beenden')
        try:
            while True:
                signal.pause()
        except AttributeError:
            while True:
                time.sleep(1)
    else:
        crawler(global_variables, arguments.remove_jf_time, True)
        p.terminate()
        sys.exit(0)


if __name__ == "__main__":
    start_feedcrawler()
