# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul ist das Herzstück des FeedCrawlers. Es durchsucht zyklisch die Feeds der konfigurierten Hostnamen.

import random
import sys
import time
import traceback

from feedcrawler.external_sites.feed_search.sites.content_all_by import BL as BY
from feedcrawler.external_sites.feed_search.sites.content_all_dw import BL as DW
from feedcrawler.external_sites.feed_search.sites.content_all_ff import BL as FF
from feedcrawler.external_sites.feed_search.sites.content_all_fx import BL as FX
from feedcrawler.external_sites.feed_search.sites.content_all_hw import BL as HW
from feedcrawler.external_sites.feed_search.sites.content_all_nk import BL as NK
from feedcrawler.external_sites.feed_search.sites.content_all_nx import BL as NX
from feedcrawler.external_sites.feed_search.sites.content_all_ww import BL as WW
from feedcrawler.external_sites.feed_search.sites.content_custom_dd import DD
from feedcrawler.external_sites.feed_search.sites.content_shows_dj import DJ
from feedcrawler.external_sites.feed_search.sites.content_shows_sf import SF
from feedcrawler.external_sites.feed_search.sites.content_shows_sj import SJ
from feedcrawler.external_tools.ombi_api import ombi_search
from feedcrawler.external_tools.overseerr_api import overseerr_search
from feedcrawler.external_tools.plex_api import plex_search
from feedcrawler.providers import shared_state
from feedcrawler.providers.common_functions import Unbuffered, is_device, readable_time
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.http_requests.flaresolverr_handler import clean_flaresolverr_session
from feedcrawler.providers.myjd_connection import get_device
from feedcrawler.providers.myjd_connection import get_info
from feedcrawler.providers.myjd_connection import jdownloader_update
from feedcrawler.providers.sqlite_database import FeedDb
from feedcrawler.providers.url_functions import check_url


def search_pool():
    return [
        FX(filename='IMDb'),
        FX(filename='List_ContentAll_Movies'),
        FX(filename='List_ContentAll_Movies_Regex'),
        FX(filename='List_ContentAll_Seasons'),
        SF(filename='List_ContentShows_Shows'),
        SF(filename='List_ContentShows_Shows_Regex'),
        SF(filename='List_ContentShows_Seasons_Regex'),
        SF(filename='List_ContentAll_Seasons'),
        DW(filename='IMDb'),
        DW(filename='List_ContentAll_Movies'),
        DW(filename='List_ContentAll_Movies_Regex'),
        DW(filename='List_ContentAll_Seasons'),
        HW(filename='IMDb'),
        HW(filename='List_ContentAll_Movies'),
        HW(filename='List_ContentAll_Movies_Regex'),
        HW(filename='List_ContentAll_Seasons'),
        FF(filename='IMDb'),
        FF(filename='List_ContentAll_Movies'),
        FF(filename='List_ContentAll_Movies_Regex'),
        FF(filename='List_ContentAll_Seasons'),
        BY(filename='IMDb'),
        BY(filename='List_ContentAll_Movies'),
        BY(filename='List_ContentAll_Movies_Regex'),
        BY(filename='List_ContentAll_Seasons'),
        NK(filename='IMDb'),
        NK(filename='List_ContentAll_Movies'),
        NK(filename='List_ContentAll_Movies_Regex'),
        NK(filename='List_ContentAll_Seasons'),
        NX(filename='IMDb'),
        NX(filename='List_ContentAll_Movies'),
        NX(filename='List_ContentAll_Movies_Regex'),
        NX(filename='List_ContentAll_Seasons'),
        WW(filename='List_ContentAll_Movies_Regex'),
        WW(filename='IMDb'),
        WW(filename='List_ContentAll_Movies'),
        WW(filename='List_ContentAll_Seasons'),
        SJ(filename='List_ContentShows_Shows'),
        SJ(filename='List_ContentShows_Shows_Regex'),
        SJ(filename='List_ContentShows_Seasons_Regex'),
        SJ(filename='List_ContentAll_Seasons'),
        DJ(filename='List_CustomDJ_Documentaries'),
        DJ(filename='List_CustomDJ_Documentaries_Regex'),
        DD(filename='List_CustomDD_Feeds')
    ]


