# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt die Web-Suche für alle integrierten Hostnamen bereit.

import json
import re

from bs4 import BeautifulSoup

from feedcrawler.common import check_is_site
from feedcrawler.common import encode_base64
from feedcrawler.common import sanitize
from feedcrawler.common import simplified_search_term_in_title
from feedcrawler.config import CrawlerConfig
from feedcrawler.external_sites.shared.internal_feed import check_release_not_sd
from feedcrawler.external_sites.shared.internal_feed import fx_content_to_soup
from feedcrawler.url import get_url
from feedcrawler.url import get_urls_async
from feedcrawler.url import post_url


def get(title, only_content_all=False, only_content_shows=False, only_fast=False, only_slow=False):
    if only_fast:
        only_slow = False
    if only_slow:
        only_fast = False

    hostnames = CrawlerConfig('Hostnames')
    by = hostnames.get('by')
    fx = hostnames.get('fx')
    hw = hostnames.get('hw')
    nk = hostnames.get('nk')
    sj = hostnames.get('sj')
    sf = hostnames.get('sf')

    specific_season = re.match(r'^(.*),(s\d{1,3})$', title.lower())
    specific_episode = re.match(r'^(.*),(s\d{1,3}e\d{1,3})$', title.lower())
    if specific_season:
        split = title.split(",")
        title = split[0]
        special = split[1].upper()
    elif specific_episode:
        split = title.split(",")
        title = split[0]
        special = split[1].upper()
    else:
        special = None

    content_all_results = []
    if not only_content_shows:
        mb_query = sanitize(title).replace(" ", "+")
        if special:
            bl_query = mb_query + "+" + special
        else:
            bl_query = mb_query

        unrated = []

        config = CrawlerConfig('ContentAll')
        quality = config.get('quality')
        ignore = config.get('ignore')

        if by:
            by_search = 'https://' + by + '/?q=' + bl_query
        else:
            by_search = None
        if fx:
            fx_search = 'https://' + fx + '/?s=' + bl_query
        else:
            fx_search = None
        if hw:
            hw_search = 'https://' + hw + '/?s=' + bl_query
        else:
            hw_search = None

        if only_fast:
            fx_search = None
        if only_slow:
            by_search = None
            hw_search = None

        async_results = get_urls_async([by_search, fx_search, hw_search])

        by_results = []
        fx_results = []
        hw_results = []

        for res in async_results:
            if check_is_site(res[1]) == 'BY':
                by_results = by_search_results(res[0], by, quality)
            elif check_is_site(res[1]) == 'FX':
                fx_results = fx_search_results(fx_content_to_soup(res[0]), bl_query)
            elif check_is_site(res[1]) == 'HW':
                hw_results = hw_search_results(res[0], quality)

        if nk and not only_slow:
            nk_search = post_url('https://' + nk + "/search",
                                 data={'search': bl_query.replace("+", " ")})
            nk_results = nk_search_results(nk_search, 'https://' + nk + '/', quality)
        else:
            nk_results = []

        password = ""
        for result in by_results:
            if "480p" in quality and check_release_not_sd(result[0]):
                continue
            unrated.append(
                [rate(result[0], ignore), encode_base64(result[1] + "|" + password), result[0] + " (BY)"])

        password = fx.split('.')[0]
        for result in fx_results:
            if "480p" in quality and check_release_not_sd(result[0]):
                continue
            # title is intentionally sent with the password, so we can detect the correct link when downloading
            unrated.append([rate(result[0], ignore), encode_base64(result[1] + "|" + password + "|" + result[0]),
                            result[0] + " (FX)"])

        password = hw.split('.')[0]
        for result in hw_results:
            if "480p" in quality and check_release_not_sd(result[0]):
                continue
            unrated.append(
                [rate(result[0], ignore), encode_base64(result[1] + "|" + password), result[0] + " (HW)"])

        password = nk.split('.')[0].capitalize()
        for result in nk_results:
            if "480p" in quality and check_release_not_sd(result[0]):
                continue
            unrated.append(
                [rate(result[0], ignore), encode_base64(result[1] + "|" + password), result[0] + " (NK)"])

        rated = sorted(unrated, reverse=True)

        results = []
        i = 0

        for result in rated:
            res = {"payload": result[1], "title": result[2]}
            results.append(res)
            i += 1
        content_all_results = results

    content_shows_sj_results = []
    content_shows_sf_results = []
    if not only_content_all:
        if sj and not only_slow:
            sj_query = sanitize(title).replace(" ", "+")
            sj_search = get_url('https://' + sj + '/serie/search?q=' + sj_query)
            try:
                sj_results = BeautifulSoup(sj_search, 'html5lib').findAll("a", href=re.compile("/serie"))
            except:
                sj_results = []
        else:
            sj_results = []

        if special:
            append = " (" + special + ")"
        else:
            append = ""
        i = 0
        results = []
        for result in sj_results:
            r_title = result.text
            if simplified_search_term_in_title(title, r_title):
                res = {"payload": encode_base64(result['href'] + "|" + r_title + "|" + str(special)),
                       "title": r_title + append}
                results.append(res)
                i += 1
        content_shows_sj_results = results

        if sf and not only_slow:
            sf_query = sanitize(title)
            sf_search = get_url('https://' + sf + '/api/v2/search?q=' + sf_query + '&ql=DE')
            try:
                sf_results = json.loads(sf_search)["result"]
            except:
                sf_results = []
        else:
            sf_results = []

        if special:
            append = " (" + special + ")"
        else:
            append = ""
        i = 0
        results = []
        for result in sf_results:
            r_title = result["title"]
            if simplified_search_term_in_title(title, r_title):
                r_url = "https://" + sf + "/" + result["url_id"]
                res = {"payload": encode_base64(r_url + "|" + r_title + "|" + str(special)),
                       "title": r_title + append}
                results.append(res)
                i += 1
        content_shows_sf_results = results

    return content_all_results, content_shows_sj_results, content_shows_sf_results


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
        article = BeautifulSoup(str(link), 'html5lib')
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


