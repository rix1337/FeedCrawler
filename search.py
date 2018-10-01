# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import json
import logging
import os
import re
import sys
try:
    from html.parser import HTMLParser
except ImportError:
    from HTMLParser import HTMLParser

import feedparser
import six
from bs4 import BeautifulSoup as bs
from fuzzywuzzy import fuzz

import common
from common import decode_base64
from notifiers import notify
from rssconfig import RssConfig
from rssdb import ListDb
from rssdb import RssDb
from url import getURL
from url import postURL


def get(title):
    specific_season = re.match(r'^(.*);(s\d{1,3})$', title.lower())
    specific_episode = re.match(r'^(.*);(s\d{1,3}e\d{1,3})$', title.lower())
    if specific_season:
        split = title.split(";")
        title = split[0]
        special = split[1].upper()
    elif specific_episode:
        split = title.split(";")
        title = split[0]
        special = split[1].upper()
    else:
        special = None
    config = RssConfig('MB')
    quality = config.get('quality')
    query = title.replace(".", " ").replace(" ", "+")
    if special:
        mb_query = query + "+" + special
    else:
        mb_query = query
    mb = getURL(
        decode_base64('aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZw==') + '/search/' + mb_query + "+" + quality + '/feed/rss2/')
    mb = re.findall(r'<title>(.*?)<\/title>\n.*?<link>(.*?)<\/link>', mb)

    unrated = []
    for result in mb:
        if not result[1].endswith("-MB") and not result[1].endswith(".MB"):
            unrated.append(
                [rate(result[0]), result[1].replace("/", "+"), result[0]])

    if config.get("crawl3d"):
        mb = getURL(
            decode_base64('aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZw==') + '/search/' + mb_query + "+3D+1080p" + '/feed/rss2/')
        mb = re.findall(r'<title>(.*?)<\/title>\n.*?<link>(.*?)<\/link>', mb)
        for result in mb:
            if not result[1].endswith("-MB") and not result[1].endswith(".MB"):
                unrated.append(
                    [rate(result[0]), result[1].replace("/", "+"), result[0]])

    rated = sorted(unrated, reverse=True)

    results = {}
    i = 0
    for result in rated:
        res = {"link": result[1], "title": result[2]}
        results["result" + str(i)] = res
        i += 1
    mb = results

    sj = postURL(decode_base64("aHR0cDovL3Nlcmllbmp1bmtpZXMub3JnL21lZGlhL2FqYXgvc2VhcmNoL3NlYXJjaC5waHA="),
                 data={'string': "'" + query + "'"})
    try:
        sj = json.loads(sj)
    except:
        sj = []

    if special:
        append = " (" + special + ")"
    else:
        append = ""
    i = 0
    results = {}
    for result in sj:
        r_title = html_to_str(result[1])
        r_rating = fuzz.ratio(title.lower(), r_title)
        if r_rating > 85:
            res = {"id": result[0], "title": r_title + append, "special": special}
            results["result" + str(i)] = res
        i += 1
    if not results:
        i = 0
        for result in sj:
            r_title = html_to_str(result[1])
            r_rating = fuzz.ratio(title.lower(), r_title.lower())
            if r_rating > 65:
                res = {"id": result[0], "title": r_title + append, "special": special}
                results["result" + str(i)] = res
            i += 1
    if not results:
        i = 0
        for result in sj:
            res = {"id": result[0], "title": html_to_str(result[1]) + append, "special": special}
            results["result" + str(i)] = res
            i += 1
    sj = results
    return mb, sj


