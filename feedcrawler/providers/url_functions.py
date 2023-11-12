# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt alle Funktionen für die Prüfung und Interaktion mit URLs zur Verfügung.

import concurrent.futures
from datetime import datetime, timedelta

from feedcrawler.providers import shared_state
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.http_requests.cache_handler import cached_request
from feedcrawler.providers.http_requests.cloudflare_handlers import get_solver_url
from feedcrawler.providers.sqlite_database import FeedDb


def check_url(start_time):
    hostnames = CrawlerConfig('Hostnames')
    db_status = FeedDb('site_status')

    for site in shared_state.values["sites"]:
        if site in ["SJ", "DJ", "SF", "FF", "HW", "WW"]:  # all sites know to use cloudflare
            last_cloudflare_run = FeedDb('crawltimes').retrieve("last_cloudflare_run")
            cloudflare_wait_time = int(CrawlerConfig('Cloudflare').get('wait_time'))
            if last_cloudflare_run and start_time < float(last_cloudflare_run) // 1000 + cloudflare_wait_time * 60 * 60:
                shared_state.logger.debug(
                    "-----------Wartezeit bei " + site + " (6h) nicht verstrichen - überspringe Prüfung!-----------")
                continue

        hostname = hostnames.get(site.lower())
        if not hostname:
            db_status.update_store(site + "_normal", "Blocked")
            db_status.update_store(site + "_advanced", "Blocked")
        else:
            hostnames.save(site.lower(), hostname)
            db_status.delete(site + "_normal")
            db_status.delete(site + "_advanced")
            sponsors_helper_url = get_solver_url("sponsors_helper")
            flaresolverr_url = get_solver_url("flaresolverr")
            skip_sites = ["HW", "WW", ]
            skip_normal_ip = (sponsors_helper_url or flaresolverr_url) and (site in skip_sites)
            if skip_normal_ip:
                blocked_with_normal_ip = True
            else:
                blocked_with_normal_ip = check_if_blocked(site, "https://" + hostname)
            if not blocked_with_normal_ip:
                print("Der Zugriff auf " + site + " funktioniert!")
            else:
                if skip_normal_ip:
                    print("Der Zugriff auf " + site + " ist nur mit FlareSolverr bzw. Sponsors Helper möglich!")
                else:
                    print("Der Zugriff auf " + site + " ist gesperrt!")
                db_status.update_store(site + "_normal", "Blocked")
                if not sponsors_helper_url and not flaresolverr_url:
                    print(
                        "Der Zugriff auf " + site + " ist ohne FlareSolverr bzw. Sponsors Helper derzeit nicht möglich!")
                    db_status.update_store(site + "_advanced", "Blocked")
                else:
                    # Since we are aware this site is blocked Sponsors Helper/FlareSolverr will be used for subsequent requests
                    still_blocked = check_if_blocked(site, "https://" + hostname)
                    if not still_blocked:
                        print("Die Cloudflare-Blockade auf " + site + " wurde erfolgreich umgangen!")
                    else:
                        print("Die Cloudflare-Blockade auf " + site + " konnte nicht umgangen werden!")
                        db_status.update_store(site + "_advanced", "Blocked")


def check_if_blocked(site, url):
    try:
        # These can be checked the same way
        if site in ["FX", "DW", "BY", "NK", "NX", "DD"]:
            status = cached_request(url, dont_cache=True)["status_code"]
            if status is not (200 or 304):
                return True
        # Custom checks required
        elif site in ["SF"]:
            delta = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
            sf_test = cached_request(url + '/updates/' + delta, dont_cache=True)
            if not sf_test["text"] or sf_test["status_code"] is not (
                    200 or 304) or '<h3><a href="/' not in sf_test["text"]:
                return True
        elif site in ["FF"]:
            delta = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
            ff_test = cached_request(url + '/updates/' + delta, dont_cache=True)
            if not ff_test["text"] or ff_test["status_code"] is not (
                    200 or 304) or '<div class="list blog"' not in ff_test["text"]:
                return True
        elif site in ["HW"]:
            status = cached_request(url, dont_cache=True)["status_code"]
            if status is not (200 or 304):
                return True
        elif site == "WW":
            ww_test = cached_request(url + "/ajax", method='post', params="p=1&t=l&q=1", dont_cache=True)
            if not ww_test["text"] or ww_test["status_code"] is not (
                    200 or 304) or '<span class="main-rls">' not in ww_test["text"]:
                return True
        elif site in ["SJ", "DJ"]:
            status = cached_request(url + '/api/releases/latest/0', dont_cache=True)["status_code"]
            if status is not (200 or 304):
                return True
        else:
            print("Keine Prüfung für " + site + " implementiert.")
    except:
        return True
    return False


def get_url(url):
    if url:
        try:
            response = cached_request(url)["text"]
            return response
        except Exception as e:
            print("Fehler beim Abruf von: " + str(url) + " " + str(e))
            pass
    return ""


def get_url_headers(url, headers=False):
    if url:
        try:
            response = cached_request(url, headers=headers)
            return response
        except Exception as e:
            print("Fehler beim Abruf von: " + url + " " + str(e))
    return ""


def get_redirected_url(url):
    if url:
        try:
            redirect_url = cached_request(url, redirect_url=True)["url"]
            return redirect_url
        except Exception as e:
            print("Fehler beim Abruf von: " + url + " " + str(e))
    return url


def post_url(url, data=False):
    if url:
        try:
            response = cached_request(url, method='post', params=data)["text"]
            return response
        except Exception as e:
            print("Fehler beim Abruf von: " + url + " " + str(e))
    return ""


def post_url_headers(url, headers, data=False):
    if url:
        try:
            response = cached_request(url, method='post', params=data, headers=headers)
            return response
        except Exception as e:
            print("Fehler beim Abruf von: " + url + " " + str(e))
    return ""


def get_urls_async(urls):
    results = []

    def load_url(url):
        return get_url(url)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(load_url, url): url for url in urls}
        futures = concurrent.futures.as_completed(future_to_url)
        for future in futures:
            source = future_to_url[future]
            try:
                results.append([future.result(), source])
            except Exception:
                pass
    return results
