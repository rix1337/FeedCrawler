# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul integriert die API von Ombi in die Feed-Suche des FeedCrawlers.

import json

import feedcrawler.external_sites.web_search.content_all
import feedcrawler.external_sites.web_search.content_shows
from feedcrawler.external_sites.metadata.imdb import get_episodes
from feedcrawler.external_sites.metadata.imdb import get_localized_title
from feedcrawler.external_sites.metadata.imdb import get_year
from feedcrawler.providers import shared_state
from feedcrawler.providers.common_functions import decode_base64
from feedcrawler.providers.common_functions import encode_base64
from feedcrawler.providers.common_functions import keep_alphanumeric_with_special_characters
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.http_requests.request_handler import request
from feedcrawler.providers.sqlite_database import FeedDb


def imdb_movie(imdb_id):
    try:
        title = keep_alphanumeric_with_special_characters(get_localized_title(imdb_id))
        year = str(get_year(imdb_id))
        return title + " " + year
    except:
        if imdb_id is None:
            shared_state.logger.debug("Ein Film ohne IMDb-ID wurde angefordert.")
        else:
            print("[Ombi] - Fehler beim Abruf der IMDb für: " + imdb_id)
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
            print("[Ombi] - Fehler beim Abruf der IMDb für: " + imdb_id)
        return False


def ombi_search(first_launch):
    db = FeedDb('Ombi')
    config = CrawlerConfig('Ombi')
    url = config.get('url')
    if url.endswith('/'):
        url = url[:-1]
        config.save('url', url)

    api = config.get('api')

    if not url or not api:
        return [0, 0]

    english = CrawlerConfig('FeedCrawler').get('english')

    try:
        requested_movies = request(url + '/api/v1/Request/movie', headers={'ApiKey': api})
        requested_movies = json.loads(requested_movies.text)
        requested_shows = request(url + '/api/v1/Request/tv', headers={'ApiKey': api})
        requested_shows = json.loads(requested_shows.text)
        len_movies = len(requested_movies)
        len_shows = len(requested_shows)
        if first_launch:
            shared_state.logger.debug("Erfolgreich mit Ombi verbunden.")
            print("Erfolgreich mit Ombi verbunden.")
    except:
        shared_state.logger.debug("Ombi ist nicht erreichbar!")
        print("Ombi ist nicht erreichbar!")
        return [0, 0]

    if requested_movies:
        shared_state.logger.debug(
            "Die Suchfunktion für Filme nutzt BY, FX, HW, NK und NX, sofern deren Hostnamen gesetzt wurden.")
    for r in requested_movies:
        if bool(r.get("approved")):
            if not bool(r.get("available")):
                imdb_id = r.get("imdbId")
                if imdb_id:
                    if not db.retrieve('movie_' + str(imdb_id)) == 'added':
                        title = imdb_movie(imdb_id)
                        if title:
                            best_result = feedcrawler.external_sites.web_search.content_all.get_best_result(title)
                            print("Film: " + title + " durch Ombi hinzugefügt.")
                            if best_result:
                                feedcrawler.external_sites.web_search.content_all.download(best_result)
                            if english:
                                title = r.get('title')
                                best_result = feedcrawler.external_sites.web_search.content_all.get_best_result(title)
                                print("Film: " + title + "durch Ombi hinzugefügt.")
                                if best_result:
                                    feedcrawler.external_sites.web_search.content_all.download(best_result)
                            db.store('movie_' + str(imdb_id), 'added')
                else:
                    print("Ein Film ohne IMDb-ID wurde in Ombi angefordert und kann nicht verarbeitet werden.")
                    shared_state.logger.debug(
                        "Ein Film ohne IMDb-ID wurde in Ombi angefordert und kann nicht verarbeitet werden.")

    if requested_shows:
        shared_state.logger.debug("Die Suchfunktion für Serien nutzt SF und SJ, sofern deren Hostnamen gesetzt wurden.")
    for r in requested_shows:
        imdb_id = r.get("imdbId")
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
                                                                "Konnte kein Release für " + title + " " + se + "finden.")
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
                                        print("Serie/Staffel/Folge: " + title + " durch Ombi hinzugefügt.")
        else:
            print("Eine Serie ohne IMDb-ID wurde in Ombi angefordert und kann nicht verarbeitet werden.")
            shared_state.logger.debug(
                "Eine Serie ohne IMDb-ID wurde in Ombi angefordert und kann nicht verarbeitet werden.")

    return [len_movies, len_shows]
