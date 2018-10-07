# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import os
import sys

import cfscrape

from rsscrawler.common import decode_base64
from rsscrawler.rssconfig import RssConfig
from rsscrawler.rssdb import RssDb


def checkURL(configfile):
    sj_url = decode_base64("aHR0cDovL3Nlcmllbmp1bmtpZXMub3Jn")
    mb_url = decode_base64("aHR0cDovL21vdmllLWJsb2cub3JnLw==")
    proxy = RssConfig('RSScrawler', configfile).get('proxy')
    scraper = cfscrape.create_scraper(delay=10)
    sj_blocked_proxy = False
    mb_blocked_proxy = False
    if proxy:
        db = RssDb(os.path.join(os.path.dirname(
            sys.argv[0]), "RSScrawler.db"), 'proxystatus')
        proxies = {'http': proxy, 'https': proxy}
        if "block." in str(
                scraper.get(sj_url, proxies=proxies, timeout=30, allow_redirects=False).headers.get("location")):
            print(u"Der Zugriff auf SJ ist mit der aktuellen Proxy-IP nicht möglich!")
            if RssConfig('RSScrawler', configfile).get("fallback"):
                db.store("SJ", "Blocked")
            sj_blocked_proxy = True
        else:
            db.delete("SJ")
        if "<Response [403]>" in str(scraper.get(mb_url, proxies=proxies, timeout=30, allow_redirects=False)):
            print(u"Der Zugriff auf MB ist mit der aktuellen Proxy-IP nicht möglich!")
            if RssConfig('RSScrawler', configfile).get("fallback"):
                db.store("MB", "Blocked")
                mb_blocked_proxy = True
        else:
            db.delete("MB")
    if not proxy or sj_blocked_proxy == True or mb_blocked_proxy == True:
        if "block." in str(scraper.get(sj_url, timeout=30, allow_redirects=False).headers.get("location")):
            print(u"Der Zugriff auf SJ ist mit der aktuellen IP nicht möglich!")
        if "<Response [403]>" in str(scraper.get(mb_url, timeout=30, allow_redirects=False)):
            print(u"Der Zugriff auf MB ist mit der aktuellen IP nicht möglich!")
    return


def getURL(url, configfile):
    config = RssConfig('RSScrawler', configfile)
    proxy = config.get('proxy')
    scraper = cfscrape.create_scraper(delay=10)
    if proxy:
        sj = decode_base64("c2VyaWVuanVua2llcy5vcmc=")
        mb = decode_base64("bW92aWUtYmxvZy5vcmc=")
        db = RssDb(os.path.join(os.path.dirname(
            sys.argv[0]), "RSScrawler.db"), 'proxystatus')
        if sj in url:
            if db.retrieve("SJ") and config.get("fallback"):
                return scraper.get(url, timeout=30).text
        elif mb in url:
            if db.retrieve("MB") and config.get("fallback"):
                return scraper.get(url, timeout=30).text
        proxies = {'http': proxy, 'https': proxy}
        return scraper.get(url, proxies=proxies, timeout=30).text
    else:
        return scraper.get(url, timeout=30).text


def getURLObject(url, configfile, headers):
    config = RssConfig('RSScrawler', configfile)
    proxy = config.get('proxy')
    scraper = cfscrape.create_scraper(delay=10)
    if proxy:
        sj = decode_base64("c2VyaWVuanVua2llcy5vcmc=")
        mb = decode_base64("bW92aWUtYmxvZy5vcmc=")
        db = RssDb(os.path.join(os.path.dirname(
            sys.argv[0]), "RSScrawler.db"), 'proxystatus')
        if sj in url:
            if db.retrieve("SJ") and config.get("fallback"):
                return scraper.get(url, headers=headers, timeout=30)
        elif mb in url:
            if db.retrieve("MB") and config.get("fallback"):
                return scraper.get(url, headers=headers, timeout=30)
        proxies = {'http': proxy, 'https': proxy}
        return scraper.get(url, headers=headers, proxies=proxies, timeout=30)
    else:
        return scraper.get(url, headers=headers, timeout=30)


def postURL(url, configfile, data):
    proxy = RssConfig('RSScrawler', configfile).get('proxy')
    if proxy:
        proxies = {'http': proxy, 'https': proxy}
        scraper = cfscrape.create_scraper(delay=10)
        return scraper.post(url, data, proxies=proxies, timeout=30).content
    else:
        scraper = cfscrape.create_scraper(delay=10)
        return scraper.post(url, data, timeout=30).content
