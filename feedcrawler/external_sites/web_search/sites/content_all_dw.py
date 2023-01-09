# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt content_all alle benötigten Parameter für die Web-Suche auf HW bereit.

from bs4 import BeautifulSoup

from feedcrawler.external_sites.feed_search.shared import check_release_not_sd
from feedcrawler.providers.common_functions import simplified_search_term_in_title


def dw_search_results(content, resolution, search_term):
    content = BeautifulSoup(content, "html.parser")
    links = content.findAll("article")
    results = []
    for link in links:
        try:
            link = link.findAll("a")[1]
            title = link["title"].replace(" ", ".").strip()
            if ".xxx." not in title.lower() and simplified_search_term_in_title(search_term, title):
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
