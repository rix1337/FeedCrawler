# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import concurrent.futures

import cloudscraper

from rsscrawler.rsscommon import decode_base64
from rsscrawler.rssconfig import RssConfig
from rsscrawler.rssdb import RssDb


def check_url(configfile, dbfile, scraper=False):
    proxy = RssConfig('RSScrawler', configfile).get('proxy')
    fallback = RssConfig('RSScrawler', configfile).get('fallback')

    if not scraper:
        scraper = cloudscraper.create_scraper()

    sj_url = "https://serienjunkies.org/api/releases/latest/0"
    mb_url = decode_base64("aHR0cDovL21vdmllLWJsb2cudG8v")
    hw_url = decode_base64("aHR0cDovL2hkLXdvcmxkLm9yZy8=")
    fx_url = decode_base64("aHR0cHM6Ly9mdW54ZC5zaXRlLw==")
    hs_url = decode_base64("aHR0cHM6Ly9oZC1zb3VyY2UudG8vY29sbGVjdGlvbi9uZXVlcnNjaGVpbnVuZ2VuLw==")
    nk_url = decode_base64('aHR0cHM6Ly9uaW1hNGsub3JnLw==')

    sj_blocked_proxy = False
    mb_blocked_proxy = False
    hw_blocked_proxy = False
    fx_blocked_proxy = False
    hs_blocked_proxy = False
    nk_blocked_proxy = False
    sj_blocked = False
    mb_blocked = False
    hw_blocked = False
    fx_blocked = False
    hs_blocked = False
    nk_blocked = False

    db = RssDb(dbfile, 'proxystatus')
    db.delete("SJ")
    db.delete("MB")
    db.delete("HW")
    db.delete("FX")
    db.delete("HS")
    db.delete("NK")
    db_normal = RssDb(dbfile, 'normalstatus')
    db_normal.delete("SJ")
    db_normal.delete("MB")
    db_normal.delete("HW")
    db_normal.delete("FX")
    db_normal.delete("HS")
    db_normal.delete("NK")

    if proxy:
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
            db.store("SJ", "Blocked")
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
            db.store("FX", "Blocked")
            scraper = cloudscraper.create_scraper()

        try:
            if "200" not in str(
                    scraper.get(hs_url, timeout=30, allow_redirects=False).status_code):
                hs_blocked_proxy = True
            else:
                db.delete("HS")
        except:
            hs_blocked_proxy = True
        if hs_blocked_proxy:
            print(u"Der Zugriff auf HS ist mit der aktuellen Proxy-IP nicht möglich!")
            db.store("HS", "Blocked")
            scraper = cloudscraper.create_scraper()

        try:
            if "200" not in str(
                    scraper.get(nk_url, timeout=30, allow_redirects=False).status_code):
                nk_blocked_proxy = True
            else:
                db.delete("NK")
        except:
            nk_blocked_proxy = True
        if nk_blocked_proxy:
            print(u"Der Zugriff auf NK ist mit der aktuellen Proxy-IP nicht möglich!")
            db.store("NK", "Blocked")
            scraper = cloudscraper.create_scraper()

    if not proxy or (proxy and sj_blocked_proxy and fallback):
        try:
            if "block." in str(
                    scraper.get(sj_url, timeout=30, allow_redirects=False).headers.get(
                        "location")):
                sj_blocked = True
        except:
            sj_blocked = True
        if sj_blocked:
            db_normal.store("SJ", "Blocked")
            print(u"Der Zugriff auf SJ ist mit der aktuellen IP nicht möglich!")

    if not proxy or (proxy and mb_blocked_proxy and fallback):
        try:
            if "<Response [403]>" in str(
                    scraper.get(mb_url, timeout=30, allow_redirects=False)):
                mb_blocked = True
        except:
            mb_blocked = True
        if mb_blocked:
            db_normal.store("MB", "Blocked")
            print(u"Der Zugriff auf MB ist mit der aktuellen IP nicht möglich!")

    if not proxy or (proxy and hw_blocked_proxy and fallback):
        try:
            if "<Response [403]>" in str(
                    scraper.get(hw_url, timeout=30, allow_redirects=False)):
                hw_blocked = True
        except:
            hw_blocked = True
        if hw_blocked:
            db_normal.store("HW", "Blocked")
            print(u"Der Zugriff auf HW ist mit der aktuellen IP nicht möglich!")

    if not proxy or (proxy and fx_blocked_proxy and fallback):
        try:
            if "<Response [403]>" in str(
                    scraper.get(fx_url, timeout=30, allow_redirects=False)):
                fx_blocked = True
        except:
            fx_blocked = True
        if fx_blocked:
            db_normal.store("FX", "Blocked")
            print(u"Der Zugriff auf FX ist mit der aktuellen IP nicht möglich!")

    if not proxy or (proxy and hs_blocked_proxy and fallback):
        try:
            if "200" not in str(
                    scraper.get(hs_url, timeout=30, allow_redirects=False).status_code):
                hs_blocked = True
        except:
            hs_blocked = True
        if hs_blocked:
            db_normal.store("HS", "Blocked")
            print(u"Der Zugriff auf HS ist mit der aktuellen IP nicht möglich!")

    if not proxy or (proxy and nk_blocked_proxy and fallback):
        try:
            if "200" not in str(
                    scraper.get(nk_url, timeout=30, allow_redirects=False).status_code):
                nk_blocked = True
        except:
            nk_blocked = True
        if nk_blocked:
            db_normal.store("NK", "Blocked")
            print(u"Der Zugriff auf NK ist mit der aktuellen IP nicht möglich!")

    return scraper


