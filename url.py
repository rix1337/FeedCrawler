# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import cfscrape

from rssconfig import RssConfig

def getURL(url):
    proxy = RssConfig('RSScrawler').get('proxy')
    if proxy:
        proxies = []
        if proxy.startswith('http://'):
            proxies[0] = proxy[:4]
            proxies[1] = proxy
        elif proxy.startswith('https://'):
            proxies[0] = proxy[:5]
            proxies[1] = proxy
        elif proxy.startswith('socks5://'):
            proxies[0] = 'http'
            proxies[1] = proxy
        proxies = {proxies[0]: proxies[1]}
        scraper = cfscrape.create_scraper(delay=10, proxies=proxies)
    else:
        scraper = cfscrape.create_scraper(delay=10)
    return scraper.get(url).content

def postURL(url, data):
    proxy = RssConfig('RSScrawler').get('proxy')
    if proxy:
        proxies = []
        if proxy.startswith('http://'):
            proxies[0] = proxy[:4]
            proxies[1] = proxy
        elif proxy.startswith('https://'):
            proxies[0] = proxy[:5]
            proxies[1] = proxy
        elif proxy.startswith('socks5://'):
            proxies[0] = 'http'
            proxies[1] = proxy
        proxies = {proxies[0]: proxies[1]}
        scraper = cfscrape.create_scraper(delay=10, proxies=proxies)
    else:
        scraper = cfscrape.create_scraper(delay=10)
    return scraper.post(url, data).content
