# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul durchsucht die Web-Suchen vieler Seiten des Typs content_all auf Basis einer standardisierten Struktur.

import re

from bs4 import BeautifulSoup

from feedcrawler import internal
from feedcrawler.common import check_hoster
from feedcrawler.common import check_is_site
from feedcrawler.common import decode_base64
from feedcrawler.common import is_retail
from feedcrawler.common import sanitize
from feedcrawler.common import simplified_search_term_in_title
from feedcrawler.config import CrawlerConfig
from feedcrawler.db import ListDb, FeedDb
from feedcrawler.external_sites.shared.imdb import get_imdb_id_from_content
from feedcrawler.external_sites.shared.imdb import get_imdb_id_from_link
from feedcrawler.external_sites.shared.internal_feed import add_decrypt_instead_of_download
from feedcrawler.external_sites.shared.internal_feed import fx_get_details
from feedcrawler.external_sites.shared.internal_feed import fx_get_download_links
from feedcrawler.notifiers import notify
from feedcrawler.search.search import get, rate
from feedcrawler.url import get_redirected_url
from feedcrawler.url import get_url
from feedcrawler.url import get_urls_async


def get_best_result(title):
    title = sanitize(title)
    try:
        bl_results = get(title, only_content_all=True)[0]
    except:
        return False

    best_score = -999
    best_match = False
    best_payload = False
    for result in bl_results:
        payload = result.get('payload')
        result = result.get('title')
        if simplified_search_term_in_title(title, result):
            score = rate(result)
            if score > best_score:
                best_score = score
                best_match = result
                best_payload = payload

    if not best_match or not best_payload:
        internal.logger.debug(u'Kein Treffer für die Suche nach ' + title + '! Suchliste ergänzt.')
        liste = "List_ContentAll_Movies"
        cont = ListDb(liste).retrieve()
        if not cont:
            cont = ""
        if title not in cont:
            ListDb(liste).store(title)
        return False
    if not is_retail(best_match, True):
        internal.logger.debug(u'Kein Retail-Release für die Suche nach ' + title + ' gefunden! Suchliste ergänzt.')
        liste = "List_ContentAll_Movies"
        cont = ListDb(liste).retrieve()
        if not cont:
            cont = ""
        if title not in cont:
            ListDb(liste).store(title)
        return best_payload
    else:
        internal.logger.debug('Bester Treffer für die Suche nach ' + title + ' ist ' + best_match)
        return best_payload


def download(payload):
    config = CrawlerConfig('ContentAll')
    db = FeedDb('FeedCrawler')
    hostnames = CrawlerConfig('Hostnames')
    by = hostnames.get('by')
    nk = hostnames.get('nk')

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

        soup = BeautifulSoup(response, 'html5lib')
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
                size = details.findAll("td", {"align": "LEFT"})[-1].text.split(" ", 1)[1].strip()
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
                    link = BeautifulSoup(link[0], 'html5lib').find("a", href=re.compile("/go\.php\?"))
                    if link:
                        url_hosters.append([link["href"], link.text.replace(" ", "")])
        elif "NK" in site:
            key = soup.find("span", {"class": "subtitle"}).text
            details = soup.find("div", {"class": "article"})
            try:
                imdb_link = details.find("a", href=re.compile("imdb.com"))
                imdb_id = get_imdb_id_from_link(key, imdb_link["href"])
            except:
                imdb_id = ""

            try:
                size = details.find("span", text=re.compile(r"(size|größe)", re.IGNORECASE)).next.next.strip()
            except:
                size = ""

            hosters = soup.find_all("a", href=re.compile("/go/"))
            for hoster in hosters:
                url_hosters.append(['https://' + nk + hoster["href"], hoster.text])
        elif "FX" in site:
            key = payload[2]
        elif "HW" in site:
            key = soup.find("h2", {"class": "entry-title"}).text.strip()

            try:
                imdb_id = get_imdb_id_from_content(key, str(soup))
            except:
                imdb_id = ""

            try:
                size = soup.find("strong",
                                 text=re.compile(
                                     r"(size|größe)", re.IGNORECASE)).next.next.text.replace("|", "").strip()
            except:
                size = ""

            download_links = soup.findAll("a", href=re.compile('filecrypt'))
            links_string = ""
            for link in download_links:
                links_string += str(link)
            url_hosters = re.findall(r'href="([^"\'>]*)".+?(.+?)<', links_string)
            password = payload[1]
        else:
            return False

        links = {}
        if "FX" in site:
            class FX:
                unused = ""

            details = fx_get_details(response, key)
            size = details["size"]
            imdb_id = details["imdb_id"]

            download_links = fx_get_download_links(FX, response, key)
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
                internal.logger.info(log_entry)
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
                internal.logger.info(log_entry)
                notify([{"text": log_entry, "imdb_id": imdb_id}])
                return [key]
    else:
        return False
