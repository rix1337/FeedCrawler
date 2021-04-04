# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337

import json
import re
from rapidfuzz import fuzz

from feedcrawler.common import decode_base64, sanitize, check_hoster, add_decrypt
from feedcrawler.config import CrawlerConfig
from feedcrawler.db import ListDb, FeedDb
from feedcrawler.notifiers import notify
from feedcrawler.search.search import get, logger, rate
from feedcrawler.url import get_url


def get_best_result(title, configfile, dbfile):
    try:
        sj_results = get(title, configfile, dbfile, sj_only=True)[1]
    except:
        return False
    results = []
    i = len(sj_results)

    j = 0
    while i > 0:
        try:
            q = "result" + str(j + 1000)
            results.append(sj_results.get(q).get('title'))
        except:
            pass
        i -= 1
        j += 1
    best_score = 0
    best_match = 0
    for r in results:
        r = re.sub(r"\s\(.*\)", "", r)
        score = fuzz.ratio(title, r)
        if score > best_score:
            best_score = score
            best_match = i + 1000
        i += 1 + 1000
    best_match = 'result' + str(best_match)
    try:
        best_title = sj_results.get(best_match).get('title')
        if not re.match(r"^" + title.replace(" ", ".") + r".*$", best_title, re.IGNORECASE):
            best_title = False
        best_payload = sj_results.get(best_match).get('payload')
    except:
        best_title = False
    if not best_title:
        logger.debug('Kein Treffer fuer die Suche nach ' + title + '! Suchliste ergänzt.')
        listen = ["SJ_Serien", "MB_Staffeln"]
        for liste in listen:
            cont = ListDb(dbfile, liste).retrieve()
            if not cont:
                cont = ""
            if title not in cont:
                ListDb(dbfile, liste).store(title)
            return False
    logger.debug('Bester Treffer fuer die Suche nach ' + title + ' ist ' + best_title)
    return best_payload


def download(payload, configfile, dbfile):
    hostnames = CrawlerConfig('Hostnames', configfile)
    sj = hostnames.get('sj')

    payload = decode_base64(payload).split("|")
    href = payload[0]
    title = payload[1]
    special = payload[2].strip().replace("None", "")

    series_url = 'https://' + sj + href
    series_info = get_url(series_url, configfile, dbfile)
    series_id = re.findall(r'data-mediaid="(.*?)"', series_info)[0]

    api_url = 'https://' + sj + '/api/media/' + series_id + '/releases'
    releases = get_url(api_url, configfile, dbfile)

    unsorted_seasons = json.loads(releases)

    listen = ["SJ_Serien", "MB_Staffeln"]
    for liste in listen:
        cont = ListDb(dbfile, liste).retrieve()
        list_title = sanitize(title)
        if not cont:
            cont = ""
        if list_title not in cont:
            ListDb(dbfile, liste).store(list_title)

    config = CrawlerConfig('SJ', configfile)
    english_ok = CrawlerConfig('FeedCrawler', configfile).get("english")
    quality = config.get('quality')
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
                valid = bool("." + special.lower() + "." in name.lower())
            if valid and not english_ok:
                valid = bool(".german." in name.lower())
            if valid:
                valid = False
                for hoster in hosters:
                    if hoster and check_hoster(hoster, configfile) or config.get("hoster_fallback"):
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
            logger.debug(u"Websuche erfolgreich für " + title + " - " + season)
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
                        if hoster and check_hoster(hoster, configfile) or config.get("hoster_fallback"):
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
            logger.debug(u"Websuche erfolgreich für " + title + " - " + season)

    matches = []

    for season in result_seasons:
        matches.append(result_seasons[season])
    for season in result_episodes:
        for episode in result_episodes[season]:
            matches.append(result_episodes[season][episode])

    notify_array = []
    for title in matches:
        db = FeedDb(dbfile, 'feedcrawler')
        if add_decrypt(title, series_url, sj, dbfile):
            db.store(title, 'added')
            log_entry = u'[Suche/Serie] - ' + title + ' - [SJ]'
            logger.info(log_entry)
            notify_array.append(log_entry)

    notify(notify_array, configfile)

    if not matches:
        return False
    return matches
