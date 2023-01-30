# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul durchsucht die Web-Suchen vieler Seiten des Typs content_all auf Basis einer standardisierten Struktur.

import json
import re

from bs4 import BeautifulSoup

import feedcrawler.external_sites.feed_search.sites.content_all_by as content_all_by_feed_search
import feedcrawler.external_sites.feed_search.sites.content_all_dw as content_all_dw_feed_search
import feedcrawler.external_sites.feed_search.sites.content_all_fx as content_all_fx_feed_search
import feedcrawler.external_sites.feed_search.sites.content_all_hw as content_all_hw_feed_search
import feedcrawler.external_sites.feed_search.sites.content_all_nk as content_all_nk_feed_search
from feedcrawler.external_sites.feed_search.shared import add_decrypt_instead_of_download
from feedcrawler.external_sites.feed_search.shared import check_release_not_sd
from feedcrawler.external_sites.feed_search.shared import standardize_size_value
from feedcrawler.external_sites.feed_search.shared import unused_get_feed_parameter
from feedcrawler.external_sites.metadata.imdb import get_imdb_id_from_content
from feedcrawler.external_sites.metadata.imdb import get_imdb_id_from_link
from feedcrawler.external_sites.web_search.shared import search_web, rate
from feedcrawler.providers import shared_state
from feedcrawler.providers.common_functions import check_hoster
from feedcrawler.providers.common_functions import check_is_site
from feedcrawler.providers.common_functions import decode_base64
from feedcrawler.providers.common_functions import is_retail
from feedcrawler.providers.common_functions import keep_alphanumeric_with_special_characters
from feedcrawler.providers.common_functions import simplified_search_term_in_title
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.notifications import notify
from feedcrawler.providers.sqlite_database import ListDb, FeedDb
from feedcrawler.providers.url_functions import get_redirected_url, get_url, get_urls_async, post_url


def get_best_result(title):
    title = keep_alphanumeric_with_special_characters(title)
    try:
        bl_results = search_web(title, only_content_all=True)[0]
    except:
        return False

    best_score = -999
    best_match = False
    best_payload = False
    for result in bl_results:
        payload = result['payload']
        result = result['title']
        if simplified_search_term_in_title(title, result):
            score = rate(result)
            if score > best_score:
                best_score = score
                best_match = result
                best_payload = payload

    if not best_match or not best_payload:
        shared_state.logger.debug(u'Kein Treffer für die Suche nach ' + title + '! Suchliste ergänzt.')
        liste = "List_ContentAll_Movies"
        cont = ListDb(liste).retrieve()
        if not cont:
            cont = ""
        if title not in cont:
            ListDb(liste).store(title)
        return False
    if not is_retail(best_match, True):
        shared_state.logger.debug(u'Kein Retail-Release für die Suche nach ' + title + ' gefunden! Suchliste ergänzt.')
        liste = "List_ContentAll_Movies"
        cont = ListDb(liste).retrieve()
        if not cont:
            cont = ""
        if title not in cont:
            ListDb(liste).store(title)
        return best_payload
    else:
        shared_state.logger.debug('Bester Treffer für die Suche nach ' + title + ' ist ' + best_match)
        return best_payload


