# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import cfscrape
from fake_useragent import FakeUserAgentError
from fake_useragent import UserAgent

from rsscrawler.common import decode_base64
from rsscrawler.rssconfig import RssConfig
from rsscrawler.rssdb import RssDb


def fake_user_agent():
    fallback = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:63.0) Gecko/20100101 Firefox/63.0"
    try:
        ua = UserAgent(fallback=fallback).random
    except FakeUserAgentError:
        ua = False
        pass
    if not ua:
        ua = fallback
        return ua


def check_url(configfile, dbfile):
    sj_url = decode_base64("aHR0cDovL3Nlcmllbmp1bmtpZXMub3Jn")
    mb_url = decode_base64("aHR0cDovL21vdmllLWJsb2cudG8v")
    proxy = RssConfig('RSScrawler', configfile).get('proxy')
    scraper = cfscrape.create_scraper(delay=10)
    agent = fake_user_agent()
    sj_blocked_proxy = False
    mb_blocked_proxy = False
    if proxy:
        db = RssDb(dbfile, 'proxystatus')
        proxies = {'http': proxy, 'https': proxy}
        if "block." in str(
                scraper.get(sj_url, headers={'User-Agent': agent}, proxies=proxies, timeout=30,
                            allow_redirects=False).headers.get("location")):
            print(u"Der Zugriff auf SJ ist mit der aktuellen Proxy-IP nicht möglich!")
            if RssConfig('RSScrawler', configfile).get("fallback"):
                db.store("SJ", "Blocked")
            sj_blocked_proxy = True
        else:
            db.delete("SJ")
        if "<Response [403]>" in str(
                scraper.get(mb_url, headers={'User-Agent': agent}, proxies=proxies, timeout=30, allow_redirects=False)):
            print(u"Der Zugriff auf MB ist mit der aktuellen Proxy-IP nicht möglich!")
            if RssConfig('RSScrawler', configfile).get("fallback"):
                db.store("MB", "Blocked")
                mb_blocked_proxy = True
        else:
            db.delete("MB")
    if not proxy or sj_blocked_proxy == True or mb_blocked_proxy == True:
        if "block." in str(
                scraper.get(sj_url, headers={'User-Agent': agent}, timeout=30, allow_redirects=False).headers.get(
                    "location")):
            print(u"Der Zugriff auf SJ ist mit der aktuellen IP nicht möglich!")
        if "<Response [403]>" in str(
                scraper.get(mb_url, headers={'User-Agent': agent}, timeout=30, allow_redirects=False)):
            print(u"Der Zugriff auf MB ist mit der aktuellen IP nicht möglich!")
    return


def get_url(url, configfile, dbfile):
    config = RssConfig('RSScrawler', configfile)
    proxy = config.get('proxy')
    scraper = cfscrape.create_scraper(delay=10)
    agent = fake_user_agent()
    if proxy:
        sj = decode_base64("c2VyaWVuanVua2llcy5vcmc=")
        mb = decode_base64("bW92aWUtYmxvZy50bw==")
        db = RssDb(dbfile, 'proxystatus')
        if sj in url:
            if db.retrieve("SJ") and config.get("fallback"):
                return scraper.get(url, headers={'User-Agent': agent}, timeout=30).text
        elif mb in url:
            if db.retrieve("MB") and config.get("fallback"):
                return scraper.get(url, headers={'User-Agent': agent}, timeout=30).text
        proxies = {'http': proxy, 'https': proxy}
        return scraper.get(url, headers={'User-Agent': agent}, proxies=proxies, timeout=30).text
    else:
        return scraper.get(url, headers={'User-Agent': agent}, timeout=30).text


def get_url_headers(url, configfile, dbfile, headers):
    config = RssConfig('RSScrawler', configfile)
    proxy = config.get('proxy')
    scraper = cfscrape.create_scraper(delay=10)
    agent = fake_user_agent()
    headers.update({'User-Agent': agent})
    if proxy:
        sj = decode_base64("c2VyaWVuanVua2llcy5vcmc=")
        mb = decode_base64("bW92aWUtYmxvZy50bw==")
        db = RssDb(dbfile, 'proxystatus')
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


def post_url(url, configfile, dbfile, data):
    config = RssConfig('RSScrawler', configfile)
    proxy = config.get('proxy')
    scraper = cfscrape.create_scraper(delay=10)
    agent = fake_user_agent()
    if proxy:
        sj = decode_base64("c2VyaWVuanVua2llcy5vcmc=")
        mb = decode_base64("bW92aWUtYmxvZy50bw==")
        db = RssDb(dbfile, 'proxystatus')
        if sj in url:
            if db.retrieve("SJ") and config.get("fallback"):
                return scraper.post(url, data, headers={'User-Agent': agent}, timeout=30).content
        elif mb in url:
            if db.retrieve("MB") and config.get("fallback"):
                return scraper.post(url, data, headers={'User-Agent': agent}, timeout=30).content
        proxies = {'http': proxy, 'https': proxy}
        return scraper.post(url, data, headers={'User-Agent': agent}, proxies=proxies, timeout=30).content
    else:
        return scraper.post(url, data, headers={'User-Agent': agent}, timeout=30).content


def post_url_json(url, configfile, dbfile, json):
    config = RssConfig('RSScrawler', configfile)
    proxy = config.get('proxy')
    scraper = cfscrape.create_scraper(delay=10)
    agent = fake_user_agent()
    if proxy:
        sj = decode_base64("c2VyaWVuanVua2llcy5vcmc=")
        mb = decode_base64("bW92aWUtYmxvZy50bw==")
        db = RssDb(dbfile, 'proxystatus')
        if sj in url:
            if db.retrieve("SJ") and config.get("fallback"):
                return scraper.post(url, json=json, headers={'User-Agent': agent}, timeout=30).content
        elif mb in url:
            if db.retrieve("MB") and config.get("fallback"):
                return scraper.post(url, json=json, headers={'User-Agent': agent}, timeout=30).content
        proxies = {'http': proxy, 'https': proxy}
        return scraper.post(url, json=json, headers={'User-Agent': agent}, proxies=proxies, timeout=30).content
    else:
        return scraper.post(url, json=json, headers={'User-Agent': agent}, timeout=30).content