def check_is_site(url):
    if decode_base64("c2VyaWVuanVua2llcy5vcmc=") in url:
        return "SJ"
    elif decode_base64("bW92aWUtYmxvZy4=") in url:
        return "MB"
    elif decode_base64("aGQtd29ybGQub3Jn") in url:
        return "HW"
    elif decode_base64("ZnVueGQ=") in url:
        return "FX"
    elif decode_base64("aGQtc291cmNlLnRv") in url:
        return "HS"
    elif decode_base64('bmltYTRr') in url:
        return "NK"
    else:
        return False


def get_url(url, configfile, dbfile, scraper=False):
    config = RssConfig('RSScrawler', configfile)
    proxy = config.get('proxy')
    if not scraper:
        scraper = cloudscraper.create_scraper()

    db = RssDb(dbfile, 'proxystatus')
    db_normal = RssDb(dbfile, 'normalstatus')
    site = check_is_site(url)
    if proxy:
        try:
            if site and "SJ" in site:
                if db.retrieve("SJ"):
                    if config.get("fallback") and not db_normal.retrieve("SJ"):
                        return scraper.get(url, timeout=30).text
                    else:
                        return ""
            elif site and "MB" in site:
                if db.retrieve("MB"):
                    if config.get("fallback") and not db_normal.retrieve("MB"):
                        return scraper.get(url, timeout=30).text
                    else:
                        return ""
            elif site and "HW" in site:
                if db.retrieve("HW"):
                    if config.get("fallback") and not db_normal.retrieve("HW"):
                        return scraper.get(url, timeout=30).text
                    else:
                        return ""
            elif site and "FX" in site:
                if db.retrieve("FX"):
                    if config.get("fallback") and not db_normal.retrieve("FX"):
                        return scraper.get(url, timeout=30).text
                    else:
                        return ""
            elif site and "HS" in site:
                if db.retrieve("HS"):
                    if config.get("fallback") and not db_normal.retrieve("HS"):
                        return scraper.get(url, timeout=30).text
                    else:
                        return ""
            elif site and "NK" in site:
                if db.retrieve("NK"):
                    if config.get("fallback") and not db_normal.retrieve("NK"):
                        return scraper.get(url, timeout=30).text
                    else:
                        return ""
            proxies = {'http': proxy, 'https': proxy}
            response = scraper.get(url, proxies=proxies, timeout=30).text
            return response
        except Exception as e:
            print(u"Fehler beim Abruf von: " + url + " " + str(e))
            return ""

    else:
        try:
            if site and "SJ" in site and db_normal.retrieve("SJ"):
                return ""
            elif site and "MB" in site and db_normal.retrieve("MB"):
                return ""
            elif site and "HW" in site and db_normal.retrieve("HW"):
                return ""
            elif site and "FX" in site and db_normal.retrieve("FX"):
                return ""
            elif site and "HS" in site and db_normal.retrieve("HS"):
                return ""
            elif site and "NK" in site and db_normal.retrieve("NK"):
                return ""
            response = scraper.get(url, timeout=30).text
            return response
        except Exception as e:
            print(u"Fehler beim Abruf von: " + url + " " + str(e))
            return ""


