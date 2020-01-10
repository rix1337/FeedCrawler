# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import concurrent.futures

import cloudscraper

from rsscrawler.rsscommon import decode_base64
from rsscrawler.rssconfig import RssConfig
from rsscrawler.rssdb import RssDb


def check_url(configfile, dbfile, scraper=False):
    sj_url = decode_base64("aHR0cDovL3Nlcmllbmp1bmtpZXMub3Jn")
    mb_url = decode_base64("aHR0cDovL21vdmllLWJsb2cudG8v")
    proxy = RssConfig('RSScrawler', configfile).get('proxy')
    if not scraper:
        scraper = cloudscraper.create_scraper(browser='chrome')
    sj_blocked_proxy = False
    mb_blocked_proxy = False
    if proxy:
        db = RssDb(dbfile, 'proxystatus')
        proxies = {'http': proxy, 'https': proxy}
        try:
            if "block." in str(
                    scraper.get(sj_url, proxies=proxies, timeout=30,
                                allow_redirects=False).headers.get("location")):
                sj_blocked_proxy = True
            else:
                db.delete("SJ")
        except:
            sj_blocked_proxy = True

        if sj_blocked_proxy:
            print(u"Der Zugriff auf SJ ist mit der aktuellen Proxy-IP nicht möglich!")
            if RssConfig('RSScrawler', configfile).get("fallback"):
                db.store("SJ", "Blocked")
            sj_blocked_proxy = True

        try:
            if "<Response [403]>" in str(
                    scraper.get(mb_url, proxies=proxies, timeout=30,
                                allow_redirects=False)):
                mb_blocked_proxy = True
            else:
                db.delete("MB")
        except:
            mb_blocked_proxy = True

        if mb_blocked_proxy:
            print(u"Der Zugriff auf MB ist mit der aktuellen Proxy-IP nicht möglich!")
            if RssConfig('RSScrawler', configfile).get("fallback"):
                db.store("MB", "Blocked")

    if not proxy or sj_blocked_proxy or mb_blocked_proxy:
        if "block." in str(
                scraper.get(sj_url, timeout=30, allow_redirects=False).headers.get(
                    "location")):
            print(u"Der Zugriff auf SJ ist mit der aktuellen IP nicht möglich!")
        if "<Response [403]>" in str(
                scraper.get(mb_url, timeout=30, allow_redirects=False)):
            print(u"Der Zugriff auf MB ist mit der aktuellen IP nicht möglich!")
    return


def get_url(url, configfile, dbfile, scraper=False):
    config = RssConfig('RSScrawler', configfile)
    proxy = config.get('proxy')
    if not scraper:
        scraper = cloudscraper.create_scraper(browser='chrome')
    if proxy:
        sj = decode_base64("c2VyaWVuanVua2llcy5vcmc=")
        mb = decode_base64("bW92aWUtYmxvZy50bw==")
        db = RssDb(dbfile, 'proxystatus')
        if sj in url:
            if db.retrieve("SJ") and config.get("fallback"):
                return scraper.get(url, timeout=30).text
        elif mb in url:
            if db.retrieve("MB") and config.get("fallback"):
                return scraper.get(url, timeout=30).text
        proxies = {'http': proxy, 'https': proxy}
        try:
            response = scraper.get(url, proxies=proxies, timeout=30).text
            return response
        except Exception as e:
            print(u"Fehler beim Abruf von: " + url + " " + str(e))
            return ""
    else:
        try:
            response = scraper.get(url, timeout=30).text
            return response
        except Exception as e:
            print(u"Fehler beim Abruf von: " + url + " " + str(e))
            return ""


