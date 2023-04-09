# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt content_all alle benötigten Parameter für die Web-Suche auf NX bereit.

import json

from feedcrawler.external_sites.feed_search.shared import check_release_not_sd
from feedcrawler.providers.common_functions import simplified_search_term_in_title
from feedcrawler.providers.config import CrawlerConfig


def nx_search_results(content, resolution, search_term):
    feed = json.loads(content)
    nx = CrawlerConfig('Hostnames').get('nx')
    items = feed['result']['releases']
    valid_types = ['movie', 'episode']

    results = []
    for item in items:
        try:
            if any(s in item['type'] for s in valid_types):
                title = item['name'].replace(" ", ".").strip()
                if ".xxx." not in title.lower() and simplified_search_term_in_title(search_term, title):
                    link = "https://" + nx + "/api/frontend/releases/" + item['slug']
                    if "#comments-title" not in link:
                        if resolution and resolution.lower() not in title.lower():
                            if "480p" in resolution:
                                if check_release_not_sd(title):
                                    continue
                            else:
                                continue
                        results.append([title, link])

        except:
            print("NX hat die Suche angepasst. Parsen teilweise nicht möglich!")
            continue

    return results
