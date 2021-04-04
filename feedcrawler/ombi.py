# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337

import json
import re
import requests
from bs4 import BeautifulSoup

import feedcrawler.search.shared.content_all
import feedcrawler.search.shared.content_shows
from feedcrawler.common import decode_base64
from feedcrawler.common import encode_base64
from feedcrawler.common import sanitize
from feedcrawler.config import RssConfig
from feedcrawler.db import FeedDb
from feedcrawler.url import get_url_headers


def get_imdb(url, configfile, dbfile, scraper):
    result = get_url_headers(url, configfile, dbfile,
                             scraper=scraper,
                             headers={'Accept-Language': 'de'}
                             )
    output = result[0].text
    scraper = result[1]
    return output, scraper


def get_title(input):
    try:
        raw_title = re.findall(r"<title>(.*) \((?:.*(?:19|20)\d{2})\) - IMDb</title>", input)[0]
    except:
        raw_title = re.findall(r'<meta name="title" content="(.*) \((?:.*(?:19|20)\d{2}).*\) - IMDb"', input)[0]
    return sanitize(raw_title)


def get_year(input):
    try:
        raw_year = re.findall(r"<title>(?:.*) \((.*(?:19|20)\d{2})\) - IMDb</title>", input)[0]
    except:
        raw_year = re.findall(r'<meta name="title" content="(?:.*) \((.*(?:19|20)\d{2}).*\) - IMDb"', input)[0]
    return sanitize(raw_year)


def imdb_movie(imdb_id, configfile, dbfile, scraper):
    try:
        result = get_imdb('https://www.imdb.com/title/' + imdb_id, configfile, dbfile, scraper)
        output = result[0]
        scraper = result[1]

        title = get_title(output)
        year = get_year(output)

        return title + " " + year, scraper
    except:
        print(u"[Ombi] - Fehler beim Abruf der IMDb für: " + imdb_id)
        return False, False


def imdb_show(ombi_imdb_id, configfile, dbfile, scraper):
    try:
        result = get_imdb('https://www.imdb.com/title/' + ombi_imdb_id, configfile, dbfile, scraper)
        output = result[0]
        scraper = result[1]

        title = get_title(output)

        eps = {}
        soup = BeautifulSoup(output, 'lxml')
        imdb_id = soup.find_all("meta", property="pageId")[0]["content"]
        seasons = soup.find_all("a", href=re.compile(r'.*/title/' + imdb_id + r'/episodes\?season=.*'))
        if not seasons:
            episode_guide = soup.find_all("a", {"class": "np_episode_guide"})[0]["href"]
            result = get_imdb("https://www.imdb.com/" + episode_guide, configfile, dbfile, scraper)
            output = result[0]
            scraper = result[1]
            soup = BeautifulSoup(output, 'lxml')
            imdb_id = soup.find_all("meta", property="pageId")[0]["content"]
            seasons = soup.find_all("a", href=re.compile(r'.*/title/' + imdb_id + r'/episodes\?season=.*'))

        latest_season = int(seasons[0].text)
        total_seasons = list(range(1, latest_season + 1))
        for sn in total_seasons:
            result = get_imdb("https://www.imdb.com/title/" + imdb_id + "/episodes?season=" + str(sn), configfile,
                              dbfile, scraper)
            output = result[0]
            scraper = result[1]

            ep = []
            soup = BeautifulSoup(output, 'lxml')
            episodes = soup.find_all("meta", itemprop="episodeNumber")
            for e in episodes:
                ep.append(int(e['content']))
            eps[sn] = ep

        return title, eps, scraper
    except:
        print(u"[Ombi] - Fehler beim Abruf der IMDb für: " + ombi_imdb_id)
        return False, False, False


