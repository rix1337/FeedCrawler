# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt die Web-Suche für alle integrierten Hostnamen bereit.

import json
import re

from bs4 import BeautifulSoup

from feedcrawler.external_sites.feed_search.sites.content_all_fx import fx_content_to_soup
from feedcrawler.external_sites.web_search.sites.content_all_by import by_search_results
from feedcrawler.external_sites.web_search.sites.content_all_dw import dw_search_results
from feedcrawler.external_sites.web_search.sites.content_all_fx import fx_search_results
from feedcrawler.external_sites.web_search.sites.content_all_hw import hw_search_results
from feedcrawler.external_sites.web_search.sites.content_all_nk import nk_search_results
from feedcrawler.external_sites.web_search.sites.content_all_nx import nx_search_results
from feedcrawler.providers.common_functions import check_is_ignored
from feedcrawler.providers.common_functions import check_is_site
from feedcrawler.providers.common_functions import encode_base64
from feedcrawler.providers.common_functions import is_show
from feedcrawler.providers.common_functions import keep_alphanumeric_with_special_characters
from feedcrawler.providers.common_functions import simplified_search_term_in_title
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.url_functions import get_url
from feedcrawler.providers.url_functions import get_urls_async
from feedcrawler.providers.url_functions import post_url


def search_web(title, only_content_movies=False, only_content_shows=False):
    hostnames = CrawlerConfig('Hostnames')
    by = hostnames.get('by')
    dw = hostnames.get('dw')
    fx = hostnames.get('fx')
    hw = hostnames.get('hw')
    nk = hostnames.get('nk')
    nx = hostnames.get('nx')
    sj = hostnames.get('sj')
    sf = hostnames.get('sf')

    force_ignore_in_web_search = CrawlerConfig('FeedCrawler').get('force_ignore_in_web_search')

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
        mb_query = keep_alphanumeric_with_special_characters(title).replace(" ", "+")
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
        if dw:
            dw_search = 'https://' + dw + '/?s=' + bl_query + '&orderby=date&order=desc'
        else:
            dw_search = None
        if fx:
            fx_search = 'https://' + fx + '/?s=' + bl_query
        else:
            fx_search = None
        if hw:
            hw_search = 'https://' + hw + '/?s=' + bl_query
        else:
            hw_search = None
        if nx:
            nx_search = 'https://' + nx + '/api/frontend/search/' + bl_query
        else:
            nx_search = None

        async_results = get_urls_async([by_search, dw_search, fx_search, hw_search, nx_search])

        by_results = []
        dw_results = []
        fx_results = []
        hw_results = []
        nx_results = []

        for res in async_results:
            if check_is_site(res[1]) == 'BY':
                by_results = by_search_results(res[0], by, quality, title)
            elif check_is_site(res[1]) == 'DW':
                dw_results = dw_search_results(res[0], quality, title)
            elif check_is_site(res[1]) == 'FX':
                fx_results = fx_search_results(fx_content_to_soup(res[0]), bl_query)
            elif check_is_site(res[1]) == 'HW':
                hw_results = hw_search_results(res[0], quality, title)
            elif check_is_site(res[1]) == 'NX':
                nx_results = nx_search_results(res[0], quality, title)

        if nk:
            nk_search = post_url('https://' + nk + "/search",
                                 data={'search': bl_query.replace("+", " ")})
            nk_results = nk_search_results(nk_search, 'https://' + nk + '/', quality, title)
        else:
            nk_results = []

        password = ""
        for result in by_results:
            if only_content_movies and is_show(result[0]):
                continue
            unrated.append(
                [rate(result[0], ignore), encode_base64(result[1] + "|" + password), result[0] + " (BY)"])

        password = fx.split('.')[0]
        for result in fx_results:
            if only_content_movies and is_show(result[0]):
                continue
            # title is intentionally sent with the password, so we can detect the correct link when downloading
            unrated.append([rate(result[0], ignore), encode_base64(result[1] + "|" + password + "|" + result[0]),
                            result[0] + " (FX)"])

        password = dw.split('.')[0]
        for result in dw_results:
            if only_content_movies and is_show(result[0]):
                continue
            unrated.append(
                [rate(result[0], ignore), encode_base64(result[1] + "|" + password), result[0] + " (DW)"])

        password = hw.split('.')[0]
        for result in hw_results:
            if only_content_movies and is_show(result[0]):
                continue
            unrated.append(
                [rate(result[0], ignore), encode_base64(result[1] + "|" + password), result[0] + " (HW)"])

        password = nk.split('.')[0].capitalize()
        for result in nk_results:
            if only_content_movies and is_show(result[0]):
                continue
            unrated.append(
                [rate(result[0], ignore), encode_base64(result[1] + "|" + password), result[0] + " (NK)"])

        password = nx.split('.')[0]
        for result in nx_results:
            if only_content_movies and is_show(result[0]):
                continue
            unrated.append(
                [rate(result[0], ignore), encode_base64(result[1] + "|" + password), result[0] + " (NX)"])

        rated = sorted(unrated, reverse=True)

        results = []
        i = 0

        for result in rated:
            if force_ignore_in_web_search and check_is_ignored(result[2], ignore):
                continue
            res = {"payload": result[1], "title": result[2]}
            results.append(res)
            i += 1
        content_all_results = results

    content_shows_sj_results = []
    content_shows_sf_results = []
    if not only_content_movies:
        if sj:
            sj_query = keep_alphanumeric_with_special_characters(title).replace(" ", "+")
            sj_search = get_url('https://' + sj + '/serie/search?q=' + sj_query)
            try:
                sj_results = BeautifulSoup(sj_search, "html.parser").findAll("a", href=re.compile("/serie"))
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

        if sf:
            sf_query = keep_alphanumeric_with_special_characters(title)
            sf_search = get_url('https://' + sf + '/api/v2/search?q=' + sf_query + '&ql=DE')
            try:
                try:
                    sf_results = json.loads(sf_search)["result"]
                except:
                    clean_sf_search = BeautifulSoup(sf_search, "html.parser").body.text
                    sf_results = json.loads(clean_sf_search)["result"]
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
        match = check_is_ignored(title, ignore)
        if match:
            score -= 5
    if ".subpack." in title.lower():
        score -= 10
    return score
