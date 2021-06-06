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
    sj = hostnames.get('sj')
    dj = hostnames.get('dj')
    sf = hostnames.get('sf')
    by = hostnames.get('by')
    dw = hostnames.get('dw')
    fx = hostnames.get('fx')
    nk = hostnames.get('nk')
    ww = hostnames.get('ww')

    sj_url = 'https://' + sj
    dj_url = 'https://' + dj
    sf_url = 'https://' + sf
    by_url = 'https://' + by
    dw_url = 'https://' + dw
    fx_url = 'https://' + fx
    nk_url = 'https://' + nk
    ww_url = 'https://' + ww

    sj_blocked = False
    dj_blocked = False
    sf_blocked = False
    by_blocked = False
    dw_blocked = False
    fx_blocked = False
    nk_blocked = False
    ww_blocked = False

    db_status = FeedDb('site_status')
    db_status.delete("SJ")
    db_status.delete("DJ")
    db_status.delete("SF")
    db_status.delete("BY")
    db_status.delete("DW")
    db_status.delete("FX")
    db_status.delete("NK")
    db_status.delete("WW")

    if not sj:
        db_status.store("SJ", "Blocked")
    else:
        try:
            if not request(sj_url)["status_code"] == 200:
                sj_blocked = True
        except:
            sj_blocked = True
        if sj_blocked:
            db_status.store("SJ", "Blocked")
            print(u"Der Zugriff auf SJ ist ohne FlareSolverr gesperrt!")

    if not dj:
        db_status.store("DJ", "Blocked")
    else:
        try:
            if not request(dj_url)["status_code"] == 200:
                dj_blocked = True
        except:
            dj_blocked = True
        if dj_blocked:
            db_status.store("DJ", "Blocked")
            print(u"Der Zugriff auf DJ ist ohne FlareSolverr gesperrt!")

    if not sf:
        db_status.store("SF", "Blocked")
    else:
        try:
            delta = datetime.datetime.now().strftime("%Y-%m-%d")
            sf_test = request(sf_url + '/updates/' + delta)
            if not sf_test["text"] or sf_test["status_code"] is not (
                    200 or 304) or '<h3><a href="/' not in sf_test["text"]:
                sf_blocked = True
        except:
            sf_blocked = True
        if sf_blocked:
            db_status.store("SF", "Blocked")
            print(u"Der Zugriff auf SF ist ohne FlareSolverr gesperrt!")

    if not by:
        db_status.store("BY", "Blocked")
    else:
        try:
            if request(by_url)["status_code"] == 403:
                by_blocked = True
        except:
            by_blocked = True
        if by_blocked:
            db_status.store("BY", "Blocked")
            print(u"Der Zugriff auf BY ist ohne FlareSolverr gesperrt!")

    if not dw:
        db_status.store("DW", "Blocked")
    else:
        try:
            dw_test = request(dw_url + "/downloads/hauptkategorie/movies/")
            if not dw_test["text"] or dw_test["status_code"] is not (
                    200 or 304) or '<a id="first_element" href=' not in dw_test["text"]:
                dw_blocked = True
        except:
            dw_blocked = True
        if dw_blocked:
            db_status.store("DW", "Blocked")
            print(u"Der Zugriff auf DW ist ohne FlareSolverr gesperrt!")

    if not fx:
        db_status.store("FX", "Blocked")
    else:
        try:
            if request(fx_url)["status_code"] == 403:
                fx_blocked = True
        except:
            fx_blocked = True
        if fx_blocked:
            db_status.store("FX", "Blocked")
            print(u"Der Zugriff auf FX ist ohne FlareSolverr gesperrt!")

    if not nk:
        db_status.store("NK", "Blocked")
    else:
        try:
            if request(nk_url)["status_code"] == 403:
                nk_blocked = True
        except:
            nk_blocked = True
        if nk_blocked:
            db_status.store("NK", "Blocked")
            print(u"Der Zugriff auf NK ist ohne FlareSolverr gesperrt!")

    if not ww:
        db_status.store("WW", "Blocked")
    else:
        try:
            ww_test = request(ww_url + "/ajax", method='post', params="p=1&t=l&q=1")
            if not ww_test["text"] or ww_test["status_code"] is not (
                    200 or 304) or '<span class="main-rls">' not in ww_test["text"]:
                ww_blocked = True
        except:
            ww_blocked = True
        if ww_blocked:
            db_status.store("WW", "Blocked")
            print(u"Der Zugriff auf WW ist ohne FlareSolverr gesperrt!")

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