def download(payload):
    config = CrawlerConfig('ContentAll')
    db = FeedDb('FeedCrawler')
    hostnames = CrawlerConfig('Hostnames')
    by = hostnames.get('by')
    nk = hostnames.get('nk')
    nx = hostnames.get('nx')

    payload = decode_base64(payload).split("|")
    source = payload[0]
    password = payload[1]

    site = check_is_site(source)
    if not site:
        return False
    else:
        response = get_url(source)
        if not response or "NinjaFirewall 429" in response:
            return False

        if not "NX" in site:
            soup = BeautifulSoup(response, "html.parser")
        else:
            soup = json.loads(response)

        url_hosters = []
        if "BY" in site:
            key = soup.find("small").text
            details = soup.findAll("td", {"valign": "TOP", "align": "CENTER"})[1]
            imdb_link = ""
            try:
                imdb = details.find("a", href=re.compile("imdb.com"))
                imdb_link = imdb["href"].replace("https://anonym.to/?", "")
            except:
                pass

            try:
                imdb_id = get_imdb_id_from_link(key, imdb_link)
            except:
                imdb_id = ""

            try:
                size = standardize_size_value(
                    details.findAll("td", {"align": "LEFT"})[-1].text.split(" ", 1)[1].strip())
            except:
                size = ""

            links = soup.find_all("iframe")
            async_link_results = []
            for link in links:
                link = link["src"]
                if 'https://' + by in link:
                    async_link_results.append(link)

            links = get_urls_async(async_link_results)
            for link in links:
                if link[0]:
                    link = BeautifulSoup(link[0], "html.parser").find("a", href=re.compile("/go\.php\?"))
                    if link:
                        url_hosters.append([link["href"], link.text.replace(" ", "")])
        elif "DW" in site:
            key = soup.find("h1").text.strip()

            try:
                imdb_link = soup.find("a", href=re.compile("imdb.com"))
                imdb_id = get_imdb_id_from_link(key, imdb_link["href"])
            except:
                imdb_id = ""

            try:
                size = standardize_size_value(soup.find("strong", text=re.compile(r"(size|größe)",
                                                                                  re.IGNORECASE)).nextSibling.nextSibling.text.split(
                    "|")[-1].strip())
            except:
                size = ""

            password = payload[1]
        elif "FX" in site:
            key = payload[2]
        elif "HW" in site:
            key = soup.find("h2", {"class": "entry-title"}).text.strip()

            try:
                imdb_id = get_imdb_id_from_content(key, str(soup))
            except:
                imdb_id = ""

            try:
                size = standardize_size_value(soup.find("strong",
                                                        text=re.compile(
                                                            r"(size|größe)", re.IGNORECASE)).next.next.text.replace("|",
                                                                                                                    "").strip())
            except:
                size = ""

            download_links = soup.findAll("a", href=re.compile('filecrypt'))
            links_string = ""
            for link in download_links:
                links_string += str(link)
            url_hosters = re.findall(r'href="([^"\'>]*)".+?(.+?)<', links_string)
            password = payload[1]
        elif "NK" in site:
            key = soup.find("span", {"class": "subtitle"}).text
            details = soup.find("div", {"class": "article"})
            try:
                imdb_link = details.find("a", href=re.compile("imdb.com"))
                imdb_id = get_imdb_id_from_link(key, imdb_link["href"])
            except:
                imdb_id = ""

            try:
                size = standardize_size_value(
                    details.find("span", text=re.compile(r"(size|größe)", re.IGNORECASE)).next.next.strip())
            except:
                size = ""

            hosters = soup.find_all("a", href=re.compile("/go/"))
            for hoster in hosters:
                url_hosters.append(['https://' + nk + hoster["href"], hoster.text])
        elif "NX" in site:
            item = soup["result"]
            try:
                source = "https://" + nx + "/release/" + item['slug']
            except:
                source = ""

            key = item['name']

            try:
                imdb_id = item['_media']['imdbid']
            except:
                imdb_id = ""

            try:
                size = standardize_size_value(item['size'] + item['sizeunit'])
            except:
                size = ""
        else:
            return False

        links = {}
        if "FX" in site:
            class FX:
                unused = ""

            details = content_all_fx_feed_search.fx_get_details(response, key)
            size = standardize_size_value(details["size"])
            imdb_id = details["imdb_id"]
            download_links = content_all_fx_feed_search.fx_get_download_links(FX, response, key)
        elif "DW" in site:
            class DW:
                url = source
                hoster_fallback = config.get("hoster_fallback")

            download_links = content_all_dw_feed_search.dw_get_download_links(DW, str(soup), key)
        elif "NX" in site:
            download_links = [source]
        else:
            for url_hoster in reversed(url_hosters):
                try:
                    link_hoster = url_hoster[1].lower().replace('target="_blank">', '').replace(" ", "-").replace(
                        "ddownload", "ddl")
                    if check_hoster(link_hoster):
                        link = url_hoster[0]
                        if by in link:
                            demasked_link = get_redirected_url(link)
                            if demasked_link:
                                link = demasked_link
                        links[link_hoster] = link
                except:
                    pass
            if config.get("hoster_fallback") and not links:
                for url_hoster in reversed(url_hosters):
                    link_hoster = url_hoster[1].lower().replace('target="_blank">', '').replace(" ", "-").replace(
                        "ddownload", "ddl")
                    link = url_hoster[0]
                    if by in link:
                        demasked_link = get_redirected_url(link)
                        if demasked_link:
                            link = demasked_link
                    links[link_hoster] = link
            download_links = list(links.values())

    englisch = False
    if "*englisch" in key.lower() or "*english" in key.lower():
        key = key.replace(
            '*ENGLISCH', '').replace("*Englisch", "").replace("*ENGLISH", "").replace("*English",
                                                                                      "").replace(
            "*", "")
        englisch = True

    staffel = re.search(r"s\d{1,2}(-s\d{1,2}|-\d{1,2}|\.)", key.lower())

    if download_links:
        if staffel:
            if add_decrypt_instead_of_download(key, "FeedCrawler", download_links, password):
                db.store(
                    key.replace(".COMPLETE", "").replace(".Complete", ""),
                    'notdl' if config.get(
                        'enforcedl') and '.dl.' not in key.lower() else 'added'
                )
                log_entry = '[Suche/Staffel] - ' + key.replace(".COMPLETE", "").replace(".Complete",
                                                                                        "") + ' - [' + site + '] - ' + size + ' - ' + source
                shared_state.logger.info(log_entry)
                notify([{"text": log_entry, "imdb_id": imdb_id}])
                return [key]
        else:
            retail = False
            if config.get('cutoff') and '.COMPLETE.' not in key.lower():
                if is_retail(key, True):
                    retail = True
            if add_decrypt_instead_of_download(key, "FeedCrawler", download_links, password):
                db.store(
                    key,
                    'notdl' if config.get(
                        'enforcedl') and '.dl.' not in key.lower() else 'added'
                )
                log_entry = '[Suche/Film' + ('/Englisch' if englisch and not retail else '') + (
                    '/Englisch/Retail' if englisch and retail else '') + (
                                '/Retail' if not englisch and retail else '') + '] - ' + key + ' - [' + site + '] - ' + size + ' - ' + source
                shared_state.logger.info(log_entry)
                notify([{"text": log_entry, "imdb_id": imdb_id}])
                return [key]
    else:
        return False


