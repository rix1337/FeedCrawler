# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337

import cloudscraper
import codecs
import concurrent.futures
import datetime
import functools
import hashlib
import pickle

from feedcrawler.common import check_is_site
from feedcrawler.config import CrawlerConfig
from feedcrawler.db import FeedDb


class DbFileMissingExpection(Exception):
    """Exception raised for missing dbfile path.

    Attributes:
        url -- url(s) from the request that caused the error
        message -- explanation of the error
    """

    def __init__(self, url, message="The dbfile parameter required for caching this request is missing!"):
        self.url = url
        self.message = message
        super().__init__(self.message + ", url(s): " + self.url)


def cache(func):
    """Decorator that caches a functions return values for specific arguments, excluding the scraper object."""

    @functools.wraps(func)
    def cache_returned_values(*args, **kwargs):
        to_hash = ""
        dbfile = False
        for a in args:
            # The path to the db file which we will use for caching is always one of the arguments
            if isinstance(a, str) and "FeedCrawler.db" in a:
                dbfile = a
            # Ignore the scraper object when caching
            if not isinstance(a, cloudscraper.CloudScraper):
                # convert all arguments to hashable strings
                to_hash += codecs.encode(pickle.dumps(a), "base64").decode()
        # This hash is based on all arguments of the request
        hashed = hashlib.sha256(to_hash.encode('ascii', 'ignore')).hexdigest()

        if dbfile:
            # Check if there is a cached request for this hash
            cached = FeedDb(dbfile, 'cached_requests').retrieve(hashed)
            if cached:
                # Unpack and return the cached result instead of processing the request
                return pickle.loads(codecs.decode(cached.encode(), "base64"))
            else:
                #
                value = func(*args, **kwargs)
                FeedDb(dbfile, 'cached_requests').store(hashed, codecs.encode(pickle.dumps(value), "base64").decode())
                return value
        raise DbFileMissingExpection(str(args[0]))

    return cache_returned_values


