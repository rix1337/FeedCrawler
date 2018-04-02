# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import common
from notifiers import notify
from rssconfig import RssConfig
from rssdb import RssDb
from url import getURL
from url import postURL

from bs4 import BeautifulSoup as bs
from HTMLParser import HTMLParser
import feedparser
import json
import logging
import re
import os
import sys
import time
import StringIO


def get(title):
    config = RssConfig('MB')
    quality = config.get('quality')
    query = title.replace(".", " ").replace(" ", "+")
    mb = getURL('aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZw=='.decode(
        'base64') + '/search/' + query + "+" + quality + '/feed/rss2/')
    mb = re.findall(r'<title>(.*?)<\/title>\n.*?<link>(.*?)<\/link>', mb)

    unrated = []
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

    results = {}
    i = 0
    sj = postURL("aHR0cDovL3Nlcmllbmp1bmtpZXMub3JnL21lZGlhL2FqYXgvc2VhcmNoL3NlYXJjaC5waHA=".decode(
        'base64'), data={'string': "'" + query + "'"})
    try:
        sj = json.loads(sj)
    except:
        sj = []
    for result in sj:
        res = {"id": result[0], "title": html_to_str(result[1])}
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


def download_dl(title, jdownloaderpath, hoster, staffel, db, config):
    search_title = title.replace(".German.720p.", ".German.DL.1080p.").replace(".German.DTS.720p.", ".German.DTS.DL.1080p.").replace(".German.AC3.720p.", ".German.AC3.DL.1080p.").replace(
        ".German.AC3LD.720p.", ".German.AC3LD.DL.1080p.").replace(".German.AC3.Dubbed.720p.", ".German.AC3.Dubbed.DL.1080p.").split('.x264-', 1)[0].split('.h264-', 1)[0].replace(".", " ").replace(" ", "+")
    search_url = "aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZy9zZWFyY2gv".decode(
        'base64') + search_title + "/feed/rss2/"
    feedsearch_title = title.replace(".German.720p.", ".German.DL.1080p.").replace(".German.DTS.720p.", ".German.DTS.DL.1080p.").replace(".German.AC3.720p.", ".German.AC3.DL.1080p.").replace(
        ".German.AC3LD.720p.", ".German.AC3LD.DL.1080p.").replace(".German.AC3.Dubbed.720p.", ".German.AC3.Dubbed.DL.1080p.").split('.x264-', 1)[0].split('.h264-', 1)[0]
    if not '.dl.' in feedsearch_title.lower():
        logging.debug(
            "%s - Release ignoriert (nicht zweisprachig, da wahrscheinlich nicht Retail)" % feedsearch_title)
        return False
    for (key, value, pattern) in dl_search(feedparser.parse(search_url), feedsearch_title):
        download_link = False
        req_page = getURL(value[0])
        soup = bs(req_page, 'lxml')
        download = soup.find("div", {"id": "content"})
        url_hosters = re.findall(r'href="([^"\'>]*)".+?(.+?)<', str(download))
        for url_hoster in url_hosters:
            if not "bW92aWUtYmxvZy5vcmcv".decode("base64") in url_hoster[0]:
                if hoster.lower() in url_hoster[1].lower():
                    download_link = url_hoster[0]

        if download_link:
            notify_array = []
            if "aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZy8yMDEw".decode("base64") in download_link:
                logging.debug("Fake-Link erkannt!")
                return False
            elif staffel:
                common.write_crawljob_file(
                    key,
                    key,
                    download_link,
                    jdownloaderpath + "/folderwatch",
                    "RSScrawler/Remux"
                )
                db.store(
                    key,
                    'dl' if config.get(
                        'enforcedl') and '.dl.' in key.lower() else 'added'
                )
                log_entry = '[Staffel] - <b>Zweisprachig</b> - ' + key + ' - <a href="' + download_link + \
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
                    download_link,
                    jdownloaderpath + "/folderwatch",
                    "RSScrawler/3Dcrawler"
                )
                db.store(
                    key,
                    'dl' if config.get(
                        'enforcedl') and '.dl.' in key.lower() else 'added'
                )
                log_entry = '[Film] - <b>' + ('Retail/' if retail else "") + '3D/Zweisprachig</b> - ' + key + ' - <a href="' + download_link + \
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
                    download_link,
                    jdownloaderpath + "/folderwatch",
                    "RSScrawler/Remux"
                )
                db.store(
                    key,
                    'dl' if config.get(
                        'enforcedl') and '.dl.' in key.lower() else 'added'
                )
                log_entry = '[Film] - <b>' + ('Retail/' if retail else "") + 'Zweisprachig</b> - ' + key + ' - <a href="' + download_link + \
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
    url = getURL("aHR0cDovL21vdmllLWJsb2cub3JnLw==".decode('base64') + link)
    rsscrawler = RssConfig('RSScrawler')
    config = RssConfig('MB')
    hoster = rsscrawler.get('hoster')
    db = RssDb(os.path.join(os.path.dirname(
        sys.argv[0]), "Einstellungen/Downloads/Downloads.db"))

    soup = bs(url, 'lxml')
    download = soup.find("div", {"id": "content"})
    key = re.findall(r'Permanent Link: (.*?)"', str(download)).pop()
    url_hosters = re.findall(r'href="([^"\'>]*)".+?(.+?)<', str(download))
    download_link = ""
    for url_hoster in url_hosters:
        if not "bW92aWUtYmxvZy5vcmcv".decode("base64") in url_hoster[0]:
            if hoster.lower() in url_hoster[1].lower():
                download_link = url_hoster[0]

    englisch = False
    if "*englisch*" in key.lower():
        key = key.replace('*ENGLISCH*', '').replace("*Englisch*", "")
        englisch = True

    staffel = re.search(r"s\d{1,2}(-s\d{1,2}|-\d{1,2}|\.)", key.lower())

    if config.get('enforcedl') and '.dl.' not in key.lower():
        original_language = ""
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
                r'<td class="result_text"> <a href="\/title\/(tt[0-9]{7,9})\/\?ref_=fn_al_tt_\d" >(.*?)<\/a>.*? \((\d{4})\)..(.{9})', search_page)
            total_results = len(search_results)
            if total_results == 0:
                download_imdb = ""
            elif staffel:
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

    if download_link:
        notify_array = []
        if staffel:
            common.write_crawljob_file(
                key,
                key,
                download_link,
                jdownloaderpath + "/folderwatch",
                "RSScrawler"
            )
            db.store(
                key.replace(".COMPLETE", "").replace(".Complete", ""),
                'notdl' if config.get(
                    'enforcedl') and '.dl.' not in key.lower() else 'added'
            )
            log_entry = '[Suche/Staffel] - ' + key.replace(
                ".COMPLETE.", ".") + ' - [<a href="' + download_link + '" target="_blank">Link</a>]'
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
                download_link,
                jdownloaderpath + "/folderwatch",
                "RSScrawler"
            )
            db.store(
                key,
                'notdl' if config.get(
                    'enforcedl') and '.dl.' not in key.lower() else 'added'
            )
            log_entry = '[Suche/Film] - <b>' + ('Retail/' if retail else "") + '3D</b> - ' + key + ' - <a href="' + download_link + '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
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
                download_link,
                jdownloaderpath + "/folderwatch",
                "RSScrawler"
            )
            db.store(
                key,
                'notdl' if config.get(
                    'enforcedl') and '.dl.' not in key.lower() else 'added'
            )
            log_entry = '[Suche/Film] - ' + ('<b>Englisch</b> - ' if englisch and not retail else "") + ('<b>Englisch/Retail</b> - ' if englisch and retail else "") + ('<b>Retail</b> - ' if not englisch and retail else "") + key + ' - <a href="' + download_link + \
                '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
            logging.info(log_entry)
            notify_array.append(log_entry)
            notify(notify_array)
            return True
    else:
        return False


