# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul integriert die API von Overseerr in die Feed-Suche des FeedCrawlers.

import json

import feedcrawler.external_sites.web_search.content_all
import feedcrawler.external_sites.web_search.content_shows
from feedcrawler.providers import shared_state
from feedcrawler.providers.common_functions import decode_base64
from feedcrawler.providers.common_functions import encode_base64
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.http_requests.request_handler import request
from feedcrawler.providers.sqlite_database import FeedDb


def overseerr_search(first_launch):
    db = FeedDb('Overseerr')
    config = CrawlerConfig('Overseerr')
    url = config.get('url')
    if url.endswith('/'):
        url = url[:-1]
        config.save('url', url)

    api = config.get('api')

    if not url or not api:
        return [0, 0]

    english = CrawlerConfig('FeedCrawler').get('english')

    try:
        requested_titles_raw = request(url + '/api/v1/request?take=999', headers={'X-Api-Key': api})
        if requested_titles_raw.status_code != 200:
            shared_state.logger.debug("Overseerr API-Key ungültig!")
            print("Overseerr API-Key ungültig!")
            return [0, 0]

        requested_titles = json.loads(requested_titles_raw.text)

        requested_movies = []
        requested_shows = []

        for item in requested_titles['results']:
            if item['status'] == 2:
                shared_state.logger.debug("Anfrage mit ID " + str(item['id']) + " ist freigegeben.")
                if item['type'] == 'movie':
                    details_raw = request(url + '/api/v1/movie/' + str(item['media']['tmdbId']),
                                          headers={'X-Api-Key': api})
                    if details_raw.status_code != 200:
                        shared_state.logger.debug(
                            "Overseerr fehlen die notwendigen Details für tmbbId: " + str(item['media']['tmdbId']))
                        print("Overseerr fehlen die notwendigen Details für tmbbId: " + str(item['media']['tmdbId']))
                    else:
                        details = json.loads(details_raw.text)
                        requested_movies.append(details)
                elif item['type'] == 'tv':
                    details_raw = request(url + '/api/v1/tv/' + str(item['media']['tmdbId']),
                                          headers={'X-Api-Key': api})
                    if details_raw.status_code != 200:
                        shared_state.logger.debug(
                            "Overseerr fehlen die notwendigen Details für tmbbId: " + str(item['media']['tmdbId']))
                        print("Overseerr fehlen die notwendigen Details für tmbbId: " + str(item['media']['tmdbId']))
                    else:
                        details = json.loads(details_raw.text)
                        requested_shows.append(details)
            else:
                shared_state.logger.debug("Anfrage mit ID " + str(item['id']) + " ist noch nicht freigegeben.")

        len_movies = len(requested_movies)
        len_shows = len(requested_shows)
        if first_launch:
            shared_state.logger.debug("Erfolgreich mit Overseerr verbunden.")
            print("Erfolgreich mit Overseerr verbunden.")
    except:
        shared_state.logger.debug("Overseerr ist nicht erreichbar!")
        print("Overseerr ist nicht erreichbar!")
        return [0, 0]

    if requested_movies:
        shared_state.logger.debug(
            "Die Suchfunktion für Filme nutzt BY, FX, HW, NK und NX, sofern deren Hostnamen gesetzt wurden.")
    for r in requested_movies:
        item_id = r["id"]
        if not db.retrieve('movie_' + str(item_id)) == 'added':
            title = r["title"]
            if title:
                best_result = feedcrawler.external_sites.web_search.content_all.get_best_result(title)
                print("Film: " + title + " durch Overseerr hinzugefügt.")
                if best_result:
                    feedcrawler.external_sites.web_search.content_all.download(best_result)
                if english:
                    title = r.get('title')
                    best_result = feedcrawler.external_sites.web_search.content_all.get_best_result(title)
                    print("Film: " + title + "durch Overseerr hinzugefügt.")
                    if best_result:
                        feedcrawler.external_sites.web_search.content_all.download(best_result)
                db.store('movie_' + str(item_id), 'added')

    if requested_shows:
        shared_state.logger.debug("Die Suchfunktion für Serien nutzt SF und SJ, sofern deren Hostnamen gesetzt wurden.")
    for r in requested_shows:
        item_id = r["id"]
        seasons = r['seasons']
        for season in seasons:
            season = str(season['seasonNumber'])
            if len(season) == 1:
                season = "s0" + season
            if not db.retrieve('show_' + str(item_id) + "_" + str(season)) == 'added':
                title = r["name"]
                if title:
                    payload = feedcrawler.external_sites.web_search.content_shows.get_best_result(title)
                    if payload:
                        payload = decode_base64(payload).split("|")
                        payload = encode_base64(payload[0] + "|" + payload[1] + "|" + season)
                        if feedcrawler.external_sites.web_search.content_shows.download(payload):
                            db.store('show_' + str(item_id) + "_" + str(season), 'added')
                            print("Serie/Staffel/Folge: " + title + " durch Overseerr hinzugefügt.")

    return [len_movies, len_shows]