def get_url_headers(url, configfile, dbfile, headers, scraper=False):
    config = RssConfig('RSScrawler', configfile)
    proxy = config.get('proxy')
    if not scraper:
        scraper = cloudscraper.create_scraper()

    db = RssDb(dbfile, 'proxystatus')
    db_normal = RssDb(dbfile, 'normalstatus')
    site = check_is_site(url)
    if proxy:
        try:
            if site and "SJ" in site:
                if db.retrieve("SJ"):
                    if config.get("fallback") and not db_normal.retrieve("SJ"):
                        return [scraper.get(url, headers=headers, timeout=30), scraper]
                    else:
                        return ["", scraper]
            elif site and "MB" in site:
                if db.retrieve("MB"):
                    if config.get("fallback") and not db_normal.retrieve("MB"):
                        return [scraper.get(url, headers=headers, timeout=30), scraper]
                    else:
                        return ["", scraper]
            elif site and "HW" in site:
                if db.retrieve("HW"):
                    if config.get("fallback") and not db_normal.retrieve("HW"):
                        return [scraper.get(url, headers=headers, timeout=30), scraper]
                    else:
                        return ["", scraper]
            elif site and "FX" in site:
                if db.retrieve("FX"):
                    if config.get("fallback") and not db_normal.retrieve("FX"):
                        return [scraper.get(url, headers=headers, timeout=30), scraper]
                    else:
                        return ["", scraper]
            elif site and "HS" in site:
                if db.retrieve("HS"):
                    if config.get("fallback") and not db_normal.retrieve("HS"):
                        return [scraper.get(url, headers=headers, timeout=30), scraper]
                    else:
                        return ["", scraper]
            elif site and "NK" in site:
                if db.retrieve("NK"):
                    if config.get("fallback") and not db_normal.retrieve("NK"):
                        return [scraper.get(url, headers=headers, timeout=30), scraper]
                    else:
                        return ["", scraper]
            proxies = {'http': proxy, 'https': proxy}
            response = scraper.get(url, headers=headers, proxies=proxies, timeout=30)
            return [response, scraper]
        except Exception as e:
            print(u"Fehler beim Abruf von: " + url + " " + str(e))
            return ["", scraper]
    else:
        try:
            if site and "SJ" in site and db_normal.retrieve("SJ"):
                return ["", scraper]
            elif site and "MB" in site and db_normal.retrieve("MB"):
                return ["", scraper]
            elif site and "HW" in site and db_normal.retrieve("HW"):
                return ["", scraper]
            elif site and "FX" in site and db_normal.retrieve("FX"):
                return ["", scraper]
            elif site and "HS" in site and db_normal.retrieve("HS"):
                return ["", scraper]
            elif site and "NK" in site and db_normal.retrieve("NK"):
                return ["", scraper]
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

    db = RssDb(dbfile, 'proxystatus')
    db_normal = RssDb(dbfile, 'normalstatus')
    site = check_is_site(url)
    if proxy:
        try:
            if site and "SJ" in site:
                if db.retrieve("SJ"):
                    if config.get("fallback") and not db_normal.retrieve("SJ"):
                        return scraper.post(url, data, timeout=30).content
                    else:
                        return ""
            elif site and "MB" in site:
                if db.retrieve("MB"):
                    if config.get("fallback") and not db_normal.retrieve("MB"):
                        return scraper.post(url, data, timeout=30).content
                    else:
                        return ""
            elif site and "HW" in site:
                if db.retrieve("HW"):
                    if config.get("fallback") and not db_normal.retrieve("HW"):
                        return scraper.post(url, data, timeout=30).content
                    else:
                        return ""
            elif site and "FX" in site:
                if db.retrieve("FX"):
                    if config.get("fallback") and not db_normal.retrieve("FX"):
                        return scraper.post(url, data, timeout=30).content
                    else:
                        return ""
            elif site and "HS" in site:
                if db.retrieve("HS"):
                    if config.get("fallback") and not db_normal.retrieve("HS"):
                        return scraper.post(url, data, timeout=30).content
                    else:
                        return ""
            elif site and "NK" in site:
                if db.retrieve("NK"):
                    if config.get("fallback") and not db_normal.retrieve("NK"):
                        return scraper.post(url, data, timeout=30).content
                    else:
                        return ""
            proxies = {'http': proxy, 'https': proxy}
            response = scraper.post(url, data, proxies=proxies, timeout=30).content
            return response
        except Exception as e:
            print(u"Fehler beim Abruf von: " + url + " " + str(e))
            return ""
    else:
        try:
            if site and "SJ" in site and db_normal.retrieve("SJ"):
                return ""
            elif site and "MB" in site and db_normal.retrieve("MB"):
                return ""
            elif site and "HW" in site and db_normal.retrieve("HW"):
                return ""
            elif site and "FX" in site and db_normal.retrieve("FX"):
                return ""
            elif site and "HS" in site and db_normal.retrieve("HS"):
                return ""
            elif site and "NK" in site and db_normal.retrieve("NK"):
                return ""
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

    db = RssDb(dbfile, 'proxystatus')
    db_normal = RssDb(dbfile, 'normalstatus')
    site = check_is_site(url)
    if proxy:
        try:
            if site and "SJ" in site:
                if db.retrieve("SJ"):
                    if config.get("fallback") and not db_normal.retrieve("SJ"):
                        return scraper.post(url, json=json, timeout=30).content
                    else:
                        return ""
            elif site and "MB" in site:
                if db.retrieve("MB"):
                    if config.get("fallback") and not db_normal.retrieve("MB"):
                        return scraper.post(url, json=json, timeout=30).content
                    else:
                        return ""
            elif site and "HW" in site:
                if db.retrieve("HW"):
                    if config.get("fallback") and not db_normal.retrieve("HW"):
                        return scraper.post(url, json=json, timeout=30).content
                    else:
                        return ""
            elif site and "FX" in site:
                if db.retrieve("FX"):
                    if config.get("fallback") and not db_normal.retrieve("FX"):
                        return scraper.post(url, json=json, timeout=30).content
                    else:
                        return ""
            elif site and "HS" in site:
                if db.retrieve("HS"):
                    if config.get("fallback") and not db_normal.retrieve("HS"):
                        return scraper.post(url, json=json, timeout=30).content
                    else:
                        return ""
            elif site and "NK" in site:
                if db.retrieve("NK"):
                    if config.get("fallback") and not db_normal.retrieve("NK"):
                        return scraper.post(url, json=json, timeout=30).content
                    else:
                        return ""
            proxies = {'http': proxy, 'https': proxy}
            response = scraper.post(url, json=json, proxies=proxies, timeout=30).content
            return response
        except Exception as e:
            print(u"Fehler beim Abruf von: " + url + " " + str(e))
            return ""
    else:
        try:
            if site and "SJ" in site and db_normal.retrieve("SJ"):
                return ""
            elif site and "MB" in site and db_normal.retrieve("MB"):
                return ""
            elif site and "HW" in site and db_normal.retrieve("HW"):
                return ""
            elif site and "FX" in site and db_normal.retrieve("FX"):
                return ""
            elif site and "HS" in site and db_normal.retrieve("HS"):
                return ""
            elif site and "NK" in site and db_normal.retrieve("NK"):
                return ""
            response = scraper.post(url, json=json, timeout=30).content
            return response
        except Exception as e:
            print(u"Fehler beim Abruf von: " + url + " " + str(e))
            return ""


def get_urls_async(urls, configfile, dbfile, scraper=False):
    if not scraper:
        scraper = cloudscraper.create_scraper()
    results = []

    def load_url(url):
        return get_url(url, configfile, dbfile, scraper)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(load_url, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            future_to_url[future]
            try:
                results.append(future.result())
            except Exception:
                pass
    return [results, scraper]