def get_search_results_for_feed_search(self, bl_query):
    unused_get_feed_parameter(self)
    hostnames = CrawlerConfig('Hostnames')
    by = hostnames.get('by')
    dw = hostnames.get('dw')
    fx = hostnames.get('fx')
    hw = hostnames.get('hw')
    nk = hostnames.get('nk')

    search_results = []

    config = CrawlerConfig('ContentAll')
    quality = config.get('quality')

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

    async_results = get_urls_async([by_search, dw_search, fx_search, hw_search])

    by_results = []
    dw_results = []
    fx_results = []
    hw_results = []

    for res in async_results:
        if check_is_site(res[1]) == 'BY':
            by_results = content_all_by_feed_search.by_search_results(res[0], by, quality)
        elif check_is_site(res[1]) == 'DW':
            dw_results = content_all_dw_feed_search.dw_search_results(res[0], quality)
        elif check_is_site(res[1]) == 'FX':
            fx_results = content_all_fx_feed_search.fx_search_results(
                content_all_fx_feed_search.fx_content_to_soup(res[0]), bl_query)
        elif check_is_site(res[1]) == 'HW':
            hw_results = content_all_hw_feed_search.hw_search_results(res[0], quality)

    if nk:
        nk_search = post_url('https://' + nk + "/search",
                             data={'search': bl_query.replace("+", " ")})
        nk_results = content_all_nk_feed_search.nk_search_results(nk_search, 'https://' + nk + '/', quality)
    else:
        nk_results = []

    password = ""
    for result in by_results:
        if "480p" in quality and check_release_not_sd(result["title"]):
            continue
        search_results.append({
            "title": result["title"],
            "link": result["link"],
            "password": password,
            "site": "BY",
            "size": result["size"],
            "source": result["source"],
            "imdb_id": result["imdb_id"]
        })

    password = dw.split('.')[0]
    for result in dw_results:
        if "480p" in quality and check_release_not_sd(result["title"]):
            continue
        search_results.append({
            "title": result["title"],
            "link": result["link"],
            "password": password,
            "site": "DW",
            "size": result["size"],
            "source": result["source"],
            "imdb_id": result["imdb_id"]
        })

    password = fx.split('.')[0]
    for result in fx_results:
        if "480p" in quality and check_release_not_sd(result["title"]):
            continue
        search_results.append({
            "title": result["title"],
            "link": result["link"],
            "password": password,
            "site": "FX",
            "size": result["size"],
            "source": result["source"],
            "imdb_id": result["imdb_id"]
        })

    password = hw.split('.')[0]
    for result in hw_results:
        if "480p" in quality and check_release_not_sd(result["title"]):
            continue
        search_results.append({
            "title": result["title"],
            "link": result["link"],
            "password": password,
            "site": "HW",
            "size": result["size"],
            "source": result["source"],
            "imdb_id": result["imdb_id"]
        })

    password = nk.split('.')[0].capitalize()
    for result in nk_results:
        if "480p" in quality and check_release_not_sd(result["title"]):
            continue
        search_results.append({
            "title": result["title"],
            "link": result["link"],
            "password": password,
            "site": "NK",
            "size": result["size"],
            "source": result["source"],
            "imdb_id": result["imdb_id"]
        })

    return search_results
