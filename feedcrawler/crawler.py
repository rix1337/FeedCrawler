# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul ist das Herzstück des FeedCrawlers. Es durchsucht zyklisch die Feeds der konfigurierten Hostnamen.

import random
import sys
import time
import traceback

from requests.packages.urllib3 import disable_warnings as disable_request_warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from feedcrawler import internal
from feedcrawler.common import Unbuffered, is_device, readable_time
from feedcrawler.config import CrawlerConfig
from feedcrawler.db import FeedDb
from feedcrawler.myjd import get_device
from feedcrawler.ombi import ombi
from feedcrawler.request_handler import clean_flaresolverr_sessions
from feedcrawler.sites.content_all_by import BL as BY
from feedcrawler.sites.content_all_ff import BL as FF
from feedcrawler.sites.content_all_fx import BL as FX
from feedcrawler.sites.content_all_hw import BL as HW
from feedcrawler.sites.content_all_nk import BL as NK
from feedcrawler.sites.content_all_ww import BL as WW
from feedcrawler.sites.content_shows_dj import DJ
from feedcrawler.sites.content_shows_sf import SF
from feedcrawler.sites.content_shows_sj import SJ
from feedcrawler.url import check_url


def search_pool():
    return [
        FX(filename='IMDB'),
        FX(filename='List_ContentAll_Movies'),
        FX(filename='List_ContentAll_Movies_Regex'),
        FX(filename='List_ContentAll_Seasons'),
        HW(filename='IMDB'),
        HW(filename='List_ContentAll_Movies'),
        HW(filename='List_ContentAll_Movies_Regex'),
        HW(filename='List_ContentAll_Seasons'),
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
        FF(filename='IMDB'),
        FF(filename='List_ContentAll_Movies'),
        FF(filename='List_ContentAll_Movies_Regex'),
        FF(filename='List_ContentAll_Seasons'),
        WW(filename='List_ContentAll_Movies_Regex'),
        WW(filename='IMDB'),
        WW(filename='List_ContentAll_Movies'),
        WW(filename='List_ContentAll_Seasons'),
        NK(filename='IMDB'),
        NK(filename='List_ContentAll_Movies'),
        NK(filename='List_ContentAll_Movies_Regex'),
        NK(filename='List_ContentAll_Seasons'),
        BY(filename='IMDB'),
        BY(filename='List_ContentAll_Movies'),
        BY(filename='List_ContentAll_Movies_Regex'),
        BY(filename='List_ContentAll_Seasons')
    ]


def crawler(global_variables, remove_f_time, test_run):
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

    if remove_f_time:
        logger.debug(u"-----------Entferne Zeitpunkt des letzten SF/FF-Suchlaufes!-----------")
        print(u"-----------Entferne Zeitpunkt des letzten SF/FF-Suchlaufes!-----------")
        FeedDb('crawltimes').delete("last_f_run")

    while True:
        try:
            if not internal.device or not is_device(internal.device):
                get_device()
            FeedDb('cached_requests').reset()
            FeedDb('cached_requests').cleanup()
            start_time = time.time()
            check_url(start_time)
            crawltimes.update_store("active", "True")
            crawltimes.update_store("start_time", start_time * 1000)
            logger.debug("-----------Alle Suchläufe gestartet.-----------")

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

            current_f_run = False
            last_f_run = FeedDb('crawltimes').retrieve("last_f_run")
            for task in search_pool():
                name = task._SITE
                try:
                    file = " - Liste: " + task.filename
                except AttributeError:
                    file = ""
                if name in ["SF", "FF"]:
                    f_interval = int(CrawlerConfig('CustomF').get('interval'))
                    if last_f_run and start_time < float(last_f_run) // 1000 + f_interval * 60 * 60:
                        logger.debug(
                            "-----------Mindestintervall bei " + name + " (6h) nicht erreicht - überspringe Suchlauf!-----------")
                        continue
                    else:
                        current_f_run = time.time()
                        FeedDb('site_status').delete("SF_FF")
                logger.debug("-----------Suchlauf (" + name + file + ") gestartet!-----------")
                task.periodical_task()
                logger.debug("-----------Suchlauf (" + name + file + ") ausgeführt!-----------")
            if current_f_run:
                crawltimes.update_store("last_f_run", current_f_run * 1000)
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
            if ombi_string:
                logger.debug(time.strftime("%Y-%m-%d %H:%M:%S") + u" - " + ombi_string)
            logger.debug(time.strftime("%Y-%m-%d %H:%M:%S") + u" - " + request_cache_string)
            logger.debug("-----------Wartezeit bis zum nächsten Suchlauf: " + readable_time(wait) + '-----------')
            ombi_string = ""
            print(time.strftime("%Y-%m-%d %H:%M:%S") +
                  u" - Alle Suchläufe ausgeführt (Dauer: " + readable_time(
                total_time) + u")!",
                  ombi_string + " - " + request_cache_string if ombi_string else request_cache_string)
            print(u"-----------Wartezeit bis zum nächsten Suchlauf: " + readable_time(wait) + '-----------')
            crawltimes.update_store("end_time", end_time * 1000)
            crawltimes.update_store("total_time", readable_time(total_time))
            crawltimes.update_store("next_start", next_start * 1000)
            crawltimes.update_store("active", "False")
            FeedDb('cached_requests').reset()
            FeedDb('cached_requests').cleanup()

            if test_run:
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