def hw_search_results(content, resolution):
    content = BeautifulSoup(content, 'html5lib')
    links = content.findAll("a", href=re.compile(r"^(?!.*\/category).*\/(filme|serien).*(?!.*#comments.*)$"))
    results = []
    for link in links:
        try:
            title = link.text.replace(" ", ".").strip()
            if ".xxx." not in title.lower():
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


def nk_search_results(content, base_url, resolution):
    content = BeautifulSoup(content, 'html5lib')
    links = content.findAll("a", {"class": "btn"}, href=re.compile("/release/"))
    results = []
    for link in links:
        try:
            title = link.parent.parent.parent.find("span", {"class": "subtitle"}).text.replace(" ", ".")
            if ".xxx." not in title.lower():
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


def rate(title, ignore=False):
    score = 0
    if ".bluray." in title.lower():
        score += 7
    if ".bd." in title.lower():
        score += 7
    if ".bdrip." in title.lower():
        score += 7
    if re.match(r'.*\-(4SJ|TVS)', title):
        score += 4
    if ".dl." in title.lower():
        score += 2
    if re.match(r'.*\.(DTS|DD\+*51|DD\+*71|AC3\.5\.*1)\..*', title):
        score += 2
    if re.match(r'.*\.(720|1080|2160)p\..*', title):
        score += 2
    if ".ml." in title.lower():
        score += 1
    if ".dd20." in title.lower():
        score += 1
    if "dubbed." in title.lower():
        score -= 1
    if ".synced." in title.lower():
        score -= 1
    if ".ac3d." in title.lower():
        score -= 1
    if ".dtsd." in title.lower():
        score -= 1
    if ".hdtv." in title.lower():
        score -= 1
    if ".dtv" in title.lower():
        score -= 1
    if ".pdtv" in title.lower():
        score -= 1
    if "tvrip." in title.lower():
        score -= 1
    if ".subbed." in title.lower():
        score -= 2
    if ".xvid." in title.lower():
        score -= 2
    if ".pal." in title.lower():
        score -= 10
    if "dvd9" in title.lower():
        score -= 10
    if ignore:
        try:
            ignore = ignore.replace(",", "|").lower() if len(ignore) > 0 else r"^unmatchable$"
        except TypeError:
            ignore = r"^unmatchable$"
        r = re.search(ignore, title.lower())
        if r:
            score -= 5
    if ".subpack." in title.lower():
        score -= 10
    return score
