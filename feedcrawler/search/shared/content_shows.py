# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul durchsucht die Web-Suchen vieler Seiten des Typs content_shows auf Basis einer standardisierten Struktur.

import datetime
import json
import re

from bs4 import BeautifulSoup

from feedcrawler import internal
from feedcrawler.common import decode_base64, sanitize, check_hoster, simplified_search_term_in_title, check_is_site
from feedcrawler.config import CrawlerConfig
from feedcrawler.db import ListDb, FeedDb
from feedcrawler.myjd import add_decrypt
from feedcrawler.notifiers import notify
from feedcrawler.search.search import get, rate
from feedcrawler.url import get_url, get_redirected_url


def get_best_result(title):
    try:
        results = get(title, only_content_shows=True)
        sj_results = results[1]
        sf_results = results[2]
    except:
        return False

    preferred_results = []
    if sf_results:
        internal.logger.debug('SF-Ergebnisse werden für ' + title + ' verwendet!')
        preferred_results = sf_results
    elif sj_results:
        internal.logger.debug('SJ-Ergebnisse werden für ' + title + ' verwendet!')
        preferred_results = sj_results

    best_difference = 999
    best_match = False
    best_payload = False
    for result in preferred_results:
        payload = result.get('payload')
        result = result.get('title')

        len_search_term = len(title)
        len_result = len(result)

        difference = abs(len_search_term - len_result)

        if simplified_search_term_in_title(title, result):
            if difference < best_difference:
                best_difference = difference
                best_match = result
                best_payload = payload

    if not best_match or not best_payload:
        internal.logger.debug('Kein Treffer für die Suche nach ' + title + '! Suchliste ergänzt.')
        listen = ["List_ContentShows_Shows", "List_ContentAll_Seasons"]
        for liste in listen:
            cont = ListDb(liste).retrieve()
            if not cont:
                cont = ""
            if title not in cont:
                ListDb(liste).store(title)
            return False
    internal.logger.debug('Bester Treffer für die Suche nach ' + title + ' ist ' + best_match)
    return best_payload


