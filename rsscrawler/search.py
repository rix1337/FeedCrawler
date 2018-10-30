# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import json
import logging
import re

import six
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz

try:
    from html.parser import HTMLParser
except ImportError:
    from HTMLParser import HTMLParser

from rsscrawler.common import decode_base64
from rsscrawler.common import sanitize
from rsscrawler.common import cutoff
from rsscrawler.common import myjd_download
from rsscrawler.notifiers import notify
from rsscrawler.rssconfig import RssConfig
from rsscrawler.rssdb import ListDb
from rsscrawler.rssdb import RssDb
from rsscrawler.url import get_url
from rsscrawler.url import post_url
from rsscrawler.sites.bl import BL


def get(title, configfile, dbfile):
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
    config = RssConfig('MB', configfile)
    quality = config.get('quality')
    query = title.replace(".", " ").replace(" ", "+")
    if special:
        mb_query = query + "+" + special
    else:
        mb_query = query
    mb_search = get_url(
        decode_base64('aHR0cDovL21vdmllLWJsb2cudG8=') + '/search/' + mb_query + "+" + quality + '/feed/rss2/',
        configfile, dbfile)
    mb_results = re.findall(r'<title>(.*?)<\/title>\n.*?<link>(.*?)<\/link>', mb_search)

    unrated = []
    for result in mb_results:
        if not result[1].endswith("-MB") and not result[1].endswith(".MB"):
            unrated.append(
                [rate(result[0], configfile), result[1].replace("/", "+"), result[0]])

    if config.get("crawl3d"):
        mb_search = get_url(
            decode_base64('aHR0cDovL21vdmllLWJsb2cudG8=') + '/search/' + mb_query + "+3D+1080p" + '/feed/rss2/',
            configfile, dbfile)
        mb_results = re.findall(r'<title>(.*?)<\/title>\n.*?<link>(.*?)<\/link>', mb_search)
        for result in mb_results:
            if not result[1].endswith("-MB") and not result[1].endswith(".MB"):
                unrated.append(
                    [rate(result[0], configfile), result[1].replace("/", "+"), result[0]])

    rated = sorted(unrated, reverse=True)

    results = {}
    i = 0
    for result in rated:
        res = {"link": result[1], "title": result[2]}
        results["result" + str(i)] = res
        i += 1
    mb_final = results

    sj_search = post_url(decode_base64("aHR0cDovL3Nlcmllbmp1bmtpZXMub3JnL21lZGlhL2FqYXgvc2VhcmNoL3NlYXJjaC5waHA="),
                         configfile,
                         dbfile,
                         data={'string': "'" + query + "'"})
    try:
        sj_results = json.loads(sj_search)
    except:
        sj_results = []

    if special:
        append = " (" + special + ")"
    else:
        append = ""
    i = 0
    results = {}
    for result in sj_results:
        r_title = html_to_str(result[1])
        r_rating = fuzz.ratio(title.lower(), r_title)
        if r_rating > 65:
            res = {"id": result[0], "title": r_title + append, "special": special}
            results["result" + str(i)] = res
            i += 1
    sj_final = results
    return mb_final, sj_final


def rate(title, configfile):
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
        config = RssConfig('SJ', configfile)
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


def best_result_mb(title, configfile, dbfile):
    title = sanitize(title)
    try:
        mb_results = get(title, configfile, dbfile)[0]
    except:
        return False
    conf = RssConfig('MB', configfile)
    ignore = "|".join([r"\.%s(\.|-)" % p for p in conf.get('ignore').lower().split(',')]) if conf.get(
        'ignore') else r"^unmatchable$"
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
    best_result = mb_results.get(best_match)
    if best_result:
        best_title = best_result.get('title')
        best_link = best_result.get('link')
        if re.search(ignore, best_title.lower()):
            best_title = None
        elif not re.search(r'^' + title.replace(" ", ".") + '.(\d{4}|German|\d{3,4}p).*', best_title):
            best_title = None
    else:
        best_title = None
    if not best_title:
        logging.debug(u'Kein Treffer für die Suche nach ' + title + '! Suchliste ergänzt.')
        liste = "MB_Filme"
        cont = ListDb(dbfile, liste).retrieve()
        if not cont:
            cont = ""
        if title not in cont:
            ListDb(dbfile, liste).store(title)
        return False
    if not cutoff(best_title, 1, dbfile):
        logging.debug(u'Kein Retail-Release für die Suche nach ' + title + ' gefunden! Suchliste ergänzt.')
        liste = "MB_Filme"
        cont = ListDb(dbfile, liste).retrieve()
        if not cont:
            cont = ""
        if title not in cont:
            ListDb(dbfile, liste).store(title)
        return best_link
    else:
        logging.debug('Bester Treffer fuer die Suche nach ' + title + ' ist ' + best_title)
        return best_link