def crawler(global_variables, remove_jf_time, test_run):
    shared_state.set_globals(global_variables)

    sys.stdout = Unbuffered(sys.stdout)
    logger = shared_state.logger

    request_management_first_run = True
    crawltimes = FeedDb("crawltimes")
    feedcrawler = CrawlerConfig('FeedCrawler')

    try:
        clean_flaresolverr_session()
    except:
        pass

    if remove_jf_time:
        logger.debug(u"-----------Entferne Zeitpunkt des letzten SJ/DJ/SF/FF-Suchlaufes!-----------")
        print(u"-----------Entferne Zeitpunkt des letzten SJ/DJ/SF/FF-Suchlaufes!-----------")
        FeedDb('crawltimes').delete("last_jf_run")

    while True:
        try:
            if not shared_state.device or not is_device(shared_state.device):
                get_device()
            FeedDb('cached_requests').reset()
            FeedDb('cached_requests').cleanup()
            start_time = time.time()
            check_url(start_time)
            crawltimes.update_store("active", "True")
            crawltimes.update_store("start_time", start_time * 1000)
            logger.debug("-----------Alle Suchläufe gestartet.-----------")

            # Connect to and run request management services

            plex_string = ""
            try:
                plex_results = plex_search(request_management_first_run)
                requested_movies = plex_results[0]
                requested_shows = plex_results[1]
                request_management_first_run = False
                if requested_movies or requested_shows:
                    plex_string = u"Die Plex-Suche lief für: "
                    if requested_movies:
                        plex_string = plex_string + str(requested_movies) + " Filme"
                        if requested_shows:
                            plex_string = plex_string + " und "
                    if requested_shows:
                        plex_string = plex_string + str(requested_shows) + " Serien"
            except Exception as e:
                print(u"Fehler bei der Plex-Suche: " + str(e))

            overseerr_string = ""
            try:
                overseerr_results = overseerr_search(request_management_first_run)
                requested_movies = overseerr_results[0]
                requested_shows = overseerr_results[1]
                request_management_first_run = False
                if requested_movies or requested_shows:
                    overseerr_string = u"Die Overseerr-Suche lief für: "
                    if requested_movies:
                        overseerr_string = overseerr_string + str(requested_movies) + " Filme"
                        if requested_shows:
                            overseerr_string = overseerr_string + " und "
                    if requested_shows:
                        overseerr_string = overseerr_string + str(requested_shows) + " Serien"
            except Exception as e:
                print(u"Fehler bei der Overseerr-Suche: " + str(e))
            ombi_string = ""

            try:
                ombi_results = ombi_search(request_management_first_run)
                requested_movies = ombi_results[0]
                requested_shows = ombi_results[1]
                request_management_first_run = False
                if requested_movies or requested_shows:
                    ombi_string = u"Die Ombi-Suche lief für: "
                    if requested_movies:
                        ombi_string = ombi_string + str(requested_movies) + " Filme"
                        if requested_shows:
                            ombi_string = ombi_string + " und "
                    if requested_shows:
                        ombi_string = ombi_string + str(requested_shows) + " Serien"
            except Exception as e:
                print(u"Fehler bei der Ombi-Suche: " + str(e))

            # Start feed search
            current_jf_run = False
            last_jf_run = FeedDb('crawltimes').retrieve("last_jf_run")
            for task in search_pool():
                name = task._SITE
                try:
                    file = " - Liste: " + task.filename
                except AttributeError:
                    file = ""
                if name in ["SJ", "DJ", "SF", "FF"]:
                    jf_wait_time = int(CrawlerConfig('CustomJF').get('wait_time'))
                    if last_jf_run and start_time < float(last_jf_run) // 1000 + jf_wait_time * 60 * 60:
                        logger.debug(
                            "-----------Wartezeit bei " + name + " (6h) nicht verstrichen - überspringe Suchlauf!-----------")
                        continue
                    else:
                        current_jf_run = time.time()
                        FeedDb('site_status').delete("SF_FF")
                logger.debug("-----------Suchlauf (" + name + file + ") gestartet!-----------")
                try:
                    task.periodical_task()
                except Exception as e:
                    print(u"Fehler bei der Feed-Suche: " + str(e))
                logger.debug("-----------Suchlauf (" + name + file + ") ausgeführt!-----------")

            # Finish feed search and log results
            if current_jf_run:
                crawltimes.update_store("last_jf_run", current_jf_run * 1000)
            cached_requests = FeedDb('cached_requests').count()
            request_cache_string = u"Der FeedCrawler-Cache hat " + str(cached_requests) + " HTTP-Requests gespart!"
            end_time = time.time()
            total_time = end_time - start_time
            interval = int(feedcrawler.get('interval')) * 60
            random_range = random.randrange(0, interval // 4)
            wait = interval + random_range
            next_start = end_time + wait
            logger.debug(time.strftime("%Y-%m-%d %H:%M:%S") +
                         " - Alle Suchläufe ausgeführt (Dauer: " + readable_time(
                total_time) + u")!")
            print(time.strftime("%Y-%m-%d %H:%M:%S") +
                  u" - Alle Suchläufe ausgeführt (Dauer: " + readable_time(
                total_time) + u")!")

            if plex_string:
                logger.debug(time.strftime("%Y-%m-%d %H:%M:%S") + u" - " + plex_string)
                print(time.strftime("%Y-%m-%d %H:%M:%S") + u" - " + plex_string)
            if overseerr_string:
                logger.debug(time.strftime("%Y-%m-%d %H:%M:%S") + u" - " + overseerr_string)
                print(time.strftime("%Y-%m-%d %H:%M:%S") + u" - " + overseerr_string)
            if ombi_string:
                logger.debug(time.strftime("%Y-%m-%d %H:%M:%S") + u" - " + ombi_string)
                print(time.strftime("%Y-%m-%d %H:%M:%S") + u" - " + ombi_string)

            logger.debug(time.strftime("%Y-%m-%d %H:%M:%S") + u" - " + request_cache_string)
            logger.debug("-----------Wartezeit bis zum nächsten Suchlauf: " + readable_time(wait) + '-----------')
            print(u"-----------Wartezeit bis zum nächsten Suchlauf: " + readable_time(wait) + '-----------')
            crawltimes.update_store("end_time", end_time * 1000)
            crawltimes.update_store("total_time", readable_time(total_time))
            crawltimes.update_store("next_start", next_start * 1000)
            crawltimes.update_store("active", "False")
            FeedDb('cached_requests').reset()
            FeedDb('cached_requests').cleanup()

            myjd_auto_update = feedcrawler.get("myjd_auto_update")
            if myjd_auto_update:
                myjd_infos = get_info()
                myjd_state = myjd_infos[1]
                myjd_grabber_collecting = myjd_infos[2]
                myjd_update_ready = myjd_infos[3]
                myjd_packages = myjd_infos[4]
                if (myjd_state == "IDLE" or not myjd_packages[0]) and (
                        not myjd_grabber_collecting and myjd_update_ready):
                    print(
                        "JDownloader Update steht bereit und JDownloader ist inaktiv.\nFühre Update durch und starte JDownloader neu...")
                    jdownloader_update()
                elif myjd_update_ready:
                    print(
                        "JDownloader Update steht bereit, aber JDownloader ist aktiv.\nFühre das Update nicht automatisch durch.")
            hide_donation_banner = CrawlerConfig('SponsorsHelper').get('hide_donation_banner')
            if hide_donation_banner:
                current_donation_banner_setting = shared_state.device.config.get(
                    'org.jdownloader.settings.GraphicalUserInterfaceSettings',
                    'null',
                    'DonateButtonState')
                if current_donation_banner_setting != "CUSTOM_HIDDEN":
                    print("Blende das Spenden-Banner im JDownloader aus.")
                    shared_state.device.config.set('org.jdownloader.settings.GraphicalUserInterfaceSettings',
                                                   'null',
                                                   'DonateButtonState', "CUSTOM_HIDDEN")

            # Clean exit if test run active
            if test_run:
                logger.debug(u"-----------test_run beendet!-----------")
                print(u"-----------test_run beendet!-----------")
                return

            # Wait until next start
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