def ombi(configfile, dbfile, device, log_debug, first_launch):
    db = FeedDb(dbfile, 'Ombi')
    config = RssConfig('Ombi', configfile)
    url = config.get('url')
    api = config.get('api')

    if not url or not api:
        return [device, [0, 0]]

    english = RssConfig('FeedCrawler', configfile).get('english')

    try:
        requested_movies = requests.get(url + '/api/v1/Request/movie', headers={'ApiKey': api})
        requested_movies = json.loads(requested_movies.text)
        requested_shows = requests.get(url + '/api/v1/Request/tv', headers={'ApiKey': api})
        requested_shows = json.loads(requested_shows.text)
        len_movies = len(requested_movies)
        len_shows = len(requested_shows)
        if first_launch:
            log_debug("Erfolgreich mit Ombi verbunden.")
            print(u"Erfolgreich mit Ombi verbunden.")
    except:
        log_debug("Ombi ist nicht erreichbar!")
        print(u"Ombi ist nicht erreichbar!")
        return [False, [0, 0]]

    scraper = False

    if requested_movies:
        log_debug("Die Suchfunktion für Filme nutzt BY, DW, FX und NK, sofern deren Hostnamen gesetzt wurden.")
    for r in requested_movies:
        if bool(r.get("approved")):
            if not bool(r.get("available")):
                imdb_id = r.get("imdbId")
                if not db.retrieve('movie_' + str(imdb_id)) == 'added':
                    response = imdb_movie(imdb_id, configfile, dbfile, scraper)
                    title = response[0]
                    if title:
                        scraper = response[1]
                        best_result = feedcrawler.search.shared.content_all.get_best_result(title, configfile, dbfile)
                        print(u"Film: " + title + u" durch Ombi hinzugefügt.")
                        if best_result:
                            feedcrawler.search.shared.content_all.download(best_result, device, configfile, dbfile)
                        if english:
                            title = r.get('title')
                            best_result = feedcrawler.search.shared.content_all.get_best_result(title, configfile,
                                                                                                dbfile)
                            print(u"Film: " + title + u"durch Ombi hinzugefügt.")
                            if best_result:
                                feedcrawler.search.shared.content_all.download(best_result, device, configfile,
                                                                               dbfile)
                        db.store('movie_' + str(imdb_id), 'added')
                    else:
                        log_debug("Titel für IMDB-ID nicht abrufbar: " + imdb_id)

    if requested_shows:
        log_debug("Die Suchfunktion für Serien nutzt SJ, sofern dessen Hostname gesetzt wurde.")
    for r in requested_shows:
        imdb_id = r.get("imdbId")
        infos = None
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
                            if not infos:
                                infos = imdb_show(imdb_id, configfile, dbfile, scraper)
                            if infos:
                                title = infos[0]
                                all_eps = infos[1]
                                scraper = infos[2]
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
                                            payload = feedcrawler.search.shared.content_shows.get_best_result(title,
                                                                                                              configfile,
                                                                                                              dbfile)
                                            if payload:
                                                payload = decode_base64(payload).split("|")
                                                payload = encode_base64(payload[0] + "|" + payload[1] + "|" + se)
                                                added_episode = feedcrawler.search.shared.content_shows.download(
                                                    payload, configfile, dbfile)
                                                if not added_episode:
                                                    payload = decode_base64(payload).split("|")
                                                    payload = encode_base64(payload[0] + "|" + payload[1] + "|" + s)
                                                    add_season = feedcrawler.search.shared.content_shows.download(
                                                        payload, configfile, dbfile)
                                                    for e in eps:
                                                        e = str(e)
                                                        if len(e) == 1:
                                                            e = "0" + e
                                                        se = s + "E" + e
                                                        db.store('show_' + str(imdb_id) + '_' + se, 'added')
                                                    if not add_season:
                                                        log_debug(
                                                            u"Konnte kein Release für " + title + " " + se + "finden.")
                                                    break
                                            db.store('show_' + str(imdb_id) + '_' + se, 'added')
                                    else:
                                        payload = feedcrawler.search.shared.content_shows.get_best_result(title,
                                                                                                          configfile,
                                                                                                          dbfile)
                                        if payload:
                                            payload = decode_base64(payload).split("|")
                                            payload = encode_base64(payload[0] + "|" + payload[1] + "|" + s)
                                            feedcrawler.search.shared.content_shows.download(payload, configfile,
                                                                                             dbfile)
                                        for ep in eps:
                                            e = str(ep)
                                            if len(e) == 1:
                                                e = "0" + e
                                            se = s + "E" + e
                                            db.store('show_' + str(imdb_id) + '_' + se, 'added')
                                    print(u"Serie/Staffel/Episode: " + title + u" durch Ombi hinzugefügt.")

    return [device, [len_movies, len_shows]]
