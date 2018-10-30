# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import json

import requests

from rsscrawler import search
from rsscrawler.common import sanitize
from rsscrawler.rssconfig import RssConfig
from rsscrawler.rssdb import RssDb
from rsscrawler.url import get_url_headers
from rsscrawler.url import post_url_json


def mdb(configfile, dbfile, tmdbid, mdb_api):
    get_title = get_url_headers(
        'https://api.themoviedb.org/3/movie/' + str(tmdbid) + '?api_key=' + mdb_api + '&language=de-DE', configfile,
        dbfile, headers={'Content-Type': 'application/json'})
    raw_title = json.loads(get_title.text).get("title")
    title = sanitize(raw_title)
    return title


def get_tvdb_token(configfile, dbfile, tvd_user, tvd_userkey, tvd_api):
    db = RssDb(dbfile, 'Ombi')
    response = post_url_json("https://api.thetvdb.com/login", configfile, dbfile, json={
        'username': tvd_user,
        'userkey': tvd_userkey,
        'apikey': tvd_api,
    })
    response = json.loads(response)
    token = response.get('token')
    db.delete("tvdb_token")
    db.store("tvdb_token", token)
    return token


def tvdb(configfile, dbfile, tvdbid, tvd_user, tvd_userkey, tvd_api):
    db = RssDb(dbfile, 'Ombi')
    token = db.retrieve('tvdb_token')

    if not token:
        token = get_tvdb_token(configfile, dbfile, tvd_user, tvd_userkey, tvd_api)

    get_info = get_url_headers('https://api.thetvdb.com/series/' + str(tvdbid), configfile, dbfile,
                               headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json',
                                        'Accept': 'application/json', 'Accept-Language': 'de'})

    if get_info.status_code == 401:
        token = get_tvdb_token(configfile, dbfile, tvd_user, tvd_userkey, tvd_api)
        get_info = get_url_headers('https://api.thetvdb.com/series/' + str(tvdbid), configfile, dbfile,
                                   headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json',
                                            'Accept': 'application/json', 'Accept-Language': 'de'})

    raw_data = json.loads(get_info.text)
    raw_info = raw_data.get('data')
    raw_title = raw_info.get('seriesName')
    if not raw_title:
        get_info = get_url_headers('https://api.thetvdb.com/series/' + str(tvdbid), configfile, dbfile,
                                   headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json',
                                            'Accept': 'application/json', 'Accept-Language': 'en'})
        raw_data = json.loads(get_info.text)
        raw_info = raw_data.get('data')
        raw_title = raw_info.get('seriesName')
    title = sanitize(raw_title)
    get_episodes = get_url_headers('https://api.thetvdb.com/series/' + str(tvdbid) + '/episodes', configfile, dbfile,
                                   headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json',
                                            'Accept': 'application/json', 'Accept-Language': 'de'})
    raw_episode_data = json.loads(get_episodes.text)
    episodes = raw_episode_data.get('data')
    total_pages = raw_episode_data.get('links')
    pages = total_pages.get('last')
    if pages > 1:
        page = 2
        while page <= pages:
            get_episodes = get_url_headers(
                'https://api.thetvdb.com/series/' + str(tvdbid) + '/episodes?page=' + str(page), configfile, dbfile,
                headers={'Authorization': 'Bearer ' + token,
                         'Content-Type': 'application/json',
                         'Accept': 'application/json', 'Accept-Language': 'de'})
            raw_episode_data = json.loads(get_episodes.text)
            more_episodes = raw_episode_data.get('data')
            episodes = episodes + more_episodes
            page += 1
    eps = {}
    for e in episodes:
        season = e.get("airedSeason")
        if season > 0:
            episode = e.get("airedEpisodeNumber")
            current = eps.get(season)
            if current:
                eps[season] = current + [episode]
            else:
                eps[season] = [episode]
    return title, eps


