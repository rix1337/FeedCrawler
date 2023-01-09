# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt content_all alle benötigten Parameter für die Web-Suche auf HW bereit.

import re

from bs4 import BeautifulSoup

from feedcrawler.external_sites.feed_search.shared import check_release_not_sd
from feedcrawler.providers.common_functions import simplified_search_term_in_title


def hw_search_results(content, resolution, search_term):
    content = BeautifulSoup(content, "html.parser")
    links = content.findAll("a", href=re.compile(r"^(?!.*\/category).*\/(filme|serien).*(?!.*#comments.*)$"))
    results = []
    for link in links:
        try:
            title = link.text.replace(" ", ".").strip()
            if ".xxx." not in title.lower() and simplified_search_term_in_title(search_term, title):
                link = link["href"]
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
