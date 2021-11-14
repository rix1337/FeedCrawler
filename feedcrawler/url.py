# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337

import concurrent.futures
import datetime

from feedcrawler.config import CrawlerConfig
from feedcrawler.db import FeedDb
from feedcrawler.flaresolverr import request


def check_url():
    hostnames = CrawlerConfig('Hostnames')
    db_status = FeedDb('site_status')

    site_names = ["SJ", "DJ", "SF", "BY", "FX", "NK", "WW", "LOL"]
    sites = {}
    for site in site_names:
        url = hostnames.get(site.lower())
        if url:
            sites[site] = {
                "url": 'https://' + url,
                "blocked_normal": False,
                "blocked_flaresolverr": False
            }
            db_status.delete(site)
            db_status.delete(site + "_normal")
            db_status.delete(site + "_flaresolverr")
        else:
            sites[site] = False

    for site in site_names:
        if not sites[site]:
            db_status.store(site + "_normal", "Blocked")
            db_status.store(site + "_flaresolverr", "Blocked")
        else:
            try:
                if site == "SJ" or site == "DJ":
                    if not request(sites[site]["url"])["status_code"] == 200:
                        sites[site]["blocked_normal"] = True
                elif site == "BY" or site == "FX" or site == "DJ":
                    if request(sites[site]["url"])["status_code"] == 403:
                        sites[site]["blocked_normal"] = True
                elif site == "SF":
                    delta = datetime.datetime.now().strftime("%Y-%m-%d")
                    sf_test = request(sites["SF"]["url"] + '/updates/' + delta)
                    if not sf_test["text"] or sf_test["status_code"] is not (
                            200 or 304) or '<h3><a href="/' not in sf_test["text"]:
                        sites["SF"]["blocked_normal"] = True
                elif site == "WW":
                    ww_test = request(sites["WW"]["url"] + "/ajax", method='post', params="p=1&t=l&q=1")
                    if not ww_test["text"] or ww_test["status_code"] is not (
                            200 or 304) or '<span class="main-rls">' not in ww_test["text"]:
                        sites["WW"]["blocked_normal"] = True
                else:
                    print(u"Keine Prüfung für " + site + " implementiert.")
            except:
                sites[site]["blocked_normal"] = True
            if sites[site]["blocked_normal"]:
                db_status.store(site + "_normal", "Blocked")
                print(u"Der Zugriff auf " + site + " ist ohne FlareSolverr gesperrt!")

    return


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