def best_result_sj(title, configfile, dbfile):
    try:
        sj_results = get(title, configfile, dbfile)[1]
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
        logging.debug('Kein Treffer fuer die Suche nach ' + title + '! Suchliste ergänzt.')
        listen = ["SJ_Serien", "MB_Staffeln"]
        for liste in listen:
            cont = ListDb(dbfile, liste).retrieve()
            if not cont:
                cont = ""
            if title not in cont:
                ListDb(dbfile, liste).store(title)
            return
    logging.debug('Bester Treffer fuer die Suche nach ' + title + ' ist ' + best_title)
    return best_id


def mb(link, device, configfile, dbfile):
    # TODO myjd_download with device isntead of jdpath
    link = link.replace("+", "/")
    url = get_url(decode_base64("aHR0cDovL21vdmllLWJsb2cub3JnLw==") + link, configfile, dbfile)
    config = RssConfig('MB', configfile)
    hoster = re.compile(config.get('hoster'))
    db = RssDb(dbfile, 'rsscrawler')

    soup = BeautifulSoup(url, 'lxml')
    download = soup.find("div", {"id": "content"})
    key = re.findall(r'Permanent Link: (.*?)"', str(download)).pop()
    url_hosters = re.findall(r'href="([^"\'>]*)".+?(.+?)<', str(download))
    links = {}
    for url_hoster in reversed(url_hosters):
        if not decode_base64("bW92aWUtYmxvZy50by8=") in url_hoster[0] and "https://goo.gl/" not in url_hoster[0]:
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
            search_page = get_url(search_url, configfile, dbfile)
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

        if staffel:
            filename = 'MB_Staffeln'
        else:
            filename = 'MB_Filme'

        bl = BL(configfile, dbfile, device, logging, filename=filename)

        if not imdb_id:
            if not bl.dual_download(key):
                logging.debug(
                    "%s - Kein zweisprachiges Release gefunden." % key)
        else:
            if isinstance(imdb_id, list):
                imdb_id = imdb_id.pop()
            imdb_url = "http://www.imdb.com/title/" + imdb_id
            details = get_url(imdb_url, configfile, dbfile)
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
                if not bl.dual_download(key) and not englisch:
                    logging.debug(
                        "%s - Kein zweisprachiges Release gefunden! Breche ab." % key)

    if download_links:
        notify_array = []
        if staffel:
            myjd_download(
                key,
                key,
                download_links,
                jdownloaderpath + "/folderwatch",
                "RSScrawler",
                configfile
            )
            db.store(
                key.replace(".COMPLETE", "").replace(".Complete", ""),
                'notdl' if config.get(
                    'enforcedl') and '.dl.' not in key.lower() else 'added'
            )
            log_entry = '[Staffel] - ' + key.replace(".COMPLETE", "").replace(".Complete", "")
            logging.info(log_entry)
            notify_array.append(log_entry)
            notify(notify_array, configfile)
            return True
        elif '.3d.' in key.lower():
            retail = False
            if config.get('cutoff') and '.COMPLETE.' not in key.lower():
                if config.get('enforcedl'):
                    if cutoff(key, '2', dbfile):
                        retail = True
            myjd_download(
                key,
                key,
                download_links,
                jdownloaderpath + "/folderwatch",
                "RSScrawler",
                configfile
            )
            db.store(
                key,
                'notdl' if config.get(
                    'enforcedl') and '.dl.' not in key.lower() else 'added'
            )
            log_entry = '[Suche/Film] - <b>' + (
                'Retail/' if retail else "") + '3D</b> - ' + key
            logging.info(log_entry)
            notify_array.append(log_entry)
            notify(notify_array, configfile)
            return True
        else:
            retail = False
            if config.get('cutoff') and '.COMPLETE.' not in key.lower():
                if config.get('enforcedl'):
                    if cutoff(key, '1', dbfile):
                        retail = True
                else:
                    if cutoff(key, '0', dbfile):
                        retail = True
            myjd_download(
                key,
                key,
                download_links,
                jdownloaderpath + "/folderwatch",
                "RSScrawler",
                configfile
            )
            db.store(
                key,
                'notdl' if config.get(
                    'enforcedl') and '.dl.' not in key.lower() else 'added'
            )
            log_entry = '[Suche/Film] - ' + ('<b>Englisch</b> - ' if englisch and not retail else "") + (
                '<b>Englisch/Retail</b> - ' if englisch and retail else "") + (
                            '<b>Retail</b> - ' if not englisch and retail else "") + key
            logging.info(log_entry)
            notify_array.append(log_entry)
            notify(notify_array, configfile)
            return True
    else:
        return False