def sj(id, jdownloaderpath):
    url = getURL("aHR0cDovL3Nlcmllbmp1bmtpZXMub3JnLz9jYXQ9".decode(
        'base64') + str(id))
    season_pool = re.findall(r'<h2>Staffeln:(.*?)<h2>Feeds', url).pop()
    season_links = re.findall(
        r'href="(.{1,125})">.{1,90}(Staffel|Season).*?(\d{1,2}-?\d{1,2}|\d{1,2})', season_pool)
    title = html_to_str(re.findall(r'>(.{1,90}?) &#', season_pool).pop())

    rsscrawler = RssConfig('RSScrawler')

    if os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/SJ_Serien.txt')):
        file = open(os.path.join(os.path.dirname(
            sys.argv[0]), 'Einstellungen/Listen/SJ_Serien.txt'))
        output = StringIO.StringIO()
        for line in file.readlines():
            output.write(line.replace("XXXXXXXXXX", ""))
    liste = output.getvalue()
    if not title in liste:
        with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/SJ_Serien.txt'), 'wb') as f:
            liste = liste + "\n" + title
            f.write(liste.encode('utf-8'))

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

    for sXX, link in found_seasons.items():
        config = RssConfig('SJ')
        quality = config.get('quality')
        url = getURL(link)
        pakete = re.findall(re.compile(r'<p><strong>(.*?\.' + sXX + r'\..*?' + quality +
                                       r'.*?)<.*?\n.*?href="(.*?)".*? \| (.*)<(?:.*?\n.*?href="(.*?)".*? \| (.*)<|)'), url)
        folgen = re.findall(re.compile(r'<p><strong>(.*?\.' + sXX +
                                       r'E\d{1,3}.*?' + quality + r'.*?)<.*?\n.*?href="(.*?)".*? \| (.*)<(?:.*?\n.*?href="(.*?)".*? \| (.*)<|)'), url)
        lq_pakete = re.findall(re.compile(
            r'<p><strong>(.*?\.' + sXX + r'\..*?)<.*?\n.*?href="(.*?)".*? \| (.*)<(?:.*?\n.*?href="(.*?)".*? \| (.*)<|)'), url)
        lq_folgen = re.findall(re.compile(
            r'<p><strong>(.*?\.' + sXX + r'E\d{1,3}.*?)<.*?\n.*?href="(.*?)".*? \| (.*)<(?:.*?\n.*?href="(.*?)".*? \| (.*)<|)'), url)

        if not pakete and not folgen and not lq_pakete and not lq_folgen:
            sXX = sXX.replace("S0", "S")
            pakete = re.findall(re.compile(r'<p><strong>(.*?\.' + sXX + r'\..*?' + quality +
                                           r'.*?)<.*?\n.*?href="(.*?)".*? \| (.*)<(?:.*?\n.*?href="(.*?)".*? \| (.*)<|)'), url)
            folgen = re.findall(re.compile(
                r'<p><strong>(.*?\.' + sXX + r'E\d{1,3}.*?' + quality + r'.*?)<.*?\n.*?href="(.*?)".*? \| (.*)<(?:.*?\n.*?href="(.*?)".*? \| (.*)<|)'), url)
            lq_pakete = re.findall(re.compile(
                r'<p><strong>(.*?\.' + sXX + r'\..*?)<.*?\n.*?href="(.*?)".*? \| (.*)<(?:.*?\n.*?href="(.*?)".*? \| (.*)<|)'), url)
            lq_folgen = re.findall(re.compile(
                r'<p><strong>(.*?\.' + sXX + r'E\d{1,3}.*?)<.*?\n.*?href="(.*?)".*? \| (.*)<(?:.*?\n.*?href="(.*?)".*? \| (.*)<|)'), url)

        best_matching_links = []

        if pakete:
            links = []
            for x in pakete:
                title = x[0]
                score = rate(title)
                hoster = [[x[2], x[1]], [x[4], x[3]]]
                links.append([score, title, hoster])
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
                links.append([score, title, hoster])
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
                links.append([score, title, hoster])
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
                links.append([score, title, hoster])
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
            rsscrawler = RssConfig('RSScrawler')
            hoster = rsscrawler.get('hoster')
            db = RssDb(os.path.join(os.path.dirname(
                sys.argv[0]), "Einstellungen/Downloads/Downloads.db"))

            if hoster.lower() in dl_hoster.lower():
                common.write_crawljob_file(
                    dl_title, dl_title, dl_link, jdownloaderpath + "/folderwatch", "RSScrawler")
                db.store(dl_title, 'added')
                log_entry = '[Suche/Serie] - ' + dl_title + ' - <a href="' + dl_link + \
                    '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + \
                    dl_title + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                logging.info(log_entry)
                notify_array.append(log_entry)
        notify(notify_array)
    return True
