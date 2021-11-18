# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337

import json

import requests
from imdb import IMDb

import feedcrawler.search.shared.content_all
import feedcrawler.search.shared.content_shows
from feedcrawler import internal
from feedcrawler.common import decode_base64
from feedcrawler.common import encode_base64
from feedcrawler.common import sanitize
from feedcrawler.config import CrawlerConfig
from feedcrawler.db import FeedDb
from feedcrawler.imdb import clean_imdb_id


def imdb_movie(imdb_id):
    try:
        imdb_id = clean_imdb_id(imdb_id)
        ia = IMDb('https', languages='de-DE')
        output = ia.get_movie(imdb_id)
        title = sanitize(output.data['localized title'])
        year = str(output.data['year'])
        return title + " " + year
    except:
        if imdb_id is None:
            internal.logger.debug("Ein Film ohne IMDb-ID wurde angefordert.")
        else:
            print(u"[Ombi] - Fehler beim Abruf der IMDb für: " + imdb_id)
        return False


def imdb_show(imdb_id):
    try:
        imdb_id = clean_imdb_id(imdb_id)
        ia = IMDb('https', languages='de-DE')
        output = ia.get_movie(imdb_id)
        ia.update(output, 'episodes')
        title = sanitize(output.data['localized title'])
        seasons = output.data['episodes']
        eps = {}

        for sn in seasons:
            ep = []
            for e in seasons[sn]:
                ep.append(int(e))
            eps[int(sn)] = ep

        return title, eps
    except:
        if imdb_id is None:
            internal.logger.debug("Eine Serie ohne IMDb-ID wurde angefordert.")
        else:
            print(u"[Ombi] - Fehler beim Abruf der IMDb für: " + imdb_id)
        return False


def ombi(first_launch):
    db = FeedDb('Ombi')
    config = CrawlerConfig('Ombi')
    url = config.get('url')
    api = config.get('api')

    if not url or not api:
        return [0, 0]

    english = CrawlerConfig('FeedCrawler').get('english')

    try:
        requested_movies = requests.get(url + '/api/v1/Request/movie', headers={'ApiKey': api})
        requested_movies = json.loads(requested_movies.text)
        requested_shows = requests.get(url + '/api/v1/Request/tv', headers={'ApiKey': api})
        requested_shows = json.loads(requested_shows.text)
        len_movies = len(requested_movies)
        len_shows = len(requested_shows)
        if first_launch:
            internal.logger.debug("Erfolgreich mit Ombi verbunden.")
            print(u"Erfolgreich mit Ombi verbunden.")
    except:
        internal.logger.debug("Ombi ist nicht erreichbar!")
        print(u"Ombi ist nicht erreichbar!")
        return [0, 0]

    if requested_movies:
        internal.logger.debug(
            "Die Suchfunktion für Filme nutzt BY, FX und NK, sofern deren Hostnamen gesetzt wurden.")
    for r in requested_movies:
        if bool(r.get("approved")):
            if not bool(r.get("available")):
                imdb_id = r.get("imdbId")
                if not db.retrieve('movie_' + str(imdb_id)) == 'added':
                    title = imdb_movie(imdb_id)
                    if title:
                        best_result = feedcrawler.search.shared.content_all.get_best_result(title)
                        print(u"Film: " + title + u" durch Ombi hinzugefügt.")
                        if best_result:
                            feedcrawler.search.shared.content_all.download(best_result)
                        if english:
                            title = r.get('title')
                            best_result = feedcrawler.search.shared.content_all.get_best_result(title)
                            print(u"Film: " + title + u"durch Ombi hinzugefügt.")
                            if best_result:
                                feedcrawler.search.shared.content_all.download(best_result)
                        db.store('movie_' + str(imdb_id), 'added')

    if requested_shows:
        internal.logger.debug("Die Suchfunktion für Serien nutzt SJ, sofern der Hostname gesetzt wurde.")
    for r in requested_shows:
        imdb_id = r.get("imdbId")
        child_requests = r.get("childRequests")
        for cr in child_requests:
            if bool(cr.get("approved")):
                if not bool(cr.get("available")):
                    details = cr.get("seasonRequests")
                    for season in details:
                        sn = season.get("seasonNumber")
                        eps = []
                        episodes = season.get("episodes")
                        for episode in episodes:
                            if not bool(episode.get("available")):
                                enr = episode.get("episodeNumber")
                                s = str(sn)
                                if len(s) == 1:
                                    s = "0" + s
                                s = "S" + s
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
                                            payload = feedcrawler.search.shared.content_shows.get_best_result(title)
                                            if payload:
                                                payload = decode_base64(payload).split("|")
                                                payload = encode_base64(payload[0] + "|" + payload[1] + "|" + se)
                                                added_episode = feedcrawler.search.shared.content_shows.download(
                                                    payload)
                                                if not added_episode:
                                                    payload = decode_base64(payload).split("|")
                                                    payload = encode_base64(payload[0] + "|" + payload[1] + "|" + s)
                                                    add_season = feedcrawler.search.shared.content_shows.download(
                                                        payload)
                                                    for e in eps:
                                                        e = str(e)
                                                        if len(e) == 1:
                                                            e = "0" + e
                                                        se = s + "E" + e
                                                        db.store('show_' + str(imdb_id) + '_' + se, 'added')
                                                    if not add_season:
                                                        internal.logger.debug(
                                                            u"Konnte kein Release für " + title + " " + se + "finden.")
                                                    break
                                            db.store('show_' + str(imdb_id) + '_' + se, 'added')
                                    else:
                                        payload = feedcrawler.search.shared.content_shows.get_best_result(title)
                                        if payload:
                                            payload = decode_base64(payload).split("|")
                                            payload = encode_base64(payload[0] + "|" + payload[1] + "|" + s)
                                            feedcrawler.search.shared.content_shows.download(payload)
                                        for ep in eps:
                                            e = str(ep)
                                            if len(e) == 1:
                                                e = "0" + e
                                            se = s + "E" + e
                                            db.store('show_' + str(imdb_id) + '_' + se, 'added')
                                    print(u"Serie/Staffel/Episode: " + title + u" durch Ombi hinzugefügt.")

    return [len_movies, len_shows]
