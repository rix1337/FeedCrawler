# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt content_all alle benötigten Parameter für die Web-Suche auf BY bereit.

import re

from bs4 import BeautifulSoup

from feedcrawler.external_sites.feed_search.shared import check_release_not_sd


def by_search_results(content, base_url, resolution):
    content = BeautifulSoup(content, 'html5lib')
    links = content.findAll("a", href=re.compile("/category/"))
    results = []
    for link in links:
        try:
            title = link.text.replace(" ", ".").strip()
            if ".xxx." not in title.lower():
                link = "https://" + base_url + link['href']
                if resolution and resolution.lower() not in title.lower():
                    if "480p" in resolution:
                        if check_release_not_sd(title):
                            continue
                    else:
                        continue
                results.append([title, link])
        except:
            pass

    return results