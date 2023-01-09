# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt content_all alle benötigten Parameter für die Web-Suche auf FX bereit.

import re

from bs4 import BeautifulSoup

from feedcrawler.providers.common_functions import simplified_search_term_in_title
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.url_functions import get_urls_async


def fx_search_results(content, search_term):
    fx = CrawlerConfig('Hostnames').get('fx')
    articles = content.find("main").find_all("article")

    async_link_results = []
    for article in articles:
        if simplified_search_term_in_title(search_term, article.find("h2").text):
            link = article.find("a")["href"]
            if link:
                async_link_results.append(link)

    links = get_urls_async(async_link_results)

    results = []

    for link in links:
        article = BeautifulSoup(str(link), "html.parser")
        titles = article.find_all("a", href=re.compile("(filecrypt|safe." + fx + ")"))
        for title in titles:
            try:
                link = article.find("link", rel="canonical")["href"]
                title = title.text.encode("ascii", errors="ignore").decode().replace("/", "").replace(" ", ".")
                if title and "-fun" in title.lower():
                    if "download" in title.lower():
                        try:
                            title = str(content.find("strong", text=re.compile(r".*Release.*")).nextSibling)
                        except:
                            continue
                    results.append([title, link])
            except:
                pass
    return results
