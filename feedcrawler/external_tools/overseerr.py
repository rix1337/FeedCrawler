# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul integriert die API von Overseerr in die Feed-Suche des FeedCrawlers.

import json

import feedcrawler.search.shared.content_all
import feedcrawler.search.shared.content_shows
from feedcrawler import internal
from feedcrawler.common import decode_base64
from feedcrawler.common import encode_base64
from feedcrawler.config import CrawlerConfig
from feedcrawler.db import FeedDb
from feedcrawler.http_requests.request_handler import request


def overseerr(first_launch):
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
            internal.logger.debug("Overseerr API-Key ungültig!")
            print(u"Overseerr API-Key ungültig!")
            return [0, 0]

        requested_titles = json.loads(requested_titles_raw.text)

        requested_movies = []
        requested_shows = []

        for item in requested_titles['results']:
            if item['status'] == 2:
                internal.logger.debug("Anfrage mit ID " + str(item['id']) + " ist freigegeben.")
                if item['type'] == 'movie':
                    details_raw = request(url + '/api/v1/movie/' + str(item['media']['tmdbId']),
                                          headers={'X-Api-Key': api})
                    if details_raw.status_code != 200:
                        internal.logger.debug(
                            "Overseerr fehlen die notwendigen Details für tmbbId: " + str(item['media']['tmdbId']))
                        print(u"Overseerr fehlen die notwendigen Details für tmbbId: " + str(item['media']['tmdbId']))
                    else:
                        details = json.loads(details_raw.text)
                        requested_movies.append(details)
                elif item['type'] == 'tv':
                    details_raw = request(url + '/api/v1/tv/' + str(item['media']['tmdbId']),
                                          headers={'X-Api-Key': api})
                    if details_raw.status_code != 200:
                        internal.logger.debug(
                            "Overseerr fehlen die notwendigen Details für tmbbId: " + str(item['media']['tmdbId']))
                        print(u"Overseerr fehlen die notwendigen Details für tmbbId: " + str(item['media']['tmdbId']))
                    else:
                        details = json.loads(details_raw.text)
                        requested_shows.append(details)
            else:
                internal.logger.debug("Anfrage mit ID " + str(item['id']) + " ist noch nicht freigegeben.")

        len_movies = len(requested_movies)
        len_shows = len(requested_shows)
        if first_launch:
            internal.logger.debug("Erfolgreich mit Overseerr verbunden.")
            print(u"Erfolgreich mit Overseerr verbunden.")
    except:
        internal.logger.debug("Overseerr ist nicht erreichbar!")
        print(u"Overseerr ist nicht erreichbar!")
        return [0, 0]

    if requested_movies:
        internal.logger.debug(
            "Die Suchfunktion für Filme nutzt BY, FX, HW und NK, sofern deren Hostnamen gesetzt wurden.")
    for r in requested_movies:
        item_id = r["id"]
        if not db.retrieve('movie_' + str(item_id)) == 'added':
            title = r["title"]
            if title:
                best_result = feedcrawler.search.shared.content_all.get_best_result(title)
                print(u"Film: " + title + u" durch Overseerr hinzugefügt.")
                if best_result:
                    feedcrawler.search.shared.content_all.download(best_result)
                if english:
                    title = r.get('title')
                    best_result = feedcrawler.search.shared.content_all.get_best_result(title)
                    print(u"Film: " + title + u"durch Overseerr hinzugefügt.")
                    if best_result:
                        feedcrawler.search.shared.content_all.download(best_result)
                db.store('movie_' + str(item_id), 'added')

    if requested_shows:
        internal.logger.debug("Die Suchfunktion für Serien nutzt SF und SJ, sofern deren Hostnamen gesetzt wurden.")
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
                    payload = feedcrawler.search.shared.content_shows.get_best_result(title)
                    if payload:
                        payload = decode_base64(payload).split("|")
                        payload = encode_base64(payload[0] + "|" + payload[1] + "|" + season)
                        if feedcrawler.search.shared.content_shows.download(payload):
                            db.store('show_' + str(item_id) + "_" + str(season), 'added')
                            print(u"Serie/Staffel/Episode: " + title + u" durch Overseerr hinzugefügt.")

    return [len_movies, len_shows]
