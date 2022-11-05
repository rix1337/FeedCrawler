# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt content_all alle benötigten Parameter für die Web-Suche auf NK bereit.

import re

from bs4 import BeautifulSoup

from feedcrawler.external_sites.feed_search.shared import check_release_not_sd
from feedcrawler.providers.common_functions import simplified_search_term_in_title


def nk_search_results(content, base_url, resolution, search_term):
    content = BeautifulSoup(content, 'html5lib')
    links = content.findAll("a", {"class": "btn"}, href=re.compile("/release/"))
    results = []
    for link in links:
        try:
            title = link.parent.parent.parent.find("span", {"class": "subtitle"}).text.replace(" ", ".")
            if ".xxx." not in title.lower() and simplified_search_term_in_title(search_term, title):
                link = base_url + link["href"]
                if "#comments-title" not in link:
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
