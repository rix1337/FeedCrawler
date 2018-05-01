# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

from __future__ import print_function
from builtins import str
import os
import sys

import cfscrape

from rssconfig import RssConfig
from rssdb import RssDb


def checkURL():
    sj_url = "aHR0cDovL3Nlcmllbmp1bmtpZXMub3Jn".decode('base64')
    mb_url = "aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZy8=".decode('base64')
    proxy = RssConfig('RSScrawler').get('proxy')
    scraper = cfscrape.create_scraper(delay=10)
    sj_blocked_proxy = False
    mb_blocked_proxy = False
    if proxy:
        db = RssDb(os.path.join(os.path.dirname(
            sys.argv[0]), "RSScrawler.db"), 'proxystatus')
        proxies = {'http': proxy, 'https': proxy}
        if "block." in str(
                scraper.get(sj_url, proxies=proxies, timeout=30, allow_redirects=False).headers.get("location")):
            print("Der Zugriff auf SJ ist mit der aktuellen Proxy-IP nicht möglich!")
            if RssConfig('RSScrawler').get("fallback"):
                db.store("SJ", "Blocked")
            sj_blocked_proxy = True
        else:
            db.delete("SJ")
        if "<Response [403]>" in str(scraper.get(mb_url, proxies=proxies, timeout=30, allow_redirects=False)):
            print("Der Zugriff auf MB ist mit der aktuellen Proxy-IP nicht möglich!")
            if RssConfig('RSScrawler').get("fallback"):
                db.store("MB", "Blocked")
                mb_blocked_proxy = True
        else:
            db.delete("MB")
    if not proxy or sj_blocked_proxy == True or mb_blocked_proxy == True:
        if "block." in str(scraper.get(sj_url, timeout=30, allow_redirects=False).headers.get("location")):
            print("Der Zugriff auf SJ ist mit der aktuellen IP nicht möglich!")
        if "<Response [403]>" in str(scraper.get(mb_url, timeout=30, allow_redirects=False)):
            print("Der Zugriff auf MB ist mit der aktuellen IP nicht möglich!")
    return


def getURL(url):
    config = RssConfig('RSScrawler')
    proxy = config.get('proxy')
    scraper = cfscrape.create_scraper(delay=10)
    if proxy:
        sj = "c2VyaWVuanVua2llcy5vcmc=".decode('base64')
        mb = "bW92aWUtYmxvZy5vcmc=".decode('base64')
        db = RssDb(os.path.join(os.path.dirname(
            sys.argv[0]), "RSScrawler.db"), 'proxystatus')
        if sj in url:
            if db.retrieve("SJ") and config.get("fallback"):
                return scraper.get(url, timeout=30).content
        elif mb in url:
            if db.retrieve("MB") and config.get("fallback"):
                return scraper.get(url, timeout=30).content
        proxies = {'http': proxy, 'https': proxy}
        return scraper.get(url, proxies=proxies, timeout=30).content
    else:
        return scraper.get(url, timeout=30).content


def postURL(url, data):
    proxy = RssConfig('RSScrawler').get('proxy')
    if proxy:
        proxies = {'http': proxy, 'https': proxy}
        scraper = cfscrape.create_scraper(delay=10)
        return scraper.post(url, data, proxies=proxies, timeout=30).content
    else:
        scraper = cfscrape.create_scraper(delay=10)
        return scraper.post(url, data, timeout=30).content