def check_url(configfile, dbfile, scraper=False):
    hostnames = CrawlerConfig('Hostnames', configfile)
    sj = hostnames.get('sj')
    dj = hostnames.get('dj')
    sf = hostnames.get('sf')
    by = hostnames.get('by')
    dw = hostnames.get('dw')
    fx = hostnames.get('fx')
    nk = hostnames.get('nk')
    ww = hostnames.get('ww')
    dd = hostnames.get('dd')

    if not scraper:
        scraper = cloudscraper.create_scraper()

    sj_url = 'https://' + sj
    dj_url = 'https://' + dj
    sf_url = 'https://' + sf
    by_url = 'https://' + by
    dw_url = 'https://' + dw
    fx_url = 'https://' + fx
    nk_url = 'https://' + nk
    ww_url = 'https://' + ww
    dd_url = 'https://' + dd

    sj_blocked_proxy = False
    dj_blocked_proxy = False
    sf_blocked_proxy = False
    by_blocked_proxy = False
    dw_blocked_proxy = False
    fx_blocked_proxy = False
    nk_blocked_proxy = False
    ww_blocked_proxy = False
    dd_blocked_proxy = False
    sj_blocked = False
    dj_blocked = False
    sf_blocked = False
    by_blocked = False
    dw_blocked = False
    fx_blocked = False
    nk_blocked = False
    ww_blocked = False
    dd_blocked = False

    db = FeedDb(dbfile, 'proxystatus')
    db.delete("SJ")
    db.delete("DJ")
    db.delete("SF")
    db.delete("BY")
    db.delete("DW")
    db.delete("FX")
    db.delete("NK")
    db.delete("WW")
    db.delete("DD")
    db_normal = FeedDb(dbfile, 'normalstatus')
    db_normal.delete("SJ")
    db_normal.delete("DJ")
    db_normal.delete("SF")
    db_normal.delete("BY")
    db_normal.delete("DW")
    db_normal.delete("FX")
    db_normal.delete("NK")
    db_normal.delete("WW")
    db_normal.delete("DD")

    proxy = CrawlerConfig('FeedCrawler', configfile).get('proxy')
    fallback = CrawlerConfig('FeedCrawler', configfile).get('fallback')

    if proxy:
        proxies = {'http': proxy, 'https': proxy}

        if not sj:
            db.store("SJ", "Blocked")
        else:
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

        if not dj:
            db.store("DJ", "Blocked")
        else:
            try:
                if "block." in str(
                        scraper.get(dj_url, proxies=proxies, timeout=30,
                                    allow_redirects=False).headers.get("location")):
                    dj_blocked_proxy = True
                else:
                    db.delete("DJ")
            except:
                dj_blocked_proxy = True
            if dj_blocked_proxy:
                print(u"Der Zugriff auf DJ ist mit der aktuellen Proxy-IP nicht möglich!")
                db.store("DJ", "Blocked")
                scraper = cloudscraper.create_scraper()

        if not sf:
            db.store("SF", "Blocked")
        else:
            try:
                delta = datetime.datetime.now().strftime("%Y-%m-%d")
                sf_test = scraper.get(sf_url + '/updates/' + delta, proxies=proxies, timeout=30, allow_redirects=False)
                if not sf_test.text or sf_test.status_code is not (
                        200 or 304) or '<h3><a href="/' not in sf_test.text:
                    sf_blocked_proxy = True
                else:
                    db.delete("SF")
            except:
                sf_blocked_proxy = True
            if sf_blocked_proxy:
                print(u"Der Zugriff auf SF ist mit der aktuellen Proxy-IP nicht möglich!")
                db.store("SF", "Blocked")
                scraper = cloudscraper.create_scraper()

        if not by:
            db.store("BY", "Blocked")
        else:
            try:
                if scraper.get(by_url, proxies=proxies, timeout=30, allow_redirects=False).status_code == 403:
                    by_blocked_proxy = True
                else:
                    db.delete("BY")
            except:
                by_blocked_proxy = True
            if by_blocked_proxy:
                print(u"Der Zugriff auf BY ist mit der aktuellen Proxy-IP nicht möglich!")
                db.store("BY", "Blocked")
                scraper = cloudscraper.create_scraper()

        if not dw:
            db.store("DW", "Blocked")
        else:
            try:
                if scraper.get(dw_url, proxies=proxies, timeout=30, allow_redirects=False).status_code == 403:
                    dw_blocked_proxy = True
                else:
                    db.delete("DW")
            except:
                dw_blocked_proxy = True
            if dw_blocked_proxy:
                print(u"Der Zugriff auf DW ist mit der aktuellen Proxy-IP nicht möglich!")
                db.store("DW", "Blocked")
                scraper = cloudscraper.create_scraper()

        if not fx:
            db.store("FX", "Blocked")
        else:
            try:
                if scraper.get(fx_url, proxies=proxies, timeout=30, allow_redirects=False).status_code == 403:
                    fx_blocked_proxy = True
                else:
                    db.delete("FX")
            except:
                fx_blocked_proxy = True
            if fx_blocked_proxy:
                print(u"Der Zugriff auf FX ist mit der aktuellen Proxy-IP nicht möglich!")
                db.store("FX", "Blocked")
                scraper = cloudscraper.create_scraper()

        if not nk:
            db.store("NK", "Blocked")
        else:
            try:
                if scraper.get(nk_url, proxies=proxies, timeout=30, allow_redirects=False).status_code == 403:
                    nk_blocked_proxy = True
                else:
                    db.delete("NK")
            except:
                nk_blocked_proxy = True
            if nk_blocked_proxy:
                print(u"Der Zugriff auf NK ist mit der aktuellen Proxy-IP nicht möglich!")
                db.store("NK", "Blocked")
                scraper = cloudscraper.create_scraper()

        if not ww:
            db.store("WW", "Blocked")
        else:
            try:
                ww_test = scraper.post(ww_url + "/ajax", data="p=1&t=l&q=1", proxies=proxies, timeout=30,
                                       allow_redirects=False)
                if not ww_test.text or ww_test.status_code is not (
                        200 or 304) or '<span class="main-rls">' not in ww_test.text:
                    ww_blocked_proxy = True
                else:
                    db.delete("WW")
            except:
                ww_blocked_proxy = True
            if ww_blocked_proxy:
                print(u"Der Zugriff auf WW ist mit der aktuellen Proxy-IP nicht möglich!")
                db.store("WW", "Blocked")
                scraper = cloudscraper.create_scraper()

        if not dd:
            db.store("DD", "Blocked")
        else:
            try:
                if scraper.get(dd_url, proxies=proxies, timeout=30, allow_redirects=False).status_code == 403:
                    dd_blocked_proxy = True
                else:
                    db.delete("DD")
            except:
                dd_blocked_proxy = True
            if dd_blocked_proxy:
                print(u"Der Zugriff auf DD ist mit der aktuellen Proxy-IP nicht möglich!")
                db.store("DD", "Blocked")
                scraper = cloudscraper.create_scraper()

    if not proxy or (proxy and sj_blocked_proxy and fallback):
        if not sj:
            db.store("SJ", "Blocked")
        else:
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

    if not proxy or (proxy and dj_blocked_proxy and fallback):
        if not dj:
            db.store("DJ", "Blocked")
        else:
            try:
                if "block." in str(
                        scraper.get(dj_url, timeout=30, allow_redirects=False).headers.get(
                            "location")):
                    dj_blocked = True
            except:
                dj_blocked = True
            if dj_blocked:
                db_normal.store("DJ", "Blocked")
                print(u"Der Zugriff auf DJ ist mit der aktuellen IP nicht möglich!")

    if not proxy or (proxy and sf_blocked_proxy and fallback):
        if not sf:
            db.store("SF", "Blocked")
        else:
            try:
                delta = datetime.datetime.now().strftime("%Y-%m-%d")
                sf_test = scraper.get(sf_url + '/updates/' + delta, timeout=30, allow_redirects=False)
                if not sf_test.text or sf_test.status_code is not (
                        200 or 304) or '<h3><a href="/' not in sf_test.text:
                    sf_blocked = True
            except:
                sf_blocked = True
            if sf_blocked:
                db_normal.store("SF", "Blocked")
                print(u"Der Zugriff auf SF ist mit der aktuellen IP nicht möglich!")

    if not proxy or (proxy and by_blocked_proxy and fallback):
        if not by:
            db.store("BY", "Blocked")
        else:
            try:
                if scraper.get(by_url, timeout=30, allow_redirects=False).status_code == 403:
                    by_blocked = True
            except:
                by_blocked = True
            if by_blocked:
                db_normal.store("BY", "Blocked")
                print(u"Der Zugriff auf BY ist mit der aktuellen IP nicht möglich!")

    if not proxy or (proxy and dw_blocked_proxy and fallback):
        if not dw:
            db.store("DW", "Blocked")
        else:
            try:
                if scraper.get(dw_url, timeout=30, allow_redirects=False).status_code == 403:
                    dw_blocked = True
            except:
                dw_blocked = True
            if dw_blocked:
                db_normal.store("DW", "Blocked")
                print(u"Der Zugriff auf DW ist mit der aktuellen IP nicht möglich!")

    if not proxy or (proxy and fx_blocked_proxy and fallback):
        if not fx:
            db.store("FX", "Blocked")
        else:
            try:
                if scraper.get(fx_url, timeout=30, allow_redirects=False).status_code == 403:
                    fx_blocked = True
            except:
                fx_blocked = True
            if fx_blocked:
                db_normal.store("FX", "Blocked")
                print(u"Der Zugriff auf FX ist mit der aktuellen IP nicht möglich!")

    if not proxy or (proxy and nk_blocked_proxy and fallback):
        if not nk:
            db.store("NK", "Blocked")
        else:
            try:
                if scraper.get(nk_url, timeout=30, allow_redirects=False).status_code == 403:
                    nk_blocked = True
            except:
                nk_blocked = True
            if nk_blocked:
                db_normal.store("NK", "Blocked")
                print(u"Der Zugriff auf NK ist mit der aktuellen IP nicht möglich!")

    if not proxy or (proxy and ww_blocked_proxy and fallback):
        if not ww:
            db.store("WW", "Blocked")
        else:
            try:
                ww_test = scraper.post(ww_url + "/ajax", data="p=1&t=l&q=1", timeout=30, allow_redirects=False)
                if not ww_test.text or ww_test.status_code is not (
                        200 or 304) or '<span class="main-rls">' not in ww_test.text:
                    ww_blocked = True
            except:
                ww_blocked = True
            if ww_blocked:
                db_normal.store("WW", "Blocked")
                print(u"Der Zugriff auf WW ist mit der aktuellen IP nicht möglich!")

    if not proxy or (proxy and dd_blocked_proxy and fallback):
        if not dd:
            db.store("DD", "Blocked")
        else:
            try:
                if scraper.get(dd_url, timeout=30, allow_redirects=False).status_code == 403:
                    dd_blocked = True
            except:
                dd_blocked = True
            if dd_blocked:
                db_normal.store("DD", "Blocked")
                print(u"Der Zugriff auf DD ist mit der aktuellen IP nicht möglich!")

    return scraper


