# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import concurrent.futures
import time

import cloudscraper

from rsscrawler.rsscommon import decode_base64
from rsscrawler.rssconfig import RssConfig
from rsscrawler.rssdb import RssDb


def check_url(configfile, dbfile, scraper=False):
    proxy = RssConfig('RSScrawler', configfile).get('proxy')
    if not scraper:
        scraper = cloudscraper.create_scraper()

    sj_url = decode_base64("aHR0cDovL3Nlcmllbmp1bmtpZXMub3Jn")
    mb_url = decode_base64("aHR0cDovL21vdmllLWJsb2cudG8v")
    hw_url = decode_base64("aHR0cDovL2hkLXdvcmxkLm9yZy8=")
    fx_url = decode_base64("aHR0cHM6Ly9mdW54ZC5zaXRlLw==")
    hs_url = decode_base64("aHR0cDovL2hkLXNvdXJjZS50by8=")

    sj_blocked_proxy = False
    mb_blocked_proxy = False
    hw_blocked_proxy = False
    fx_blocked_proxy = False
    hs_blocked_proxy = False

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
            scraper = cloudscraper.create_scraper()

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
            scraper = cloudscraper.create_scraper()

        try:
            if "<Response [403]>" in str(
                    scraper.get(hw_url, proxies=proxies, timeout=30,
                                allow_redirects=False)):
                hw_blocked_proxy = True
            else:
                db.delete("HW")
        except:
            hw_blocked_proxy = True
        if hw_blocked_proxy:
            print(u"Der Zugriff auf HW ist mit der aktuellen Proxy-IP nicht möglich!")
            if RssConfig('RSScrawler', configfile).get("fallback"):
                db.store("HW", "Blocked")
            scraper = cloudscraper.create_scraper()

        try:
            if "<Response [403]>" in str(
                    scraper.get(fx_url, proxies=proxies, timeout=30,
                                allow_redirects=False)):
                fx_blocked_proxy = True
            else:
                db.delete("FX")
        except:
            fx_blocked_proxy = True
        if fx_blocked_proxy:
            print(u"Der Zugriff auf FX ist mit der aktuellen Proxy-IP nicht möglich!")
            if RssConfig('RSScrawler', configfile).get("fallback"):
                db.store("FX", "Blocked")
            scraper = cloudscraper.create_scraper()

        try:
            scraper.get(hs_url, proxies=proxies, timeout=30, allow_redirects=False)
            db.delete("HS")
        except:
            hs_blocked_proxy = True
        if hs_blocked_proxy:
            print(u"Der Zugriff auf HS ist mit der aktuellen Proxy-IP nicht möglich!")
            if RssConfig('RSScrawler', configfile).get("fallback"):
                db.store("HS", "Blocked")
            scraper = cloudscraper.create_scraper()

    if sj_blocked_proxy:
        if "block." in str(
                scraper.get(sj_url, timeout=30, allow_redirects=False).headers.get(
                    "location")):
            print(u"Der Zugriff auf SJ ist mit der aktuellen IP nicht möglich!")

    if mb_blocked_proxy:
        if "<Response [403]>" in str(
                scraper.get(mb_url, timeout=30, allow_redirects=False)):
            print(u"Der Zugriff auf MB ist mit der aktuellen IP nicht möglich!")

    if hw_blocked_proxy:
        if "<Response [403]>" in str(
                scraper.get(hw_url, timeout=30, allow_redirects=False)):
            print(u"Der Zugriff auf HW ist mit der aktuellen IP nicht möglich!")

    if fx_blocked_proxy:
        if "<Response [403]>" in str(
                scraper.get(fx_url, timeout=30, allow_redirects=False)):
            print(u"Der Zugriff auf FX ist mit der aktuellen IP nicht möglich!")

    if hs_blocked_proxy:
        if "<Response [403]>" in str(
                scraper.get(hs_url, timeout=30, allow_redirects=False)):
            print(u"Der Zugriff auf HS ist mit der aktuellen IP nicht möglich!")
    return scraper


def get_url(url, configfile, dbfile, scraper=False):
    config = RssConfig('RSScrawler', configfile)
    proxy = config.get('proxy')
    if not scraper:
        scraper = cloudscraper.create_scraper()
    if proxy:
        sj = decode_base64("c2VyaWVuanVua2llcy5vcmc=")
        mb = decode_base64("bW92aWUtYmxvZy50bw==")
        hw = decode_base64("aGQtd29ybGQub3Jn")
        fx = decode_base64("ZnVueGQK")
        hs = decode_base64("aGQtc291cmNlLnRv")
        db = RssDb(dbfile, 'proxystatus')
        try:
            if sj in url:
                if db.retrieve("SJ") and config.get("fallback"):
                    return scraper.get(url, timeout=30).text
            elif mb in url:
                if db.retrieve("MB") and config.get("fallback"):
                    return scraper.get(url, timeout=30).text
            elif hw in url:
                if db.retrieve("HW") and config.get("fallback"):
                    return scraper.get(url, timeout=30).text
            elif fx in url:
                if db.retrieve("FX") and config.get("fallback"):
                    return scraper.get(url, timeout=30).text
            elif hs in url:
                if db.retrieve("HS") and config.get("fallback"):
                    return scraper.get(url, timeout=30).text
        except Exception as e:
            print(u"Fehler beim Abruf von: " + url + " " + str(e))
            return ""

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