def sj(sj_id, special, device, configfile, dbfile):
    # TODO myjd_download with device isntead of jdpath
    url = get_url(decode_base64("aHR0cDovL3Nlcmllbmp1bmtpZXMub3JnLz9jYXQ9") + str(sj_id), configfile, dbfile)
    season_pool = re.findall(r'<h2>Staffeln:(.*?)<h2>Feeds', url).pop()
    season_links = re.findall(
        r'href="(.{1,125})">.{1,90}(Staffel|Season).*?(\d{1,2}-?\d{1,2}|\d{1,2})', season_pool)
    title = html_to_str(re.findall(r'>(.{1,85}?) &#', season_pool).pop())

    rsscrawler = RssConfig('RSScrawler', configfile)

    listen = ["SJ_Serien", "MB_Staffeln"]
    for liste in listen:
        cont = ListDb(dbfile, liste).retrieve()
        list_title = sanitize(title)
        if not cont:
            cont = ""
        if not list_title in cont:
            ListDb(dbfile, liste).store(list_title)

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
            sxx = "S0" + str(dl[0])
        else:
            sxx = "S" + str(dl[0])
        link = dl[1]
        if sxx not in found_seasons:
            found_seasons[sxx] = link

    something_found = False

    for sxx, link in found_seasons.items():
        config = RssConfig('SJ', configfile)
        quality = config.get('quality')
        url = get_url(link, configfile, dbfile)
        pakete = re.findall(re.compile(r'<p><strong>(.*?\.' + sxx + r'\..*?' + quality +
                                       r'.*?)<.*?\n.*?href="(.*?)".*? \| (.*)<(?:.*?\n.*?href="(.*?)".*? \| (.*)<|)'),
                            url)
        folgen = re.findall(re.compile(r'<p><strong>(.*?\.' + sxx +
                                       r'E\d{1,3}.*?' + quality + r'.*?)<.*?\n.*?href="(.*?)".*? \| (.*)<(?:.*?\n.*?href="(.*?)".*? \| (.*)<|)'),
                            url)
        lq_pakete = re.findall(re.compile(
            r'<p><strong>(.*?\.' + sxx + r'\..*?)<.*?\n.*?href="(.*?)".*? \| (.*)<(?:.*?\n.*?href="(.*?)".*? \| (.*)<|)'),
            url)
        lq_folgen = re.findall(re.compile(
            r'<p><strong>(.*?\.' + sxx + r'E\d{1,3}.*?)<.*?\n.*?href="(.*?)".*? \| (.*)<(?:.*?\n.*?href="(.*?)".*? \| (.*)<|)'),
            url)

        if not pakete and not folgen and not lq_pakete and not lq_folgen:
            sxx = sxx.replace("S0", "S")
            pakete = re.findall(re.compile(r'<p><strong>(.*?\.' + sxx + r'\..*?' + quality +
                                           r'.*?)<.*?\n.*?href="(.*?)".*? \| (.*)<(?:.*?\n.*?href="(.*?)".*? \| (.*)<|)'),
                                url)
            folgen = re.findall(re.compile(
                r'<p><strong>(.*?\.' + sxx + r'E\d{1,3}.*?' + quality + r'.*?)<.*?\n.*?href="(.*?)".*? \| (.*)<(?:.*?\n.*?href="(.*?)".*? \| (.*)<|)'),
                url)
            lq_pakete = re.findall(re.compile(
                r'<p><strong>(.*?\.' + sxx + r'\..*?)<.*?\n.*?href="(.*?)".*? \| (.*)<(?:.*?\n.*?href="(.*?)".*? \| (.*)<|)'),
                url)
            lq_folgen = re.findall(re.compile(
                r'<p><strong>(.*?\.' + sxx + r'E\d{1,3}.*?)<.*?\n.*?href="(.*?)".*? \| (.*)<(?:.*?\n.*?href="(.*?)".*? \| (.*)<|)'),
                url)

        if special and "e" in special.lower():
            pakete = []
            lq_pakete = []

        best_matching_links = []

        if pakete:
            links = []
            for x in pakete:
                title = x[0]
                score = rate(title, configfile)
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
                score = rate(title, configfile)
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
                score = rate(title, configfile)
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
                score = rate(title, configfile)
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
        for best_link in best_matching_links:
            dl_title = best_link[0].replace(
                "Staffelpack ", "").replace("Staffelpack.", "")
            dl_hoster = best_link[1]
            dl_link = best_link[2]
            config = RssConfig('SJ', configfile)
            hoster = re.compile(config.get('hoster'))
            db = RssDb(dbfile, 'rsscrawler')

            if re.match(hoster, dl_hoster.lower()):
                myjd_download(configfile, device, dl_title, "RSScrawler", dl_link,
                              decode_base64("c2VyaWVuanVua2llcy5vcmc="))
                db.store(dl_title, 'added')
                log_entry = '[Suche/Serie] - ' + dl_title
                logging.info(log_entry)
                notify_array.append(log_entry)
        if len(best_matching_links) > 0:
            something_found = True
        notify(notify_array, configfile)
    if not something_found:
        return False
    return True