def rate(title):
    score = 0
    if ".bluray." in title.lower():
        score += 7
    if ".bd." in title.lower():
        score += 7
    if ".bdrip." in title.lower():
        score += 7
    if re.match(r'.*\-(4SJ|TVS)', title):
        score += 4
    if ".dl." in title.lower():
        score += 2
    if re.match(r'.*\.(DTS|DD\+*51|DD\+*71|AC3\.5\.*1)\..*', title):
        score += 2
    if re.match(r'.*\.(720|1080|2160)p\..*', title):
        score += 2
    if ".ml." in title.lower():
        score += 1
    if ".dd20." in title.lower():
        score += 1
    if "dubbed." in title.lower():
        score -= 1
    if ".synced." in title.lower():
        score -= 1
    if ".ac3d." in title.lower():
        score -= 1
    if ".dtsd." in title.lower():
        score -= 1
    if ".hdtv." in title.lower():
        score -= 1
    if ".dtv" in title.lower():
        score -= 1
    if ".pdtv" in title.lower():
        score -= 1
    if "tvrip." in title.lower():
        score -= 1
    if ".subbed." in title.lower():
        score -= 2
    if ".xvid." in title.lower():
        score -= 2
    if ".pal." in title.lower():
        score -= 10
    if "dvd9" in title.lower():
        score -= 10
    try:
        config = RssConfig('SJ')
        reject = config.get("rejectlist").replace(",", "|").lower() if len(
            config.get("rejectlist")) > 0 else r"^unmatchable$"
    except TypeError:
        reject = r"^unmatchable$"
    r = re.search(reject, title.lower())
    if r:
        score -= 5
    if ".subpack." in title.lower():
        score -= 10
    return score


def html_to_str(unescape):
    return HTMLParser().unescape(unescape)


def best_result_mb(title):
    title = title.replace('.', ' ').replace(';', '').replace(',', '').replace(u'Ä', 'Ae').replace(
        u'ä', 'ae').replace(u'Ö', 'Oe').replace(u'ö', 'oe').replace(u'Ü', 'Ue').replace(u'ü', 'ue').replace(u'ß',
                                                                                                            'ss').replace(
        '(', '').replace(')', '').replace('*', '').replace('|', '').replace('\\', '').replace('/', '').replace('?',
                                                                                                               '').replace(
        '!', '').replace(':', '').replace('  ', ' ').replace("'", '')
    try:
        mb_results = get(title)[0]
    except:
        return False
    results = []
    i = len(mb_results)
    j = 0
    while i > 0:
        q = 'result' + str(j)
        results.append(mb_results.get(q).get('title'))
        i -= 1
        j += 1
    best_score = 0
    best_match = 0
    for r in results:
        r = r.replace(".", " ")
        without_year = re.sub(
            r'(|.UNRATED.*|.Unrated.*|.Uncut.*|.UNCUT.*)(|.Directors.Cut.*|.Final.Cut.*|.DC.*|.EXTENDED.*|.Extended.*|.Theatrical.*|.THEATRICAL.*)(|.3D.*|.3D.HSBS.*|.3D.HOU.*|.HSBS.*|.HOU.*)(|.)\d{4}(|.)(|.UNRATED.*|.Unrated.*|.Uncut.*|.UNCUT.*)(|.Directors.Cut.*|.Final.Cut.*|.DC.*|.EXTENDED.*|.Extended.*|.Theatrical.*|.THEATRICAL.*)(|.3D.*|.3D.HSBS.*|.3D.HOU.*|.HSBS.*|.HOU.*).(German|GERMAN)(|.AC3|.DTS|.DTS-HD)(|.DL)(|.AC3|.DTS).(2160|1080|720)p.(UHD.|Ultra.HD.|)(HDDVD|BluRay)(|.HDR)(|.AVC|.AVC.REMUX|.x264|.x265)(|.REPACK|.RERiP|.REAL.RERiP)-.*',
            "", r)
        with_year = re.sub(
            r'(|.UNRATED.*|.Unrated.*|.Uncut.*|.UNCUT.*)(|.Directors.Cut.*|.Final.Cut.*|.DC.*|.EXTENDED.*|.Extended.*|.Theatrical.*|.THEATRICAL.*)(|.3D.*|.3D.HSBS.*|.3D.HOU.*|.HSBS.*|.HOU.*).(German|GERMAN)(|.AC3|.DTS|.DTS-HD)(|.DL)(|.AC3|.DTS|.DTS-HD).(2160|1080|720)p.(UHD.|Ultra.HD.|)(HDDVD|BluRay)(|.HDR)(|.AVC|.AVC.REMUX|.x264|.x265)(|.REPACK|.RERiP|.REAL.RERiP)-.*',
            "", r)
        score = fuzz.ratio(title, without_year) + fuzz.ratio(title, with_year)
        if score > best_score:
            best_score = score
            best_match = i
        i += 1
    best_match = 'result' + str(best_match)
    try:
        best_title = mb_results.get(best_match).get('title')
        best_link = mb_results.get(best_match).get('link')
    except:
        logging.debug('Kein Treffer fuer die Suche nach ' + title + '! Suchliste ergänzt.')
        listen = ["MB_Filme"]
        for liste in listen:
            cont = ListDb(os.path.join(os.path.dirname(
                sys.argv[0]), "RSScrawler.db"), liste).retrieve()
            if not cont:
                cont = ""
            if not title in cont:
                ListDb(os.path.join(os.path.dirname(
                    sys.argv[0]), "RSScrawler.db"), liste).store(title)
        return
    logging.debug('Bester Treffer fuer die Suche nach ' + title + ' ist ' + best_title)
    return best_link