def get_urls_async(urls, configfile, dbfile, scraper=False):
    config = RssConfig('RSScrawler', configfile)
    proxy = config.get('proxy')
    if not scraper:
        scraper = cloudscraper.create_scraper()
    results = []

    def load_url(url):
        try:
            if proxy:
                sj = decode_base64("c2VyaWVuanVua2llcy5vcmc=")
                mb = decode_base64("bW92aWUtYmxvZy50bw==")
                hw = decode_base64("aGQtd29ybGQub3Jn")
                fx = decode_base64("ZnVueGQK")
                hs = decode_base64("aGQtc291cmNlLnRv")
                db = RssDb(dbfile, 'proxystatus')
                if sj in url:
                    if db.retrieve("SJ") and config.get("fallback"):
                        return scraper.get(url, timeout=30).text
                elif mb in url:
                    if db.retrieve("SJ") and config.get("fallback"):
                        return scraper.get(url, timeout=30).text
                elif hw in url:
                    if db.retrieve("HW") and config.get("fallback"):
                        return scraper.get(url, timeout=30).text
                elif fx in url:
                    if db.retrieve("FX") and config.get("fallback"):
                        return scraper.get(url, timeout=30).text
                elif hs in url:
                    if db.retrieve("HS") and config.get("fallback"):
                        return scraper.get(url, timeout=30).text
                proxies = {'http': proxy, 'https': proxy}
                return scraper.get(url, proxies=proxies, timeout=30).text
            else:
                return scraper.get(url, timeout=30).text
        except Exception as e:
            try:
                if proxy:
                    time.sleep(5)
                    proxies = {'http': proxy, 'https': proxy}
                    return scraper.get(url, proxies=proxies, timeout=30).text
                else:
                    time.sleep(5)
                    return scraper.get(url, timeout=30).text
            except:
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
        scraper = cloudscraper.create_scraper()
    if proxy:
        sj = decode_base64("c2VyaWVuanVua2llcy5vcmc=")
        mb = decode_base64("bW92aWUtYmxvZy50bw==")
        hw = decode_base64("aGQtd29ybGQub3Jn")
        fx = decode_base64("ZnVueGQK")
        hs = decode_base64("aGQtc291cmNlLnRv")

        db = RssDb(dbfile, 'proxystatus')
        try:
            if sj in url:
                if db.retrieve("SJ") and config.get("fallback"):
                    return [scraper.get(url, headers=headers, timeout=30), scraper]
            elif mb in url:
                if db.retrieve("MB") and config.get("fallback"):
                    return [scraper.get(url, headers=headers, timeout=30), scraper]
            elif hw in url:
                if db.retrieve("HW") and config.get("fallback"):
                    return [scraper.get(url, headers=headers, timeout=30), scraper]
            elif fx in url:
                if db.retrieve("FX") and config.get("fallback"):
                    return [scraper.get(url, headers=headers, timeout=30), scraper]
            elif hs in url:
                if db.retrieve("HS") and config.get("fallback"):
                    return [scraper.get(url, headers=headers, timeout=30), scraper]
        except Exception as e:
            print(u"Fehler beim Abruf von: " + url + " " + str(e))
            return ""
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
        scraper = cloudscraper.create_scraper()
    if proxy:
        sj = decode_base64("c2VyaWVuanVua2llcy5vcmc=")
        mb = decode_base64("bW92aWUtYmxvZy50bw==")
        hw = decode_base64("aGQtd29ybGQub3Jn")
        fx = decode_base64("ZnVueGQK")
        hs = decode_base64("aGQtc291cmNlLnRv")

        db = RssDb(dbfile, 'proxystatus')
        try:
            if sj in url:
                if db.retrieve("SJ") and config.get("fallback"):
                    return scraper.post(url, data, timeout=30).content
            elif mb in url:
                if db.retrieve("MB") and config.get("fallback"):
                    return scraper.post(url, data, timeout=30).content
            elif hw in url:
                if db.retrieve("HW") and config.get("fallback"):
                    return scraper.post(url, data, timeout=30).content
            elif fx in url:
                if db.retrieve("FX") and config.get("fallback"):
                    return scraper.post(url, data, timeout=30).content
            elif hs in url:
                if db.retrieve("HS") and config.get("fallback"):
                    return scraper.post(url, data, timeout=30).content
        except Exception as e:
            print(u"Fehler beim Abruf von: " + url + " " + str(e))
            return ""
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
        scraper = cloudscraper.create_scraper()
    if proxy:
        sj = decode_base64("c2VyaWVuanVua2llcy5vcmc=")
        mb = decode_base64("bW92aWUtYmxvZy50bw==")
        hw = decode_base64("aGQtd29ybGQub3Jn")
        fx = decode_base64("ZnVueGQK")
        hs = decode_base64("aGQtc291cmNlLnRv")

        db = RssDb(dbfile, 'proxystatus')
        try:
            if sj in url:
                if db.retrieve("SJ") and config.get("fallback"):
                    return scraper.post(url, json=json, timeout=30).content
            elif mb in url:
                if db.retrieve("MB") and config.get("fallback"):
                    return scraper.post(url, json=json, timeout=30).content
            elif hw in url:
                if db.retrieve("HW") and config.get("fallback"):
                    return scraper.post(url, json=json, timeout=30).content
            elif fx in url:
                if db.retrieve("FX") and config.get("fallback"):
                    return scraper.post(url, json=json, timeout=30).content
            elif hs in url:
                if db.retrieve("HS") and config.get("fallback"):
                    return scraper.post(url, json=json, timeout=30).content
        except Exception as e:
            print(u"Fehler beim Abruf von: " + url + " " + str(e))
            return ""
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