def get_urls_asynch(urls, configfile, scraper=False):
    config = RssConfig('RSScrawler', configfile)
    proxy = config.get('proxy')
    if not scraper:
        scraper = cloudscraper.create_scraper(browser='chrome')
    results = []

    def load_url(url):
        try:
            if proxy:
                proxies = {'http': proxy, 'https': proxy}
                return scraper.get(url, proxies=proxies, timeout=30).text
            else:
                return scraper.get(url, timeout=30).text
        except Exception as e:
            print(u"Fehler beim Abruf von: " + url + " " + str(e))
            return ""

    with concurrent.futures.ThreadPoolExecutor(max_workers=40) as executor:
        future_to_url = {executor.submit(load_url, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            future_to_url[future]
            try:
                results.append(future.result())
            except Exception:
                pass
    return [results, scraper]


def get_url_headers(url, configfile, dbfile, headers, scraper=False):
    config = RssConfig('RSScrawler', configfile)
    proxy = config.get('proxy')
    if not scraper:
        scraper = cloudscraper.create_scraper(browser='chrome')
    if proxy:
        sj = decode_base64("c2VyaWVuanVua2llcy5vcmc=")
        mb = decode_base64("bW92aWUtYmxvZy50bw==")
        db = RssDb(dbfile, 'proxystatus')
        if sj in url:
            if db.retrieve("SJ") and config.get("fallback"):
                return [scraper.get(url, headers=headers, timeout=30), scraper]
        elif mb in url:
            if db.retrieve("MB") and config.get("fallback"):
                return [scraper.get(url, headers=headers, timeout=30), scraper]
        proxies = {'http': proxy, 'https': proxy}
        try:
            response = scraper.get(url, headers=headers, proxies=proxies, timeout=30)
            return [response, scraper]
        except Exception as e:
            print(u"Fehler beim Abruf von: " + url + " " + str(e))
            return ["", scraper]
    else:
        try:
            response = scraper.get(url, headers=headers, timeout=30)
            return [response, scraper]
        except Exception as e:
            print(u"Fehler beim Abruf von: " + url + " " + str(e))
            return ["", scraper]


def post_url(url, configfile, dbfile, data, scraper=False):
    config = RssConfig('RSScrawler', configfile)
    proxy = config.get('proxy')
    if not scraper:
        scraper = cloudscraper.create_scraper(browser='chrome')
    if proxy:
        sj = decode_base64("c2VyaWVuanVua2llcy5vcmc=")
        mb = decode_base64("bW92aWUtYmxvZy50bw==")
        db = RssDb(dbfile, 'proxystatus')
        if sj in url:
            if db.retrieve("SJ") and config.get("fallback"):
                return scraper.post(url, data, timeout=30).content
        elif mb in url:
            if db.retrieve("MB") and config.get("fallback"):
                return scraper.post(url, data, timeout=30).content
        proxies = {'http': proxy, 'https': proxy}
        try:
            response = scraper.post(url, data, proxies=proxies, timeout=30).content
            return response
        except Exception as e:
            print(u"Fehler beim Abruf von: " + url + " " + str(e))
            return ""
    else:
        try:
            response = scraper.post(url, data, timeout=30).content
            return response
        except Exception as e:
            print(u"Fehler beim Abruf von: " + url + " " + str(e))
            return ""


def post_url_json(url, configfile, dbfile, json, scraper=False):
    config = RssConfig('RSScrawler', configfile)
    proxy = config.get('proxy')
    if not scraper:
        scraper = cloudscraper.create_scraper(browser='chrome')
    if proxy:
        sj = decode_base64("c2VyaWVuanVua2llcy5vcmc=")
        mb = decode_base64("bW92aWUtYmxvZy50bw==")
        db = RssDb(dbfile, 'proxystatus')
        if sj in url:
            if db.retrieve("SJ") and config.get("fallback"):
                return scraper.post(url, json=json, timeout=30).content
        elif mb in url:
            if db.retrieve("MB") and config.get("fallback"):
                return scraper.post(url, json=json, timeout=30).content
        proxies = {'http': proxy, 'https': proxy}
        try:
            response = scraper.post(url, json=json, proxies=proxies, timeout=30).content
            return response
        except Exception as e:
            print(u"Fehler beim Abruf von: " + url + " " + str(e))
            return ""
    else:
        try:
            response = scraper.post(url, json=json, timeout=30).content
            return response
        except Exception as e:
            print(u"Fehler beim Abruf von: " + url + " " + str(e))
            return ""
