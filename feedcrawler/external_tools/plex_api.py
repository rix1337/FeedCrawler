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
from feedcrawler.external_sites.metadata.imdb import get_episodes
from feedcrawler.external_sites.metadata.imdb import get_imdb_id_from_title
from feedcrawler.external_sites.metadata.imdb import get_localized_title
from feedcrawler.external_sites.metadata.imdb import get_year
from feedcrawler.providers import shared_state
from feedcrawler.providers.common_functions import decode_base64
from feedcrawler.providers.common_functions import encode_base64
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
            print(u"[Plex] - Fehler beim Abruf der IMDb für: " + imdb_id)
        return False


def imdb_show(imdb_id):
    try:
        title = keep_alphanumeric_with_special_characters(get_localized_title(imdb_id))
        seasons = get_episodes(imdb_id)

        return title, seasons
    except:
        if imdb_id is None:
            shared_state.logger.debug("Eine Serie ohne IMDb-ID wurde angefordert.")
        else:
            print(u"[Plex] - Fehler beim Abruf der IMDb für: " + imdb_id)
        return False


def get_imdb_id_from_plex_metadata(element, plex_headers):
    metadata = get_url_headers("https://metadata.provider.plex.tv" + element.attrib["key"] + "?includeExternalMedia=1",
                               headers=plex_headers)
    imdb = re.findall(r'id="imdb://(.*?)"', metadata["text"])
    if len(imdb) > 0:
        return imdb[0]
    else:
        print(u"[Plex] - Metadaten enthalten keine IMDb-ID für: " + element.attrib["title"])
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
            print(u"[Plex] - Fehler beim Abruf der Plex Watchlist: " + watchlist_content["text"])
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
                    print(u"[Plex] - Unbekannter Typ: " + element.attrib["type"] + " - " + element.attrib["title"])

        len_movies = len(requested_movies)
        len_shows = len(requested_shows)
        if first_launch:
            shared_state.logger.debug("Erfolgreich mit Plex verbunden.")
            print(u"Erfolgreich mit Plex verbunden.")
    except:
        shared_state.logger.debug("Plex ist nicht erreichbar!")
        print(u"Plex ist nicht erreichbar!")
        return [0, 0]

    if requested_movies:
        shared_state.logger.debug(
            "Die Suchfunktion für Filme nutzt BY, FX, HW und NK, sofern deren Hostnamen gesetzt wurden.")
    for r in requested_movies:
        imdb_id = r.get("imdb_id")
        if imdb_id:
            if not db.retrieve('movie_' + str(imdb_id)) == 'added':
                title = imdb_movie(imdb_id)
                if title:
                    best_result = feedcrawler.external_sites.web_search.content_all.get_best_result(title)
                    print(u"Film: " + title + u" durch Plex hinzugefügt.")
                    if best_result:
                        feedcrawler.external_sites.web_search.content_all.download(best_result)
                    if english:
                        title = r.get('title')
                        best_result = feedcrawler.external_sites.web_search.content_all.get_best_result(title)
                        print(u"Film: " + title + u"durch Plex hinzugefügt.")
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
            child_requests = r.get("childRequests")
            for cr in child_requests:
                if bool(cr.get("approved")):
                    if not bool(cr.get("available")):
                        details = cr.get("seasonRequests")
                        for season in details:
                            sn = season.get("seasonNumber")
                            s = str(sn)
                            if len(s) == 1:
                                s = "0" + s
                            s = "S" + s
                            eps = []
                            episodes = season.get("episodes")
                            for episode in episodes:
                                if not bool(episode.get("available")):
                                    enr = episode.get("episodeNumber")
                                    e = str(enr)
                                    if len(e) == 1:
                                        e = "0" + e
                                    se = s + "E" + e
                                    if not db.retrieve('show_' + str(imdb_id) + '_' + se) == 'added':
                                        eps.append(enr)
                            if eps:
                                infos = imdb_show(imdb_id)
                                if infos:
                                    title = infos[0]
                                    all_eps = infos[1]
                                    check_sn = False
                                    if all_eps:
                                        check_sn = all_eps.get(sn)
                                    if check_sn:
                                        sn_length = len(eps)
                                        check_sn_length = len(check_sn)
                                        if check_sn_length > sn_length:
                                            for ep in eps:
                                                e = str(ep)
                                                if len(e) == 1:
                                                    e = "0" + e
                                                se = s + "E" + e
                                                payload = feedcrawler.external_sites.web_search. \
                                                    content_shows.get_best_result(title)
                                                if payload:
                                                    payload = decode_base64(payload).split("|")
                                                    payload = encode_base64(payload[0] + "|" + payload[1] + "|" + se)
                                                    added_episode = feedcrawler.external_sites.web_search. \
                                                        content_shows.download(payload)
                                                    if not added_episode:
                                                        payload = decode_base64(payload).split("|")
                                                        payload = encode_base64(payload[0] + "|" + payload[1] + "|" + s)
                                                        add_season = feedcrawler.external_sites.web_search. \
                                                            content_shows.download(payload)
                                                        for e in eps:
                                                            e = str(e)
                                                            if len(e) == 1:
                                                                e = "0" + e
                                                            se = s + "E" + e
                                                            db.store('show_' + str(imdb_id) + '_' + se, 'added')
                                                        if not add_season:
                                                            shared_state.logger.debug(
                                                                u"Konnte kein Release für " + title + " " + se + "finden.")
                                                        break
                                                db.store('show_' + str(imdb_id) + '_' + se, 'added')
                                        else:
                                            payload = feedcrawler.external_sites.web_search. \
                                                content_shows.get_best_result(title)
                                            if payload:
                                                payload = decode_base64(payload).split("|")
                                                payload = encode_base64(payload[0] + "|" + payload[1] + "|" + s)
                                                feedcrawler.external_sites.web_search.content_shows.download(payload)
                                            for ep in eps:
                                                e = str(ep)
                                                if len(e) == 1:
                                                    e = "0" + e
                                                se = s + "E" + e
                                                db.store('show_' + str(imdb_id) + '_' + se, 'added')
                                        print(u"Serie/Staffel/Episode: " + title + u" durch Plex hinzugefügt.")
        else:
            print("Eine Serie ohne IMDb-ID wurde in Plex angefordert und kann nicht verarbeitet werden.")
            shared_state.logger.debug(
                "Eine Serie ohne IMDb-ID wurde in Plex angefordert und kann nicht verarbeitet werden.")

    return [len_movies, len_shows]