def best_result_sj(title):
    try:
        sj_results = get(title)[1]
    except:
        return False
    results = []
    i = len(sj_results)
    j = 0
    while i > 0:
        q = 'result' + str(j)
        results.append(sj_results.get(q).get('title'))
        i -= 1
        j += 1
    best_score = 0
    best_match = 0
    for r in results:
        score = fuzz.ratio(title, r)
        if score > best_score:
            best_score = score
            best_match = i
        i += 1
    best_match = 'result' + str(best_match)
    try:
        best_title = sj_results.get(best_match).get('title')
        best_id = sj_results.get(best_match).get('id')
    except:
        logging.debug('Kein Treffer fuer die Suche nach ' + title)
        return
    logging.debug('Bester Treffer fuer die Suche nach ' + title + ' ist ' + best_title)
    return best_id


def download_dl(title, jdownloaderpath, hoster, staffel, db, config):
    search_title = \
        title.replace(".German.720p.", ".German.DL.1080p.").replace(".German.DTS.720p.",
                                                                    ".German.DTS.DL.1080p.").replace(
            ".German.AC3.720p.", ".German.AC3.DL.1080p.").replace(
            ".German.AC3LD.720p.", ".German.AC3LD.DL.1080p.").replace(".German.AC3.Dubbed.720p.",
                                                                      ".German.AC3.Dubbed.DL.1080p.").split('.x264-',
                                                                                                            1)[
            0].split('.h264-', 1)[0].replace(".", " ").replace(" ", "+")
    search_url = decode_base64("aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZy9zZWFyY2gv") + search_title + "/feed/rss2/"
    feedsearch_title = \
        title.replace(".German.720p.", ".German.DL.1080p.").replace(".German.DTS.720p.",
                                                                    ".German.DTS.DL.1080p.").replace(
            ".German.AC3.720p.", ".German.AC3.DL.1080p.").replace(
            ".German.AC3LD.720p.", ".German.AC3LD.DL.1080p.").replace(".German.AC3.Dubbed.720p.",
                                                                      ".German.AC3.Dubbed.DL.1080p.").split('.x264-',
                                                                                                            1)[
            0].split('.h264-', 1)[0]
    if not '.dl.' in feedsearch_title.lower():
        logging.debug(
            "%s - Release ignoriert (nicht zweisprachig, da wahrscheinlich nicht Retail)" % feedsearch_title)
        return False
    for (key, value, pattern) in dl_search(feedparser.parse(search_url), feedsearch_title):
        req_page = getURL(value[0])
        soup = bs(req_page, 'lxml')
        download = soup.find("div", {"id": "content"})
        url_hosters = re.findall(r'href="([^"\'>]*)".+?(.+?)<', str(download))
        links = {}
        for url_hoster in reversed(url_hosters):
            if not decode_base64("bW92aWUtYmxvZy5vcmcv") in url_hoster[0] and not "https://goo.gl/" in url_hoster[0]:
                link_hoster = url_hoster[1].lower().replace(
                    'target="_blank">', '')
                if re.match(hoster, link_hoster):
                    links[link_hoster] = url_hoster[0]
        download_links = links.values() if six.PY2 else list(links.values())

        if download_links:
            download_link = download_links[0]
            notify_array = []
            if decode_base64("aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZy8yMDEw") in download_link:
                logging.debug("Fake-Link erkannt!")
                return False
            elif staffel:
                common.write_crawljob_file(
                    key,
                    key,
                    download_links,
                    jdownloaderpath + "/folderwatch",
                    "RSScrawler/Remux"
                )
                db.store(
                    key,
                    'dl' if config.get(
                        'enforcedl') and '.dl.' in key.lower() else 'added'
                )
                log_entry = '[Suche/Staffel] - <b>Zweisprachig</b> - ' + key + ' - <a href="' + download_link + \
                            '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                            key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                logging.info(log_entry)
                notify_array.append(log_entry)
                notify(notify_array)
                return True
            elif '.3d.' in key.lower():
                retail = False
                if config.get('cutoff'):
                    if common.cutoff(key, '2'):
                        retail = True
                common.write_crawljob_file(
                    key,
                    key,
                    download_links,
                    jdownloaderpath + "/folderwatch",
                    "RSScrawler/3Dcrawler"
                )
                db.store(
                    key,
                    'dl' if config.get(
                        'enforcedl') and '.dl.' in key.lower() else 'added'
                )
                log_entry = '[Suche/Film] - <b>' + (
                    'Retail/' if retail else "") + '3D/Zweisprachig</b> - ' + key + ' - <a href="' + download_link + \
                            '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                            key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                logging.info(log_entry)
                notify_array.append(log_entry)
                notify(notify_array)
                return True
            else:
                retail = False
                if config.get('cutoff'):
                    if config.get('enforcedl'):
                        if common.cutoff(key, '1'):
                            retail = True
                    else:
                        if common.cutoff(key, '0'):
                            retail = True
                common.write_crawljob_file(
                    key,
                    key,
                    download_links,
                    jdownloaderpath + "/folderwatch",
                    "RSScrawler/Remux"
                )
                db.store(
                    key,
                    'dl' if config.get(
                        'enforcedl') and '.dl.' in key.lower() else 'added'
                )
                log_entry = '[Suche/Film] - <b>' + (
                    'Retail/' if retail else "") + 'Zweisprachig</b> - ' + key + ' - <a href="' + download_link + \
                            '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                            key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                logging.info(log_entry)
                notify_array.append(log_entry)
                notify(notify_array)
                return True


