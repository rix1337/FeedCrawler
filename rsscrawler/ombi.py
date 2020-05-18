# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import json

import requests

from rsscrawler import search
from rsscrawler.rsscommon import sanitize
from rsscrawler.rsscommon import decode_base64
from rsscrawler.rsscommon import encode_base64
from rsscrawler.rssconfig import RssConfig
from rsscrawler.rssdb import RssDb
from rsscrawler.url import get_url_headers
from rsscrawler.url import post_url_json


def mdb(configfile, dbfile, tmdbid, mdb_api, log_debug):
    get_title = get_url_headers(
        'https://api.themoviedb.org/3/movie/' + str(tmdbid) + '?api_key=' + mdb_api + '&language=de-DE', configfile,
        dbfile, headers={'Content-Type': 'application/json'})[0]
    raw_title = json.loads(get_title.text).get("title")
    if not raw_title:
        get_title = get_url_headers(
            'https://api.themoviedb.org/3/movie/' + str(tmdbid) + '?api_key=' + mdb_api + '&language=en-US', configfile,
            dbfile, headers={'Content-Type': 'application/json'})[0]
        raw_title = json.loads(get_title.text).get("title")
    if raw_title:
        title = sanitize(raw_title)
        return title
    else:
        log_debug("Aufgrund fehlerhafter API-Zugangsdaten werden keine Filme aus Ombi importiert.")
        return False


def get_tvdb_token(configfile, dbfile, tvd_user, tvd_userkey, tvd_api, log_debug):
    db = RssDb(dbfile, 'Ombi')
    response = post_url_json("https://api.thetvdb.com/login", configfile, dbfile, json={
        'username': tvd_user,
        'userkey': tvd_userkey,
        'apikey': tvd_api,
    })
    if response:
        response = json.loads(response)
        token = response.get('token')
        db.delete("tvdb_token")
        db.store("tvdb_token", token)

        if token:
            return token
    else:
        log_debug("Aufgrund fehlerhafter API-Zugangsdaten werden keine Serien aus Ombi importiert.")
        return False


def tvdb(configfile, dbfile, tvdbid, tvd_user, tvd_userkey, tvd_api, log_debug):
    db = RssDb(dbfile, 'Ombi')
    token = db.retrieve('tvdb_token')

    if not token:
        token = get_tvdb_token(configfile, dbfile, tvd_user, tvd_userkey, tvd_api, log_debug)

    if token:
        get_info = get_url_headers('https://api.thetvdb.com/series/' + str(tvdbid), configfile, dbfile,
                                   headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json',
                                            'Accept': 'application/json', 'Accept-Language': 'de'})[0]

        if get_info.status_code == 401:
            token = get_tvdb_token(configfile, dbfile, tvd_user, tvd_userkey, tvd_api, log_debug)
            if token:
                get_info = get_url_headers('https://api.thetvdb.com/series/' + str(tvdbid), configfile, dbfile,
                                           headers={'Authorization': 'Bearer ' + token,
                                                    'Content-Type': 'application/json',
                                                    'Accept': 'application/json', 'Accept-Language': 'de'})[0]
            else:
                return False

        raw_data = json.loads(get_info.text)
        raw_info = raw_data.get('data')
        raw_title = raw_info.get('seriesName')
        if not raw_title:
            get_info = get_url_headers('https://api.thetvdb.com/series/' + str(tvdbid), configfile, dbfile,
                                       headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json',
                                                'Accept': 'application/json', 'Accept-Language': 'en'})[0]
            raw_data = json.loads(get_info.text)
            raw_info = raw_data.get('data')
            raw_title = raw_info.get('seriesName')
        title = sanitize(raw_title)
        get_episodes = get_url_headers('https://api.thetvdb.com/series/' + str(tvdbid) + '/episodes', configfile,
                                       dbfile,
                                       headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json',
                                                'Accept': 'application/json', 'Accept-Language': 'de'})[0]
        raw_episode_data = json.loads(get_episodes.text)
        episodes = raw_episode_data.get('data')
        total_pages = raw_episode_data.get('links')
        if total_pages:
            pages = total_pages.get('last')
            if pages > 1:
                page = 2
                while page <= pages:
                    get_episodes = get_url_headers(
                        'https://api.thetvdb.com/series/' + str(tvdbid) + '/episodes?page=' + str(page), configfile,
                        dbfile,
                        headers={'Authorization': 'Bearer ' + token,
                                 'Content-Type': 'application/json',
                                 'Accept': 'application/json', 'Accept-Language': 'de'})[0]
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
        return title, False
    return False


