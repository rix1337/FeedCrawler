# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt content_all alle benötigten Parameter für die Web-Suche auf NX bereit.

import json

from feedcrawler.providers.common_functions import simplified_search_term_in_title
from feedcrawler.providers.config import CrawlerConfig


def nx_search_results(content, quality, search_term):
    feed = json.loads(content)
    nx = CrawlerConfig('Hostnames').get('nx')
    items = feed['result']['releases']
    valid_types = ['movie', 'episode']

    results = []
    for item in items:
        try:
            if any(s in item['type'] for s in valid_types):
                link = "https://" + nx + "/api/frontend/releases/" + item['slug']
                title = item['name']

                if simplified_search_term_in_title(search_term, title):
                    results.append([title, link])

        except:
            print(u"NX hat die Suche angepasst. Parsen teilweise nicht möglich!")
            continue

    return results
