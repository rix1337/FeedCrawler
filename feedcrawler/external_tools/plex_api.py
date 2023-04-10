# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul integriert die API von Plex in die Feed-Suche des FeedCrawlers.

import re
from platform import uname
from urllib import parse
from uuid import getnode
from xml.etree import ElementTree

import feedcrawler.external_sites.web_search.content_all
import feedcrawler.external_sites.web_search.content_shows
from feedcrawler.external_sites.metadata.imdb import get_imdb_id_from_title
from feedcrawler.external_sites.metadata.imdb import get_localized_title
from feedcrawler.external_sites.metadata.imdb import get_year
from feedcrawler.providers import shared_state
from feedcrawler.providers.common_functions import keep_alphanumeric_with_special_characters
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.sqlite_database import FeedDb
from feedcrawler.providers.url_functions import get_url_headers
from feedcrawler.providers.version import get_version


def imdb_movie(imdb_id):
    try:
        title = keep_alphanumeric_with_special_characters(get_localized_title(imdb_id))
        year = str(get_year(imdb_id))
        return title + " " + year
    except:
        if imdb_id is None:
            shared_state.logger.debug("Ein Film ohne IMDb-ID wurde angefordert.")
        else:
            print("[Plex] - Fehler beim Abruf der IMDb für: " + imdb_id)
        return False


def imdb_show(imdb_id):
    try:
        title = keep_alphanumeric_with_special_characters(get_localized_title(imdb_id))

        return title
    except:
        if imdb_id is None:
            shared_state.logger.debug("Eine Serie ohne IMDb-ID wurde angefordert.")
        else:
            print("[Plex] - Fehler beim Abruf der IMDb für: " + imdb_id)
        return False


def get_imdb_id_from_plex_metadata(element, plex_headers):
    metadata = get_url_headers("https://metadata.provider.plex.tv" + element.attrib["key"] + "?includeExternalMedia=1",
                               headers=plex_headers)
    imdb = re.findall(r'id="imdb://(.*?)"', metadata["text"])
    if len(imdb) > 0:
        return imdb[0]
    else:
        print("[Plex] - Metadaten enthalten keine IMDb-ID für: " + element.attrib["title"])
        return None


def get_client_id():
    config = CrawlerConfig('Plex')
    client_id = config.get('client_id')
    if client_id:
        return client_id
    else:
        client_id = str(hex(getnode()))
        config.save('client_id', client_id)
        return client_id


def get_plex_headers(token):
    return {
        'X-Plex-Platform': uname()[0],
        'X-Plex-Platform-Version': uname()[2],
        'X-Plex-Provides': 'controller',
        'X-Plex-Product': 'FeedCrawler',
        'X-Plex-Version': get_version(),
        'X-Plex-Device': uname()[0],
        'X-Plex-Device-Name': uname()[1],
        'X-Plex-Client-Identifier': get_client_id(),
        'X-Plex-Sync-Version': '2',
        'X-Plex-Features': 'external-media',
        'X-Plex-Token': token
    }


