# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt content_all alle benötigten Parameter für die Web-Suche auf HW bereit.

from bs4 import BeautifulSoup

from feedcrawler.external_sites.feed_search.shared import check_release_not_sd


def dw_search_results(content, resolution):
    content = BeautifulSoup(content, 'html5lib')
    links = content.findAll("article")
    results = []
    for link in links:
        try:
            link = link.findAll("a")[1]
            title = link["title"].replace(" ", ".").strip()
            if ".xxx." not in title.lower():
                link = link["href"]
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
