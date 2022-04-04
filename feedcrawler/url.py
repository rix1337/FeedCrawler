# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt alle Funktionen für die Prüfung und Interaktion mit URLs zur Verfügung.

import concurrent.futures
import datetime

from feedcrawler import internal
from feedcrawler.config import CrawlerConfig
from feedcrawler.db import FeedDb
from feedcrawler.request_handler import get_flaresolverr_url
from feedcrawler.request_handler import request


def check_url(start_time):
    hostnames = CrawlerConfig('Hostnames')
    db_status = FeedDb('site_status')
    db_status.reset()
    db_status = FeedDb('site_status')

    for site in internal.sites:
        if site in ["SF", "FF"]:
            last_f_run = FeedDb('crawltimes').retrieve("last_f_run")
            f_interval = int(CrawlerConfig('CustomF').get('interval'))
            if last_f_run and start_time < float(last_f_run) // 1000 + f_interval * 60 * 60:
                internal.logger.debug(
                    "-----------Mindestintervall bei " + site + " (6h) nicht erreicht - überspringe Prüfung!-----------")
                continue

        hostname = hostnames.get(site.lower())
        if not hostname:
            db_status.store(site + "_normal", "Blocked")
            db_status.store(site + "_flaresolverr", "Blocked")
            db_status.store(site + "_flaresolverr_proxy", "Blocked")
        else:
            flaresolverr = get_flaresolverr_url()
            skip_sites = ["WW"]
            skip_normal_ip = flaresolverr and (site in skip_sites)
            if skip_normal_ip:
                blocked_with_normal_ip = True
            else:
                blocked_with_normal_ip = check_if_blocked(site, "https://" + hostname)
            if blocked_with_normal_ip:
                if skip_normal_ip:
                    print(u"Der Zugriff auf " + site + " erfolgt nur mit FlareSolverr!")
                else:
                    print(u"Der Zugriff auf " + site + " ist für die aktuelle IP gesperrt!")
                db_status.store(site + "_normal", "Blocked")
                if not flaresolverr:
                    print(
                        u"Der Zugriff auf " + site + " funktioniert vielleicht mit FlareSolverr. FlareSolverr ist derzeit nicht eingerichtet!")
                    db_status.store(site + "_flaresolverr", "Blocked")
                    db_status.store(site + "_flaresolverr_proxy", "Blocked")
                else:
                    # Since we are aware this site is blocked FlareSolverr will be used for subsequent requests
                    blocked_with_flaresolverr = check_if_blocked(site, "https://" + hostname)
                    if not blocked_with_flaresolverr:
                        print(u"Der Zugriff auf " + site + " mit FlareSolverr funktioniert!")
                    else:
                        print(u"Der Zugriff auf " + site + " ist mit FlareSolverr gesperrt!")
                        db_status.store(site + "_flaresolverr", "Blocked")

                        if not flaresolverr:
                            print(
                                u"Der Zugriff auf " + site + " funktioniert vielleicht mit FlareSolverr + Proxy. Proxy ist derzeit nicht eingerichtet!")
                            db_status.store(site + "_flaresolverr_proxy", "Blocked")
                        else:
                            # Since FlareSolverr is now aware it was blocked, it will try to use the proxy for subsequent requests
                            blocked_with_flaresolverr_and_proxy = check_if_blocked(site, "https://" + hostname)
                            if blocked_with_flaresolverr_and_proxy:
                                print(u"Der Zugriff auf " + site + " ist mit FlareSolverr + Proxy gesperrt!")
                                db_status.store(site + "_flaresolverr_proxy", "Blocked")
                            else:
                                print(u"Der Zugriff auf " + site + " mit FlareSolverr + Proxy funktioniert!")


def check_if_blocked(site, url):
    try:
        # These can be checked the same way
        if site in ["BY", "FX", "HW"]:
            status = request(url, dont_cache=True)["status_code"]
            if not status == 200 or status == 403:
                return True
        # Custom check required
        elif site in ["SJ", "DJ"]:
            status = request(url + '/api/releases/latest/0', dont_cache=True)["status_code"]
            if not status == 200 or status == 403:
                return True
        elif site in ["FF"]:
            delta = datetime.datetime.now().strftime("%Y-%m-%d")
            ff_test = request(url + '/updates/' + delta, dont_cache=True)
            if not ff_test["text"] or ff_test["status_code"] is not (
                    200 or 304) or '<div class="list blog"' not in ff_test["text"]:
                return True
        # Custom check required
        elif site in ["SF"]:
            delta = datetime.datetime.now().strftime("%Y-%m-%d")
            sf_test = request(url + '/updates/' + delta, dont_cache=True)
            if not sf_test["text"] or sf_test["status_code"] is not (
                    200 or 304) or '<h3><a href="/' not in sf_test["text"]:
                return True
        # Custom check required
        elif site == "WW":
            ww_test = request(url + "/ajax", method='post', params="p=1&t=l&q=1", dont_cache=True)
            if not ww_test["text"] or ww_test["status_code"] is not (
                    200 or 304) or '<span class="main-rls">' not in ww_test["text"]:
                return True
        else:
            print(u"Keine Prüfung für " + site + " implementiert.")
    except:
        return True
    return False


def get_url(url):
    try:
        response = request(url)["text"]
        return response
    except Exception as e:
        print(u"Fehler beim Abruf von: " + url + " " + str(e))
        return ""


def get_url_headers(url, headers=False):
    try:
        response = request(url, headers=headers)
        return response
    except Exception as e:
        print(u"Fehler beim Abruf von: " + url + " " + str(e))
        return ""


def get_redirected_url(url):
    try:
        redirect_url = request(url, redirect_url=True)
        return redirect_url
    except Exception as e:
        print(u"Fehler beim Abruf von: " + url + " " + str(e))
        return url


def post_url(url, data=False):
    try:
        response = request(url, method='post', params=data)["text"]
        return response
    except Exception as e:
        print(u"Fehler beim Abruf von: " + url + " " + str(e))
        return ""


def post_url_headers(url, headers, data=False):
    try:
        response = request(url, method='post', params=data, headers=headers)
        return response
    except Exception as e:
        print(u"Fehler beim Abruf von: " + url + " " + str(e))
        return ""


def get_urls_async(urls):
    results = []

    def load_url(url):
        return get_url(url)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(load_url, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            future_to_url[future]
            try:
                results.append(future.result())
            except Exception:
                pass
    return [results]