@cache
def get_url(url, configfile, dbfile, scraper=False):
    config = CrawlerConfig('FeedCrawler', configfile)
    proxy = config.get('proxy')
    if not scraper:
        scraper = cloudscraper.create_scraper()

    db = FeedDb(dbfile, 'proxystatus')
    db_normal = FeedDb(dbfile, 'normalstatus')
    site = check_is_site(url, configfile)

    if proxy:
        try:
            if site and "SJ" in site:
                if db.retrieve("SJ"):
                    if config.get("fallback") and not db_normal.retrieve("SJ"):
                        return scraper.get(url, timeout=30).text
                    else:
                        return ""
            elif site and "DJ" in site:
                if db.retrieve("DJ"):
                    if config.get("fallback") and not db_normal.retrieve("DJ"):
                        return scraper.get(url, timeout=30).text
                    else:
                        return ""
            elif site and "SF" in site:
                if db.retrieve("SF"):
                    if config.get("fallback") and not db_normal.retrieve("SF"):
                        return scraper.get(url, timeout=30).text
                    else:
                        return ""
            elif site and "BY" in site:
                if db.retrieve("BY"):
                    if config.get("fallback") and not db_normal.retrieve("BY"):
                        return scraper.get(url, timeout=30).text
                    else:
                        return ""
            elif site and "DW" in site:
                if db.retrieve("DW"):
                    if config.get("fallback") and not db_normal.retrieve("DW"):
                        return scraper.get(url, timeout=30).text
                    else:
                        return ""
            elif site and "FX" in site:
                if db.retrieve("FX"):
                    if config.get("fallback") and not db_normal.retrieve("FX"):
                        return scraper.get(url, timeout=30).text
                    else:
                        return ""
            elif site and "NK" in site:
                if db.retrieve("NK"):
                    if config.get("fallback") and not db_normal.retrieve("NK"):
                        return scraper.get(url, timeout=30).text
                    else:
                        return ""
            elif site and "WW" in site:
                if db.retrieve("WW"):
                    if config.get("fallback") and not db_normal.retrieve("WW"):
                        return scraper.get(url, timeout=30).text
                    else:
                        return ""
            elif site and "DD" in site:
                if db.retrieve("DD"):
                    if config.get("fallback") and not db_normal.retrieve("DD"):
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
            elif site and "DJ" in site and db_normal.retrieve("DJ"):
                return ""
            elif site and "SF" in site and db_normal.retrieve("SF"):
                return ""
            elif site and "BY" in site and db_normal.retrieve("BY"):
                return ""
            elif site and "DW" in site and db_normal.retrieve("DW"):
                return ""
            elif site and "FX" in site and db_normal.retrieve("FX"):
                return ""
            elif site and "NK" in site and db_normal.retrieve("NK"):
                return ""
            elif site and "WW" in site and db_normal.retrieve("WW"):
                return ""
            elif site and "DD" in site and db_normal.retrieve("DD"):
                return ""
            response = scraper.get(url, timeout=30).text
            return response
        except Exception as e:
            print(u"Fehler beim Abruf von: " + url + " " + str(e))
            return ""


