# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

# import rsscrawler modules
from rssconfig import RssConfig

# import third party modules
import cfscrape


def getURL(url):
    proxy = RssConfig('RSScrawler').get('proxy')
    if proxy:
        proxies = {'http': proxy, 'https': proxy}
        scraper = cfscrape.create_scraper(delay=10)
        return scraper.get(url, proxies=proxies).content
    else:
        scraper = cfscrape.create_scraper(delay=10)
        return scraper.get(url).content


def postURL(url, data):
    proxy = RssConfig('RSScrawler').get('proxy')
    if proxy:
        proxies = {'http': proxy, 'https': proxy}
        scraper = cfscrape.create_scraper(delay=10)
        return scraper.post(url, data, proxies=proxies).content
    else:
        scraper = cfscrape.create_scraper(delay=10)
        return scraper.post(url, data).content
