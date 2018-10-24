# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import json

import requests

from rsscrawler.common import sanitize
from rsscrawler.rssconfig import RssConfig


def ombi(configfile):
    config = RssConfig('Ombi', configfile)
    url = config.get('url')
    api = config.get('url')
    mdb_api = config.get('url')
    tvd_api = config.get('url')
    tvd_user = config.get('url')
    tvd_userkey = config.get('url')

    try:
        requested_movies = requests.get(url + '/api/v1/Request/movie', headers={'ApiKey': api})
        requested_movies = json.loads(requested_movies.text)
        requested_shows = requests.get(url + '/api/v1/Request/tv', headers={'ApiKey': api})
        requested_shows = json.loads(requested_shows.text)
    except:
        print("Ombi nicht erreichbar")
        return

    movies = []
    shows = []

    for r in requested_movies:
        tmdbid = r.get("theMovieDbId")
        title = mdb(tmdbid, mdb_api)
        movies.append(title)

    for r in requested_shows:
        tvdbid = r.get("tvDbId")
        infos = tvdb(tvdbid, tvd_user, tvd_userkey, tvd_api)
        title = infos[0]
        all_eps = infos[1]
        child_request = r.get("childRequests")
        for cr in child_request:
            details = cr.get("seasonRequests")
            for season in details:
                eps = []
                episodes = season.get("episodes")
                for episode in episodes:
                    eps.append(episode.get("episodeNumber"))
                sn = season.get("seasonNumber")
                check_sn = all_eps.get(sn)
                sn_length = len(eps)
                check_sn_length = len(check_sn)
                if check_sn_length > sn_length:
                    for ep in eps:
                        shows.append({title: str(sn) + ',' + str(ep)})
                else:
                    shows.append({title: str(sn)})


def mdb(tmdbid, mdb_api):
    get_title = requests.get(
        'https://api.themoviedb.org/3/movie/' + str(tmdbid) + '?api_key=' + mdb_api + '&language=de-DE',
        headers={'Content-Type': 'application/json'})
    raw_title = json.loads(get_title.text).get("title")
    title = sanitize(raw_title)
    return title


def tvdb(tvdbid, tvd_user, tvd_userkey, tvd_api):
    response = requests.post("https://api.thetvdb.com/login", json={
        'username': tvd_user,
        'userkey': tvd_userkey,
        'apikey': tvd_api,
    })
    response = json.loads(response.text)
    jwttoken = response.get('token')

    get_info = requests.get('https://api.thetvdb.com/series/' + str(tvdbid),
                            headers={'Authorization': 'Bearer ' + jwttoken, 'Content-Type': 'application/json',
                                     'Accept': 'application/json', 'Accept-Language': 'de'})
    raw_data = json.loads(get_info.text)
    raw_info = raw_data.get('data')
    raw_title = raw_info.get('seriesName')
    title = sanitize(raw_title)
    get_episodes = requests.get('https://api.thetvdb.com/series/' + str(tvdbid) + '/episodes',
                                headers={'Authorization': 'Bearer ' + jwttoken, 'Content-Type': 'application/json',
                                         'Accept': 'application/json', 'Accept-Language': 'de'})
    raw_episode_data = json.loads(get_episodes.text)
    episodes = raw_episode_data.get('data')
    total_pages = raw_episode_data.get('links')
    pages = total_pages.get('last')
    if pages > 1:
        page = 2
        while page <= pages:
            get_episodes = requests.get('https://api.thetvdb.com/series/' + str(tvdbid) + '/episodes?page=' + str(page),
                                        headers={'Authorization': 'Bearer ' + jwttoken,
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