@cache
def get_url_headers(url, configfile, dbfile, headers, scraper=False):
    config = CrawlerConfig('FeedCrawler', configfile)
    proxy = config.get('proxy')
    if not scraper:
        scraper = cloudscraper.create_scraper()

    db = FeedDb(dbfile, 'proxystatus')
    db_normal = FeedDb(dbfile, 'normalstatus')
    site = check_is_site(url, configfile)

    if proxy:
        try:
            if site and "SJ" in site:
                if db.retrieve("SJ"):
                    if config.get("fallback") and not db_normal.retrieve("SJ"):
                        return [scraper.get(url, headers=headers, timeout=30), scraper]
                    else:
                        return ["", scraper]
            elif site and "DJ" in site:
                if db.retrieve("DJ"):
                    if config.get("fallback") and not db_normal.retrieve("DJ"):
                        return [scraper.get(url, headers=headers, timeout=30), scraper]
                    else:
                        return ["", scraper]
            elif site and "SF" in site:
                if db.retrieve("SF"):
                    if config.get("fallback") and not db_normal.retrieve("SF"):
                        return [scraper.get(url, headers=headers, timeout=30), scraper]
                    else:
                        return ["", scraper]
            elif site and "BY" in site:
                if db.retrieve("BY"):
                    if config.get("fallback") and not db_normal.retrieve("BY"):
                        return [scraper.get(url, headers=headers, timeout=30), scraper]
                    else:
                        return ["", scraper]
            elif site and "DW" in site:
                if db.retrieve("DW"):
                    if config.get("fallback") and not db_normal.retrieve("DW"):
                        return [scraper.get(url, headers=headers, timeout=30), scraper]
                    else:
                        return ["", scraper]
            elif site and "FX" in site:
                if db.retrieve("FX"):
                    if config.get("fallback") and not db_normal.retrieve("FX"):
                        return [scraper.get(url, headers=headers, timeout=30), scraper]
                    else:
                        return ["", scraper]
            elif site and "NK" in site:
                if db.retrieve("NK"):
                    if config.get("fallback") and not db_normal.retrieve("NK"):
                        return [scraper.get(url, headers=headers, timeout=30), scraper]
                    else:
                        return ["", scraper]
            elif site and "WW" in site:
                if db.retrieve("WW"):
                    if config.get("fallback") and not db_normal.retrieve("WW"):
                        return [scraper.get(url, headers=headers, timeout=30), scraper]
                    else:
                        return ["", scraper]
            elif site and "DD" in site:
                if db.retrieve("DD"):
                    if config.get("fallback") and not db_normal.retrieve("DD"):
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
            elif site and "DJ" in site and db_normal.retrieve("DJ"):
                return ["", scraper]
            elif site and "SF" in site and db_normal.retrieve("SF"):
                return ["", scraper]
            elif site and "BY" in site and db_normal.retrieve("BY"):
                return ["", scraper]
            elif site and "DW" in site and db_normal.retrieve("DW"):
                return ["", scraper]
            elif site and "FX" in site and db_normal.retrieve("FX"):
                return ["", scraper]
            elif site and "NK" in site and db_normal.retrieve("NK"):
                return ["", scraper]
            elif site and "WW" in site and db_normal.retrieve("WW"):
                return ["", scraper]
            elif site and "DD" in site and db_normal.retrieve("DD"):
                return ["", scraper]
            response = scraper.get(url, headers=headers, timeout=30)
            return [response, scraper]
        except Exception as e:
            print(u"Fehler beim Abruf von: " + url + " " + str(e))
            return ["", scraper]


