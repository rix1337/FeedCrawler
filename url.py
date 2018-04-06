# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import cfscrape
import time
import os
import sys

from rssconfig import RssConfig
from rssdb import CheckDb


def checkURL():
    sj_url = "aHR0cDovL3Nlcmllbmp1bmtpZXMub3Jn".decode('base64')
    mb_url = "aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZy8=".decode('base64')
    proxy = RssConfig('RSScrawler').get('proxy')
    scraper = cfscrape.create_scraper(delay=10)
    db = CheckDb(os.path.join(os.path.dirname(
        sys.argv[0]), "Einstellungen/Downloads/Downloads.db"))
    sj_blocked_proxy = False
    mb_blocked_proxy = False
    if proxy:
        proxies = {'http': proxy, 'https': proxy}
        if "block." in str(scraper.get(sj_url, proxies=proxies, timeout=30, allow_redirects=False).headers.get("location")):
            print "Der Zugriff auf SJ ist mit der aktuellen Proxy-IP nicht möglich!"
            if RssConfig('RSScrawler').get("fallback"):
                db.store("SJ", "Blocked")
            sj_blocked_proxy = True
        else:
            db.delete("SJ")
        if "<Response [403]>" in str(scraper.get(mb_url, proxies=proxies, timeout=30, allow_redirects=False)):
            print "Der Zugriff auf MB ist mit der aktuellen Proxy-IP nicht möglich!"
            if RssConfig('RSScrawler').get("fallback"):
                db.store("MB", "Blocked")
                mb_blocked_proxy = True
        else:
            db.delete("MB")
    if not proxy or sj_blocked_proxy == True or mb_blocked_proxy == True:
        if "block." in str(scraper.get(sj_url, timeout=30, allow_redirects=False).headers.get("location")):
            print "Der Zugriff auf SJ ist mit der aktuellen IP nicht möglich!"
        if "<Response [403]>" in str(scraper.get(mb_url, timeout=30, allow_redirects=False)):
            print "Der Zugriff auf MB ist mit der aktuellen IP nicht möglich!"
    return


def getURL(url):
    proxy = RssConfig('RSScrawler').get('proxy')
    scraper = cfscrape.create_scraper(delay=10)
    if proxy:
        db = CheckDb(os.path.join(os.path.dirname(
            sys.argv[0]), "Einstellungen/Downloads/Downloads.db"))
        # TODO if db.retrieve("SJ") and serienjunkies.org in url use no proxies
        # TODO if db.retrieve("MB") and movie-blog.org in url use no proxies
        if "movie-blog.org" in url:
            if db.retrieve("MB"):
                print "Not using proxy"
                return scraper.get(url, timeout=30).content
        proxies = {'http': proxy, 'https': proxy}
        return scraper.get(url, proxies=proxies, timeout=30).content
    else:
        return scraper.get(url, timeout=30).content


def postURL(url, data):
    proxy = RssConfig('RSScrawler').get('proxy')
    if proxy:
        db = CheckDb(os.path.join(os.path.dirname(
            sys.argv[0]), "Einstellungen/Downloads/Downloads.db"))
        proxies = {'http': proxy, 'https': proxy}
        scraper = cfscrape.create_scraper(delay=10)
        return scraper.post(url, data, proxies=proxies, timeout=30).content
    else:
        scraper = cfscrape.create_scraper(delay=10)
        return scraper.post(url, data, timeout=30).content