def dl_search(feed, title):
    s = re.sub(r"[&#\s/]", ".", title).lower()
    for post in feed.entries:
        found = re.search(s, post.title.lower())
        if found:
            yield (post.title, [post.link], title)


def mb(link, jdownloaderpath):
    link = link.replace("+", "/")
    url = getURL(decode_base64("aHR0cDovL21vdmllLWJsb2cub3JnLw==") + link)
    config = RssConfig('MB')
    hoster = re.compile(config.get('hoster'))
    db = RssDb(os.path.join(os.path.dirname(
        sys.argv[0]), "RSScrawler.db"), 'rsscrawler')

    soup = bs(url, 'lxml')
    download = soup.find("div", {"id": "content"})
    key = re.findall(r'Permanent Link: (.*?)"', str(download)).pop()
    url_hosters = re.findall(r'href="([^"\'>]*)".+?(.+?)<', str(download))
    links = {}
    for url_hoster in reversed(url_hosters):
        if not decode_base64("bW92aWUtYmxvZy5vcmcv") in url_hoster[0] and "https://goo.gl/" not in url_hoster[0]:
            link_hoster = url_hoster[1].lower().replace('target="_blank">', '')
            if re.match(hoster, link_hoster):
                links[link_hoster] = url_hoster[0]
    download_links = links.values() if six.PY2 else list(links.values())

    englisch = False
    if "*englisch*" in key.lower():
        key = key.replace('*ENGLISCH*', '').replace("*Englisch*", "")
        englisch = True

    staffel = re.search(r"s\d{1,2}(-s\d{1,2}|-\d{1,2}|\.)", key.lower())

    if config.get('enforcedl') and '.dl.' not in key.lower():
        fail = False
        get_imdb_url = url
        key_regex = r'<title>' + \
                    re.escape(
                        key) + r'.*?<\/title>\n.*?<link>(?:(?:.*?\n){1,25}).*?[mM][kK][vV].*?(?:|href=.?http(?:|s):\/\/(?:|www\.)imdb\.com\/title\/(tt[0-9]{7,9}).*?)[iI][mM][dD][bB].*?(?!\d(?:\.|\,)\d)(?:.|.*?)<\/a>'
        imdb_id = re.findall(key_regex, get_imdb_url)
        if len(imdb_id) > 0:
            if not imdb_id[0]:
                fail = True
            else:
                imdb_id = imdb_id[0]
        else:
            fail = True
        if fail:
            search_title = re.findall(
                r"(.*?)(?:\.(?:(?:19|20)\d{2})|\.German|\.\d{3,4}p|\.S(?:\d{1,3})\.)", key)[0].replace(".", "+")
            search_url = "http://www.imdb.com/find?q=" + search_title
            search_page = getURL(search_url)
            search_results = re.findall(
                r'<td class="result_text"> <a href="\/title\/(tt[0-9]{7,9})\/\?ref_=fn_al_tt_\d" >(.*?)<\/a>.*? \((\d{4})\)..(.{9})',
                search_page)
            total_results = len(search_results)
            if staffel:
                imdb_id = search_results[0][0]
            else:
                no_series = False
                while total_results > 0:
                    attempt = 0
                    for result in search_results:
                        if result[3] == "TV Series":
                            no_series = False
                            total_results -= 1
                            attempt += 1
                        else:
                            no_series = True
                            imdb_id = search_results[attempt][0]
                            total_results = 0
                            break
                if no_series is False:
                    logging.debug(
                        "%s - Keine passende Film-IMDB-Seite gefunden" % key)
        if not imdb_id:
            if not download_dl(key, jdownloaderpath, hoster, staffel, db, config):
                logging.debug(
                    "%s - Kein zweisprachiges Release gefunden." % key)
        else:
            if isinstance(imdb_id, list):
                imdb_id = imdb_id.pop()
            imdb_url = "http://www.imdb.com/title/" + imdb_id
            details = getURL(imdb_url)
            if not details:
                logging.debug("%s - Originalsprache nicht ermittelbar" % key)
            original_language = re.findall(
                r"Language:<\/h4>\n.*?\n.*?url'>(.*?)<\/a>", details)
            if original_language:
                original_language = original_language[0]
            if original_language == "German":
                logging.debug(
                    "%s - Originalsprache ist Deutsch. Breche Suche nach zweisprachigem Release ab!" % key)
            else:
                if not download_dl(key, jdownloaderpath, hoster, staffel, db, config) and not englisch:
                    logging.debug(
                        "%s - Kein zweisprachiges Release gefunden! Breche ab." % key)

    if download_links:
        download_link = download_links[0]
        notify_array = []
        if staffel:
            common.write_crawljob_file(
                key,
                key,
                download_links,
                jdownloaderpath + "/folderwatch",
                "RSScrawler"
            )
            db.store(
                key.replace(".COMPLETE", "").replace(".Complete", ""),
                'notdl' if config.get(
                    'enforcedl') and '.dl.' not in key.lower() else 'added'
            )
            log_entry = '[Staffel] - ' + key.replace(".COMPLETE", "").replace(
                ".Complete",
                "") + ' - <a href="' + download_link + '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                        key.replace(".COMPLETE", "").replace(
                            ".Complete",
                            "") + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
            logging.info(log_entry)
            notify_array.append(log_entry)
            notify(notify_array)
            return True
        elif '.3d.' in key.lower():
            retail = False
            if config.get('cutoff') and '.COMPLETE.' not in key.lower():
                if config.get('enforcedl'):
                    if common.cutoff(key, '2'):
                        retail = True
            common.write_crawljob_file(
                key,
                key,
                download_links,
                jdownloaderpath + "/folderwatch",
                "RSScrawler"
            )
            db.store(
                key,
                'notdl' if config.get(
                    'enforcedl') and '.dl.' not in key.lower() else 'added'
            )
            log_entry = '[Suche/Film] - <b>' + (
                'Retail/' if retail else "") + '3D</b> - ' + key + ' - <a href="' + download_link + '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                        key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
            logging.info(log_entry)
            notify_array.append(log_entry)
            notify(notify_array)
            return True
        else:
            retail = False
            if config.get('cutoff') and '.COMPLETE.' not in key.lower():
                if config.get('enforcedl'):
                    if common.cutoff(key, '1'):
                        retail = True
                else:
                    if common.cutoff(key, '0'):
                        retail = True
            common.write_crawljob_file(
                key,
                key,
                download_links,
                jdownloaderpath + "/folderwatch",
                "RSScrawler"
            )
            db.store(
                key,
                'notdl' if config.get(
                    'enforcedl') and '.dl.' not in key.lower() else 'added'
            )
            log_entry = '[Suche/Film] - ' + ('<b>Englisch</b> - ' if englisch and not retail else "") + (
                '<b>Englisch/Retail</b> - ' if englisch and retail else "") + (
                            '<b>Retail</b> - ' if not englisch and retail else "") + key + ' - <a href="' + download_link + \
                        '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                        key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
            logging.info(log_entry)
            notify_array.append(log_entry)
            notify(notify_array)
            return True
    else:
        return False