@cache
def get_redirected_url(url, configfile, dbfile, scraper=False):
    config = CrawlerConfig('FeedCrawler', configfile)
    proxy = config.get('proxy')
    if not scraper:
        scraper = cloudscraper.create_scraper()

    db = FeedDb(dbfile, 'proxystatus')
    db_normal = FeedDb(dbfile, 'normalstatus')
    site = check_is_site(url, configfile)

    if proxy:
        try:
            if site and "SJ" in site:
                if db.retrieve("SJ"):
                    if config.get("fallback") and not db_normal.retrieve("SJ"):
                        return scraper.get(url, allow_redirects=False, timeout=30).headers._store["location"][1]
                    else:
                        return url
            elif site and "DJ" in site:
                if db.retrieve("DJ"):
                    if config.get("fallback") and not db_normal.retrieve("DJ"):
                        return scraper.get(url, allow_redirects=False, timeout=30).headers._store["location"][1]
                    else:
                        return url
            elif site and "SF" in site:
                if db.retrieve("SF"):
                    if config.get("fallback") and not db_normal.retrieve("SF"):
                        return scraper.get(url, allow_redirects=False, timeout=30).headers._store["location"][1]
                    else:
                        return url
            elif site and "BY" in site:
                if db.retrieve("BY"):
                    if config.get("fallback") and not db_normal.retrieve("BY"):
                        return scraper.get(url, allow_redirects=False, timeout=30).headers._store["location"][1]
                    else:
                        return url
            elif site and "DW" in site:
                if db.retrieve("DW"):
                    if config.get("fallback") and not db_normal.retrieve("DW"):
                        return scraper.get(url, allow_redirects=False, timeout=30).headers._store["location"][1]
                    else:
                        return url
            elif site and "FX" in site:
                if db.retrieve("FX"):
                    if config.get("fallback") and not db_normal.retrieve("FX"):
                        return scraper.get(url, allow_redirects=False, timeout=30).headers._store["location"][1]
                    else:
                        return url
            elif site and "NK" in site:
                if db.retrieve("NK"):
                    if config.get("fallback") and not db_normal.retrieve("NK"):
                        return scraper.get(url, allow_redirects=False, timeout=30).headers._store["location"][1]
                    else:
                        return url
            elif site and "WW" in site:
                return url
            elif site and "DD" in site:
                if db.retrieve("DD"):
                    if config.get("fallback") and not db_normal.retrieve("DD"):
                        return scraper.get(url, allow_redirects=False, timeout=30).headers._store["location"][1]
                    else:
                        return url
            proxies = {'http': proxy, 'https': proxy}
            response = scraper.get(url, allow_redirects=False, proxies=proxies, timeout=30).headers._store["location"][
                1]
            return response
        except Exception as e:
            print(u"Fehler beim Abruf von: " + url + " " + str(e))
            return url
    else:
        try:
            if site and "SJ" in site and db_normal.retrieve("SJ"):
                return url
            elif site and "DJ" in site and db_normal.retrieve("DJ"):
                return url
            elif site and "SF" in site and db_normal.retrieve("SF"):
                return url
            elif site and "BY" in site and db_normal.retrieve("BY"):
                return url
            elif site and "DW" in site and db_normal.retrieve("DW"):
                return url
            elif site and "FX" in site and db_normal.retrieve("FX"):
                return url
            elif site and "NK" in site and db_normal.retrieve("NK"):
                return url
            elif site and "WW" in site:
                return url
            elif site and "DD" in site and db_normal.retrieve("DD"):
                return url
            response = scraper.get(url, allow_redirects=False, timeout=30).headers._store["location"][1]
            return response
        except Exception as e:
            print(u"Fehler beim Abruf von: " + url + " " + str(e))
            return url