def ombi(configfile, dbfile, device, log_debug):
    db = RssDb(dbfile, 'Ombi')
    config = RssConfig('Ombi', configfile)
    url = config.get('url')
    api = config.get('api')
    mdb_api = config.get('mdb_api')
    tvd_api = config.get('tvd_api')
    tvd_user = config.get('tvd_user')
    tvd_userkey = config.get('tvd_userkey')
    english = RssConfig('RSScrawler', configfile).get('english')

    try:
        if mdb_api:
            requested_movies = requests.get(url + '/api/v1/Request/movie', headers={'ApiKey': api})
            requested_movies = json.loads(requested_movies.text)
        else:
            requested_movies = []
            log_debug("Aufgrund fehlender API-Zugangsdaten werden keine Filme aus Ombi importiert.")
        if tvd_api and tvd_user and tvd_userkey:
            requested_shows = requests.get(url + '/api/v1/Request/tv', headers={'ApiKey': api})
            requested_shows = json.loads(requested_shows.text)
        else:
            requested_shows = []
            log_debug("Aufgrund fehlender API-Zugangsdaten werden keine Serien aus Ombi importiert.")
    except:
        log_debug("Ombi ist nicht erreichbar!")
        return False

    for r in requested_movies:
        if bool(r.get("approved")):
            tmdbid = r.get("theMovieDbId")
            if not db.retrieve('tmdb_' + str(tmdbid)) == 'added':
                title = mdb(configfile, dbfile, tmdbid, mdb_api)
                best_result = search.best_result_mb(title, configfile, dbfile)
                print(u"Film: " + title + u"durch Ombi hinzugefügt.")
                if best_result:
                    search.mb(best_result, device, configfile, dbfile)
                if english:
                    title = r.get('title')
                    best_result = search.best_result_mb(title, configfile, dbfile)
                    print(u"Film: " + title + u"durch Ombi hinzugefügt.")
                    if best_result:
                        search.mb(best_result, device, configfile, dbfile)
                db.store('tmdb_' + str(tmdbid), 'added')

    for r in requested_shows:
        tvdbid = r.get("tvDbId")
        infos = None
        child_request = r.get("childRequests")
        for cr in child_request:
            if bool(cr.get("approved")):
                details = cr.get("seasonRequests")
                for season in details:
                    sn = season.get("seasonNumber")
                    eps = []
                    episodes = season.get("episodes")
                    for episode in episodes:
                        enr = episode.get("episodeNumber")
                        s = str(sn)
                        if len(s) == 1:
                            s = "0" + s
                        s = "S" + s
                        e = str(enr)
                        if len(e) == 1:
                            e = "0" + e
                        se = s + "E" + e
                        if not db.retrieve('tvdb_' + str(tvdbid) + '_' + se) == 'added':
                            eps.append(enr)
                    if eps:
                        if not infos:
                            infos = tvdb(configfile, dbfile, tvdbid, tvd_user, tvd_userkey, tvd_api)
                        title = infos[0]
                        all_eps = infos[1]
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
                                    best_result = search.best_result_sj(title, configfile, dbfile)
                                    if best_result:
                                        add_episode = search.sj(best_result, se, device, configfile, dbfile)
                                        if not add_episode:
                                            add_season = search.sj(best_result, s, device, configfile, dbfile)
                                            for e in eps:
                                                e = str(e)
                                                if len(e) == 1:
                                                    e = "0" + e
                                                se = s + "E" + e
                                                db.store('tvdb_' + str(tvdbid) + '_' + se, 'added')
                                            if not add_season:
                                                log_debug(u"Konnte kein Release für " + title + " " + se + "finden.")
                                            break
                                    db.store('tvdb_' + str(tvdbid) + '_' + se, 'added')
                            else:
                                best_result = search.best_result_sj(title, configfile, dbfile)
                                if best_result:
                                    search.sj(best_result, s, device, configfile, dbfile)
                                for ep in eps:
                                    e = str(ep)
                                    if len(e) == 1:
                                        e = "0" + e
                                    se = s + "E" + e
                                    db.store('tvdb_' + str(tvdbid) + '_' + se, 'added')
                        print(u"Serie/Staffel/Episode: " + title + u"durch Ombi hinzugefügt.")