def download(payload):
    hostnames = CrawlerConfig('Hostnames')
    sj = hostnames.get('sj')
    sf = hostnames.get('sf')

    payload = decode_base64(payload).split("|")
    href = payload[0]
    title = payload[1]
    special = payload[2].strip().replace("None", "")

    special_season = False
    special_episode = False
    if special:
        try:
            special = special.upper()
            special_season = re.findall(r'.*(S\d{1,3})E\d{1,3}.*', special, re.IGNORECASE)[0].upper()
            special_episode = str(int(re.findall(r'.*S\d{1,3}E(\d{1,3}).*', special, re.IGNORECASE)[0]))
        except:
            pass

    site = check_is_site(href)

    real_urls = {}

    if site == "SF":
        password = sf
        series_url = False

        epoch = str(datetime.datetime.now().timestamp()).replace('.', '')[:-3]
        season_page = get_url(href)
        season_id = re.findall(r"initSeason\('(.+?)\',", season_page)[0]

        api_url = 'https://' + sf + '/api/v1/' + season_id + '/season/ALL?lang=ALL&_=' + epoch

        response = get_url(api_url)
        info = json.loads(response)
        content = BeautifulSoup(info['html'], 'html5lib')
        releases = content.findAll("h3")

        unsorted_seasons = {}
        for release in releases:
            season = re.findall(r"(Staffel .*)", release.text.strip())[0].replace("Staffel ", "S")
            details = release.parent.parent.parent

            name = details.find("small").text.strip()
            try:
                resolution = re.findall(r"(\d+p)", name)[0].replace("480p", "SD")
            except:
                resolution = "SD"

            hosters = []
            raw_hosters = details.findAll("span", attrs={'class': None})
            for hoster in raw_hosters:
                hoster = hoster.text.strip()
                if len(hoster) > 2:
                    hosters.append(hoster)

            url = 'https://' + sf + details.find("a")['href']
            demasked_link = get_redirected_url(url)
            if demasked_link:
                url = demasked_link.split("?")[0]

            items = {
                "items": [
                    {
                        "name": name,
                        "resolution": resolution,
                        "hoster": hosters,
                        "url": url,
                    }
                ]}

            if season in unsorted_seasons:
                items = {
                    "items": unsorted_seasons[season]["items"] + items["items"]
                }

            real_urls[name] = url
            unsorted_seasons[season] = items
    else:
        site = "SJ"
        password = sj
        series_url = 'https://' + sj + href
        series_info = get_url(series_url)
        series_id = re.findall(r'data-mediaid="(.*?)"', series_info)[0]
        api_url = 'https://' + sj + '/api/media/' + series_id + '/releases'

        releases = get_url(api_url)
        unsorted_seasons = json.loads(releases)

    listen = ["List_ContentShows_Shows", "List_ContentAll_Seasons"]
    for liste in listen:
        cont = ListDb(liste).retrieve()
        list_title = sanitize(title)
        if not cont:
            cont = ""
        if list_title not in cont:
            ListDb(liste).store(list_title)

    config = CrawlerConfig('ContentShows')
    english_ok = CrawlerConfig('FeedCrawler').get("english")
    quality = config.get('quality').replace("480p", "SD")
    ignore = config.get('rejectlist')

    result_seasons = {}
    result_episodes = {}

    seasons = {}
    for season in unsorted_seasons:
        if "sp" in season.lower():
            seasons[season] = unsorted_seasons[season]
    for season in unsorted_seasons:
        if "sp" not in season.lower():
            seasons[season] = unsorted_seasons[season]

    for season in seasons:
        releases = seasons[season]
        for release in releases['items']:
            name = release['name'].encode('ascii', errors='ignore').decode('utf-8')

            try:
                season = re.findall(r'.*\.(s\d{1,3}).*', name, re.IGNORECASE)[0]
            except:
                pass
            hosters = release['hoster']
            try:
                valid = bool(release['resolution'] == quality)
            except:
                valid = re.match(re.compile(r'.*' + quality + r'.*'), name)
            if valid and special:
                if site == "SF" and special_season and special_episode:
                    if special_season in name:
                        special_url = real_urls[name] + "?episode=" + special_episode
                        name = name.replace("." + special_season + ".", "." + special + ".")
                        real_urls[name] = special_url
                        valid = True
                    else:
                        valid = False
                else:
                    valid = bool("." + special.lower() + "." in name.lower())
            if valid and not english_ok:
                valid = bool(".german." in name.lower())
            if valid:
                valid = False
                for hoster in hosters:
                    if hoster and check_hoster(hoster) or config.get("hoster_fallback"):
                        valid = True
            if valid:
                try:
                    ep = release['episode']
                    if ep:
                        existing = result_episodes.get(season)
                        if existing:
                            valid = False
                            for e in existing:
                                if e == ep:
                                    if rate(name, ignore) > rate(existing[e], ignore):
                                        valid = True
                                else:
                                    valid = True
                            if valid:
                                existing.update({ep: name})
                        else:
                            existing = {ep: name}
                        result_episodes.update({season: existing})
                        continue
                except:
                    pass

                existing = result_seasons.get(season)
                dont = False
                if existing:
                    if rate(name, ignore) < rate(existing, ignore):
                        dont = True
                if not dont:
                    result_seasons.update({season: name})

        try:
            if result_seasons[season] and result_episodes[season]:
                del result_episodes[season]
        except:
            pass

        success = False
        try:
            if result_seasons[season]:
                success = True
        except:
            try:
                if result_episodes[season]:
                    success = True
            except:
                pass

        if success:
            internal.logger.debug(u"Web-Suche erfolgreich für " + title + " - " + season)
        else:
            for release in releases['items']:
                name = release['name'].encode('ascii', errors='ignore').decode('utf-8')
                hosters = release['hoster']
                valid = True
                if valid and special:
                    valid = bool("." + special.lower() + "." in name.lower())
                if valid and not english_ok:
                    valid = bool(".german." in name.lower())
                if valid:
                    valid = False
                    for hoster in hosters:
                        if hoster and check_hoster(hoster) or config.get("hoster_fallback"):
                            valid = True
                if valid:
                    try:
                        ep = release['episode']
                        if ep:
                            existing = result_episodes.get(season)
                            if existing:
                                for e in existing:
                                    if e == ep:
                                        if rate(name, ignore) > rate(existing[e], ignore):
                                            existing.update({ep: name})
                            else:
                                existing = {ep: name}
                            result_episodes.update({season: existing})
                            continue
                    except:
                        pass

                    existing = result_seasons.get(season)
                    dont = False
                    if existing:
                        if rate(name, ignore) < rate(existing, ignore):
                            dont = True
                    if not dont:
                        result_seasons.update({season: name})

            try:
                if result_seasons[season] and result_episodes[season]:
                    del result_episodes[season]
            except:
                pass
            internal.logger.debug(u"Web-Suche erfolgreich für " + title + " - " + season)

    matches = []

    for season in result_seasons:
        matches.append(result_seasons[season])
    for season in result_episodes:
        for episode in result_episodes[season]:
            matches.append(result_episodes[season][episode])

    notify_array = []
    for title in matches:
        db = FeedDb('FeedCrawler')
        if not series_url:
            try:
                url = real_urls[title]
            except:
                url = False
                print("Keine passende URL für " + title + " gefunden. Vermutlich hat SF die Seitenstruktur geändert!")
        else:
            url = series_url

        if url:
            if add_decrypt(title, url, password):
                db.store(title, 'added')
                log_entry = u'[Suche/Serie] - ' + title + ' - ' + site
                internal.logger.info(log_entry)
                notify_array.append(log_entry)

    notify(notify_array)

    if not matches:
        return False
    return matches