@cache
def post_url(url, configfile, dbfile, data, scraper=False):
    config = CrawlerConfig('FeedCrawler', configfile)
    proxy = config.get('proxy')
    if not scraper:
        scraper = cloudscraper.create_scraper()

    db = FeedDb(dbfile, 'proxystatus')
    db_normal = FeedDb(dbfile, 'normalstatus')
    site = check_is_site(url, configfile)

    if proxy:
        try:
            if site and "SJ" in site:
                if db.retrieve("SJ"):
                    if config.get("fallback") and not db_normal.retrieve("SJ"):
                        return scraper.post(url, data, timeout=30).content
                    else:
                        return ""
            elif site and "DJ" in site:
                if db.retrieve("DJ"):
                    if config.get("fallback") and not db_normal.retrieve("DJ"):
                        return scraper.post(url, data, timeout=30).content
                    else:
                        return ""
            elif site and "SF" in site:
                if db.retrieve("SF"):
                    if config.get("fallback") and not db_normal.retrieve("SF"):
                        return scraper.post(url, data, timeout=30).content
                    else:
                        return ""
            elif site and "BY" in site:
                if db.retrieve("BY"):
                    if config.get("fallback") and not db_normal.retrieve("BY"):
                        return scraper.post(url, data, timeout=30).content
                    else:
                        return ""
            elif site and "DW" in site:
                if db.retrieve("DW"):
                    if config.get("fallback") and not db_normal.retrieve("DW"):
                        return scraper.post(url, data, timeout=30).content
                    else:
                        return ""
            elif site and "FX" in site:
                if db.retrieve("FX"):
                    if config.get("fallback") and not db_normal.retrieve("FX"):
                        return scraper.post(url, data, timeout=30).content
                    else:
                        return ""
            elif site and "NK" in site:
                if db.retrieve("NK"):
                    if config.get("fallback") and not db_normal.retrieve("NK"):
                        return scraper.post(url, data, timeout=30).content
                    else:
                        return ""
            elif site and "WW" in site:
                if db.retrieve("WW"):
                    if config.get("fallback") and not db_normal.retrieve("WW"):
                        return scraper.post(url, data, timeout=30).content
                    else:
                        return ""
            elif site and "DD" in site:
                if db.retrieve("DD"):
                    if config.get("fallback") and not db_normal.retrieve("DD"):
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
            elif site and "DJ" in site and db_normal.retrieve("DJ"):
                return ""
            elif site and "SF" in site and db_normal.retrieve("SF"):
                return ""
            elif site and "BY" in site and db_normal.retrieve("BY"):
                return ""
            elif site and "DW" in site and db_normal.retrieve("DW"):
                return ""
            elif site and "FX" in site and db_normal.retrieve("FX"):
                return ""
            elif site and "NK" in site and db_normal.retrieve("NK"):
                return ""
            elif site and "WW" in site and db_normal.retrieve("WW"):
                return ""
            elif site and "DD" in site and db_normal.retrieve("DD"):
                return ""
            response = scraper.post(url, data, timeout=30).content
            return response
        except Exception as e:
            print(u"Fehler beim Abruf von: " + url + " " + str(e))
            return ""