def plex_search(first_launch):
    db = FeedDb('Plex')
    config = CrawlerConfig('Plex')

    server_url = config.get('url')
    token = config.get('api')

    if not server_url or not token:
        return [0, 0]

    plex_headers = get_plex_headers(token)
    english = CrawlerConfig('FeedCrawler').get('english')

    try:
        params = [
            'includeCollections=0'
            'includeExternalMedia=1'
            'sort=watchlistedAt:desc'
        ]

        metadata_url = 'https://metadata.provider.plex.tv/library/sections/watchlist/all?' + "&".join(params)
        watchlist_content = get_url_headers(metadata_url, headers=plex_headers)

        if not watchlist_content["status_code"] == 200:
            print("[Plex] - Fehler beim Abruf der Plex Watchlist: " + watchlist_content["text"])
            return [0, 0]

        watchlist = ElementTree.fromstring(watchlist_content["text"])

        requested_movies = []
        requested_shows = []

        for element in watchlist:
            title = element.attrib["title"]

            library_tag = '&type=2' if element.attrib["type"] == "show" else '&type=1'
            library_item_url = '/library/all?guid=' + parse.quote(element.attrib["guid"], safe='') + library_tag
            library_search = get_url_headers(server_url + library_item_url, headers=plex_headers)

            search_result = ElementTree.fromstring(library_search["text"])
            element_in_plex_library = int(search_result.attrib["size"])

            if not element_in_plex_library:
                if element.attrib["type"] == "movie":
                    imdb_id = get_imdb_id_from_plex_metadata(element, plex_headers)
                    if imdb_id:
                        requested_movies.append({
                            "title": title,
                            "imdb_id": imdb_id
                        })
                elif element.attrib["type"] == "show":
                    year = element.attrib["year"]
                    imdb_id = get_imdb_id_from_title(title + " " + year, current_list="List_ContentAll_Seasons",
                                                     language="en", year_in_title=True)
                    if imdb_id:
                        requested_shows.append({
                            "title": title,
                            "imdb_id": imdb_id
                        })
                else:
                    print("[Plex] - Unbekannter Typ: " + element.attrib["type"] + " - " + element.attrib["title"])

        len_movies = len(requested_movies)
        len_shows = len(requested_shows)
        if first_launch:
            shared_state.logger.debug("Erfolgreich mit Plex verbunden.")
            print("Erfolgreich mit Plex verbunden.")
    except:
        shared_state.logger.debug("Plex ist nicht erreichbar!")
        print("Plex ist nicht erreichbar!")
        return [0, 0]

    if requested_movies:
        shared_state.logger.debug(
            "Die Suchfunktion für Filme nutzt BY, FX, HW, NK und NX, sofern deren Hostnamen gesetzt wurden.")
    for r in requested_movies:
        imdb_id = r.get("imdb_id")
        if imdb_id:
            if not db.retrieve('movie_' + str(imdb_id)) == 'added':
                title = imdb_movie(imdb_id)
                if title:
                    best_result = feedcrawler.external_sites.web_search.content_all.get_best_result(title)
                    print("Film: " + title + " durch Plex hinzugefügt.")
                    if best_result:
                        feedcrawler.external_sites.web_search.content_all.download(best_result)
                    if english:
                        title = r.get('title')
                        best_result = feedcrawler.external_sites.web_search.content_all.get_best_result(title)
                        print("Film: " + title + "durch Plex hinzugefügt.")
                        if best_result:
                            feedcrawler.external_sites.web_search.content_all.download(best_result)
                    db.store('movie_' + str(imdb_id), 'added')
        else:
            print("Ein Film ohne IMDb-ID wurde in Plex angefordert und kann nicht verarbeitet werden.")
            shared_state.logger.debug(
                "Ein Film ohne IMDb-ID wurde in Plex angefordert und kann nicht verarbeitet werden.")

    if requested_shows:
        shared_state.logger.debug("Die Suchfunktion für Serien nutzt SF und SJ, sofern deren Hostnamen gesetzt wurden.")
    for r in requested_shows:
        imdb_id = r.get("imdb_id")
        if imdb_id:
            if not db.retrieve('show_' + str(imdb_id)) == 'added':
                title = imdb_show(imdb_id)
                if title:
                    best_result = feedcrawler.external_sites.web_search.content_shows.get_best_result(title)
                    print("Serie: " + title + " durch Plex hinzugefügt.")
                    if best_result:
                        feedcrawler.external_sites.web_search.content_shows.download(best_result)
                    if english:
                        title = r.get('title')
                        best_result = feedcrawler.external_sites.web_search.content_shows.get_best_result(title)
                        print("Serie: " + title + "durch Plex hinzugefügt.")
                        if best_result:
                            feedcrawler.external_sites.web_search.content_shows.download(best_result)
                    db.store('show_' + str(imdb_id), 'added')
        else:
            print("Eine Serie ohne IMDb-ID wurde in Plex angefordert und kann nicht verarbeitet werden.")
            shared_state.logger.debug(
                "Eine Serie ohne IMDb-ID wurde in Plex angefordert und kann nicht verarbeitet werden.")

    return [len_movies, len_shows]