def ombi(configfile, dbfile, device, log_debug):
    db = RssDb(dbfile, 'Ombi')
    config = RssConfig('Ombi', configfile)
    url = config.get('url')
    api = config.get('api')

    if not url or not api:
        return device

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
            if not bool(r.get("available")):
                tmdbid = r.get("theMovieDbId")
                if not db.retrieve('tmdb_' + str(tmdbid)) == 'added':
                    title = mdb(configfile, dbfile, tmdbid, mdb_api, log_debug)
                    if title:
                        best_result = search.best_result_bl(title, configfile, dbfile)
                        print(u"Film: " + title + u" durch Ombi hinzugefügt.")
                        if best_result:
                            search.download_bl(best_result, device, configfile, dbfile)
                        if english:
                            title = r.get('title')
                            best_result = search.best_result_bl(title, configfile, dbfile)
                            print(u"Film: " + title + u"durch Ombi hinzugefügt.")
                            if best_result:
                                search.download_bl(best_result, device, configfile, dbfile)
                        db.store('tmdb_' + str(tmdbid), 'added')

    for r in requested_shows:
        tvdbid = r.get("tvDbId")
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
                                if not db.retrieve('tvdb_' + str(tvdbid) + '_' + se) == 'added':
                                    eps.append(enr)
                        if eps:
                            if not infos:
                                infos = tvdb(configfile, dbfile, tvdbid, tvd_user, tvd_userkey, tvd_api, log_debug)
                            if infos:
                                title = infos[0]
                                all_eps = infos[1]
                                if all_eps:
                                    check_sn = all_eps.get(sn)
                                else:
                                    check_sn = False
                                if check_sn:
                                    sn_length = len(eps)
                                    check_sn_length = len(check_sn)
                                    if check_sn_length > sn_length:
                                        for ep in eps:
                                            e = str(ep)
                                            if len(e) == 1:
                                                e = "0" + e
                                            se = s + "E" + e
                                            payload = search.best_result_sj(title, configfile, dbfile)
                                            if payload:
                                                payload = decode_base64(payload).split("|")
                                                payload = encode_base64(payload[0] + "|" + payload[1] + "|" + se)
                                                added_episode = search.download_sj(payload, configfile, dbfile)
                                                if not added_episode:
                                                    payload = decode_base64(payload).split("|")
                                                    payload = encode_base64(payload[0] + "|" + payload[1] + "|" + s)
                                                    add_season = search.download_sj(payload, configfile, dbfile)
                                                    for e in eps:
                                                        e = str(e)
                                                        if len(e) == 1:
                                                            e = "0" + e
                                                        se = s + "E" + e
                                                        db.store('tvdb_' + str(tvdbid) + '_' + se, 'added')
                                                    if not add_season:
                                                        log_debug(
                                                            u"Konnte kein Release für " + title + " " + se + "finden.")
                                                    break
                                            db.store('tvdb_' + str(tvdbid) + '_' + se, 'added')
                                    else:
                                        payload = search.best_result_sj(title, configfile, dbfile)
                                        if payload:
                                            payload = decode_base64(payload).split("|")
                                            payload = encode_base64(payload[0] + "|" + payload[1] + "|" + s)
                                            search.download_sj(payload, configfile, dbfile)
                                        for ep in eps:
                                            e = str(ep)
                                            if len(e) == 1:
                                                e = "0" + e
                                            se = s + "E" + e
                                            db.store('tvdb_' + str(tvdbid) + '_' + se, 'added')
                                    print(u"Serie/Staffel/Episode: " + title + u" durch Ombi hinzugefügt.")

    return device