@cache
def post_url_headers(url, configfile, dbfile, headers, data, scraper=False):
    config = CrawlerConfig('FeedCrawler', configfile)
    proxy = config.get('proxy')
    if not scraper:
        scraper = cloudscraper.create_scraper()

    db = FeedDb(dbfile, 'proxystatus')
    db_normal = FeedDb(dbfile, 'normalstatus')
    site = check_is_site(url, configfile)

    if proxy:
        try:
            if site and "SJ" in site:
                if db.retrieve("SJ"):
                    if config.get("fallback") and not db_normal.retrieve("SJ"):
                        return [scraper.post(url, data, headers=headers, timeout=30), scraper]
                    else:
                        return ["", scraper]
            elif site and "DJ" in site:
                if db.retrieve("DJ"):
                    if config.get("fallback") and not db_normal.retrieve("DJ"):
                        return [scraper.post(url, data, headers=headers, timeout=30), scraper]
                    else:
                        return ["", scraper]
            elif site and "SF" in site:
                if db.retrieve("SF"):
                    if config.get("fallback") and not db_normal.retrieve("SF"):
                        return [scraper.post(url, data, headers=headers, timeout=30), scraper]
                    else:
                        return ["", scraper]
            elif site and "BY" in site:
                if db.retrieve("BY"):
                    if config.get("fallback") and not db_normal.retrieve("BY"):
                        return [scraper.post(url, data, headers=headers, timeout=30), scraper]
                    else:
                        return ["", scraper]
            elif site and "DW" in site:
                if db.retrieve("DW"):
                    if config.get("fallback") and not db_normal.retrieve("DW"):
                        return [scraper.post(url, data, headers=headers, timeout=30), scraper]
                    else:
                        return ["", scraper]
            elif site and "FX" in site:
                if db.retrieve("FX"):
                    if config.get("fallback") and not db_normal.retrieve("FX"):
                        return [scraper.post(url, data, headers=headers, timeout=30), scraper]
                    else:
                        return ["", scraper]
            elif site and "NK" in site:
                if db.retrieve("NK"):
                    if config.get("fallback") and not db_normal.retrieve("NK"):
                        return [scraper.post(url, data, headers=headers, timeout=30), scraper]
                    else:
                        return ["", scraper]
            elif site and "WW" in site:
                if db.retrieve("WW"):
                    if config.get("fallback") and not db_normal.retrieve("WW"):
                        return [scraper.post(url, data, headers=headers, timeout=30), scraper]
                    else:
                        return ["", scraper]
            elif site and "DD" in site:
                if db.retrieve("DD"):
                    if config.get("fallback") and not db_normal.retrieve("DD"):
                        return [scraper.post(url, data, headers=headers, timeout=30), scraper]
                    else:
                        return ["", scraper]
            proxies = {'http': proxy, 'https': proxy}
            response = scraper.post(url, data, headers=headers, proxies=proxies, timeout=30)
            return [response, scraper]
        except Exception as e:
            print(u"Fehler beim Abruf von: " + url + " " + str(e))
            return ["", scraper]
    else:
        try:
            if site and "SJ" in site and db_normal.retrieve("SJ"):
                return ["", scraper]
            elif site and "DJ" in site and db_normal.retrieve("DJ"):
                return ["", scraper]
            elif site and "SF" in site and db_normal.retrieve("SF"):
                return ["", scraper]
            elif site and "BY" in site and db_normal.retrieve("BY"):
                return ["", scraper]
            elif site and "DW" in site and db_normal.retrieve("DW"):
                return ["", scraper]
            elif site and "FX" in site and db_normal.retrieve("FX"):
                return ["", scraper]
            elif site and "NK" in site and db_normal.retrieve("NK"):
                return ["", scraper]
            elif site and "WW" in site and db_normal.retrieve("WW"):
                return ["", scraper]
            elif site and "DD" in site and db_normal.retrieve("DD"):
                return ["", scraper]
            response = scraper.post(url, data, headers=headers, timeout=30)
            return [response, scraper]
        except Exception as e:
            print(u"Fehler beim Abruf von: " + url + " " + str(e))
            return ["", scraper]


@cache
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