def sj(id, special, jdownloaderpath):
    url = getURL(decode_base64("aHR0cDovL3Nlcmllbmp1bmtpZXMub3JnLz9jYXQ9") + str(id))
    season_pool = re.findall(r'<h2>Staffeln:(.*?)<h2>Feeds', url).pop()
    season_links = re.findall(
        r'href="(.{1,125})">.{1,90}(Staffel|Season).*?(\d{1,2}-?\d{1,2}|\d{1,2})', season_pool)
    title = html_to_str(re.findall(r'>(.{1,85}?) &#', season_pool).pop())

    rsscrawler = RssConfig('RSScrawler')

    listen = ["SJ_Serien", "MB_Staffeln"]
    for liste in listen:
        cont = ListDb(os.path.join(os.path.dirname(
            sys.argv[0]), "RSScrawler.db"), liste).retrieve()
        if not cont:
            cont = ""
        if not title in cont:
            ListDb(os.path.join(os.path.dirname(
                sys.argv[0]), "RSScrawler.db"), liste).store(title)

    staffeln = []
    staffel_nr = []
    seasons = []

    for s in season_links:
        if "staffel" in s[1].lower():
            staffeln.append([s[2], s[0]])
            if "-" in s[2]:
                split = s[2].split("-")
                split = range(int(split[0]), int(split[1]) + 1)
                for nr in split:
                    staffel_nr.append(str(nr))
            else:
                staffel_nr.append(s[2])
        else:
            seasons.append([s[2], s[0]])

    if rsscrawler.get("english"):
        for se in seasons:
            if not se[0] in staffel_nr:
                staffeln.append(se)

    to_dl = []
    for s in staffeln:
        if "-" in s[0]:
            split = s[0].split("-")
            split = range(int(split[0]), int(split[1]) + 1)
            for i in split:
                to_dl.append([str(i), s[1]])
        else:
            to_dl.append([s[0], s[1]])

    found_seasons = {}
    for dl in to_dl:
        if len(dl[0]) is 1:
            sXX = "S0" + str(dl[0])
        else:
            sXX = "S" + str(dl[0])
        link = dl[1]
        if sXX not in found_seasons:
            found_seasons[sXX] = link

    something_found = False

    for sXX, link in found_seasons.items():
        config = RssConfig('SJ')
        quality = config.get('quality')
        url = getURL(link)
        pakete = re.findall(re.compile(r'<p><strong>(.*?\.' + sXX + r'\..*?' + quality +
                                       r'.*?)<.*?\n.*?href="(.*?)".*? \| (.*)<(?:.*?\n.*?href="(.*?)".*? \| (.*)<|)'),
                            url)
        folgen = re.findall(re.compile(r'<p><strong>(.*?\.' + sXX +
                                       r'E\d{1,3}.*?' + quality + r'.*?)<.*?\n.*?href="(.*?)".*? \| (.*)<(?:.*?\n.*?href="(.*?)".*? \| (.*)<|)'),
                            url)
        lq_pakete = re.findall(re.compile(
            r'<p><strong>(.*?\.' + sXX + r'\..*?)<.*?\n.*?href="(.*?)".*? \| (.*)<(?:.*?\n.*?href="(.*?)".*? \| (.*)<|)'),
            url)
        lq_folgen = re.findall(re.compile(
            r'<p><strong>(.*?\.' + sXX + r'E\d{1,3}.*?)<.*?\n.*?href="(.*?)".*? \| (.*)<(?:.*?\n.*?href="(.*?)".*? \| (.*)<|)'),
            url)

        if not pakete and not folgen and not lq_pakete and not lq_folgen:
            sXX = sXX.replace("S0", "S")
            pakete = re.findall(re.compile(r'<p><strong>(.*?\.' + sXX + r'\..*?' + quality +
                                           r'.*?)<.*?\n.*?href="(.*?)".*? \| (.*)<(?:.*?\n.*?href="(.*?)".*? \| (.*)<|)'),
                                url)
            folgen = re.findall(re.compile(
                r'<p><strong>(.*?\.' + sXX + r'E\d{1,3}.*?' + quality + r'.*?)<.*?\n.*?href="(.*?)".*? \| (.*)<(?:.*?\n.*?href="(.*?)".*? \| (.*)<|)'),
                url)
            lq_pakete = re.findall(re.compile(
                r'<p><strong>(.*?\.' + sXX + r'\..*?)<.*?\n.*?href="(.*?)".*? \| (.*)<(?:.*?\n.*?href="(.*?)".*? \| (.*)<|)'),
                url)
            lq_folgen = re.findall(re.compile(
                r'<p><strong>(.*?\.' + sXX + r'E\d{1,3}.*?)<.*?\n.*?href="(.*?)".*? \| (.*)<(?:.*?\n.*?href="(.*?)".*? \| (.*)<|)'),
                url)

        if special and "e" in special.lower():
            pakete = []
            lq_pakete = []

        best_matching_links = []

        if pakete:
            links = []
            for x in pakete:
                title = x[0]
                score = rate(title)
                hoster = [[x[2], x[1]], [x[4], x[3]]]
                if special:
                    if special.lower() in title.lower():
                        links.append([score, title, hoster])
                else:
                    links.append([score, title, hoster])
            if links:
                highest_score = sorted(links, reverse=True)[0][0]
                for l in links:
                    if l[0] == highest_score:
                        for hoster in l[2]:
                            best_matching_links.append(
                                [l[1], hoster[0], hoster[1]])
        elif folgen:
            links = []
            for x in folgen:
                title = x[0]
                score = rate(title)
                hoster = [[x[2], x[1]], [x[4], x[3]]]
                if special:
                    if special.lower() in title.lower():
                        links.append([score, title, hoster])
                else:
                    links.append([score, title, hoster])
            if links:
                highest_score = sorted(links, reverse=True)[0][0]
                for l in links:
                    if l[0] == highest_score:
                        for hoster in l[2]:
                            best_matching_links.append(
                                [l[1], hoster[0], hoster[1]])
        elif lq_pakete:
            links = []
            for x in lq_pakete:
                title = x[0]
                score = rate(title)
                hoster = [[x[2], x[1]], [x[4], x[3]]]
                if special:
                    if special.lower() in title.lower():
                        links.append([score, title, hoster])
                else:
                    links.append([score, title, hoster])
            if links:
                highest_score = sorted(links, reverse=True)[0][0]
                for l in links:
                    if l[0] == highest_score:
                        for hoster in l[2]:
                            best_matching_links.append(
                                [l[1], hoster[0], hoster[1]])
        elif lq_folgen:
            links = []
            for x in lq_folgen:
                title = x[0]
                score = rate(title)
                hoster = [[x[2], x[1]], [x[4], x[3]]]
                if special:
                    if special.lower() in title.lower():
                        links.append([score, title, hoster])
                else:
                    links.append([score, title, hoster])
            if links:
                highest_score = sorted(links, reverse=True)[0][0]
                for l in links:
                    if l[0] == highest_score:
                        for hoster in l[2]:
                            best_matching_links.append(
                                [l[1], hoster[0], hoster[1]])

        notify_array = []
        for link in best_matching_links:
            dl_title = link[0].replace(
                "Staffelpack ", "").replace("Staffelpack.", "")
            dl_hoster = link[1]
            dl_link = link[2]
            config = RssConfig('SJ')
            hoster = re.compile(config.get('hoster'))
            db = RssDb(os.path.join(os.path.dirname(
                sys.argv[0]), "RSScrawler.db"), 'rsscrawler')

            if re.match(hoster, dl_hoster.lower()):
                common.write_crawljob_file(
                    dl_title, dl_title, dl_link, jdownloaderpath + "/folderwatch", "RSScrawler")
                db.store(dl_title, 'added')
                log_entry = '[Suche/Serie] - ' + dl_title + ' - <a href="' + dl_link + \
                            '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                            dl_title + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                logging.info(log_entry)
                notify_array.append(log_entry)
        if len(best_matching_links) > 0:
            something_found = True
        notify(notify_array)
    if not something_found:
        return False
    return True
