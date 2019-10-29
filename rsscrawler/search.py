# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import html
import json
import logging
import re

from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz

from rsscrawler.common import check_hoster
from rsscrawler.common import cutoff
from rsscrawler.common import decode_base64
from rsscrawler.common import encode_base64
from rsscrawler.common import sanitize
from rsscrawler.fakefeed import ha_search_results
from rsscrawler.myjd import myjd_download
from rsscrawler.notifiers import notify
from rsscrawler.rssconfig import RssConfig
from rsscrawler.rssdb import ListDb
from rsscrawler.rssdb import RssDb
from rsscrawler.sites.bl import BL
from rsscrawler.url import get_url
from rsscrawler.url import post_url


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

    query = title.replace(" ", "+")
    mb_query = sanitize(title).replace(" ", "+")
    if special:
        bl_query = mb_query + "+" + special
    else:
        bl_query = mb_query

    unrated = []

    config = RssConfig('MB', configfile)

    quality = config.get('quality')
    if "480p" not in quality:
        search_quality = "+" + quality
    else:
        search_quality = ""

    mb_search = get_url(
        decode_base64('aHR0cDovL21vdmllLWJsb2cudG8=') + '/search/' + bl_query + "+" + search_quality + '/feed/rss2/',
        configfile, dbfile)
    mb_results = re.findall(r'<title>(.*?)<\/title>\n.*?<link>(.*?)<\/link>', mb_search)
    password = decode_base64("bW92aWUtYmxvZy5vcmc=")
    for result in mb_results:
        if "480p" in quality:
            if "720p" in result[0].lower() or "1080p" in result[0].lower() or "1080i" in result[0].lower() or "2160p" in \
                    result[0].lower() or "complete.bluray" in result[0].lower() or "complete.mbluray" in result[
                0].lower() or "complete.uhd.bluray" in result[0].lower():
                continue
        if not result[0].endswith("-MB") and not result[0].endswith(".MB"):
            unrated.append(
                [rate(result[0], configfile), encode_base64(result[1] + ";" + password), result[0] + " (MB)"])

    hw_search = get_url(
        decode_base64('aHR0cDovL2hkLXdvcmxkLm9yZw==') + '/search/' + bl_query + "+" + search_quality + '/feed/rss2/',
        configfile, dbfile)
    hw_results = re.findall(r'<title>(.*?)<\/title>\n.*?<link>(.*?)<\/link>', hw_search)
    password = decode_base64("aGQtd29ybGQub3Jn")
    for result in hw_results:
        if "480p" in quality:
            if "720p" in result[0].lower() or "1080p" in result[0].lower() or "1080i" in result[0].lower() or "2160p" in \
                    result[0].lower() or "complete.bluray" in result[0].lower() or "complete.mbluray" in result[
                0].lower() or "complete.uhd.bluray" in result[0].lower():
                continue
        unrated.append(
            [rate(result[0], configfile), encode_base64(result[1] + ";" + password), result[0] + " (HW)"])

    ha_search = decode_base64('aHR0cDovL3d3dy5oZC1hcmVhLm9yZy8/cz1zZWFyY2gmcT0=') + bl_query + "&c=" + quality
    ha_results = ha_search_results(ha_search, configfile, dbfile)
    password = decode_base64("aGQtYXJlYS5vcmc=")
    for result in ha_results:
        if "480p" in quality:
            if "720p" in result[0].lower() or "1080p" in result[0].lower() or "1080i" in result[0].lower() or "2160p" in \
                    result[0].lower() or "complete.bluray" in result[0].lower() or "complete.mbluray" in result[
                0].lower() or "complete.uhd.bluray" in result[0].lower():
                continue
        unrated.append(
            [rate(result[0], configfile), encode_base64(result[1] + ";" + password), result[0] + " (HA)"])

    if config.get("crawl3d"):
        mb_search = get_url(
            decode_base64('aHR0cDovL21vdmllLWJsb2cudG8=') + '/search/' + bl_query + "+3D+1080p" + '/feed/rss2/',
            configfile, dbfile)
        mb_results = re.findall(r'<title>(.*?)<\/title>\n.*?<link>(.*?)<\/link>', mb_search)
        for result in mb_results:
            if not result[1].endswith("-MB") and not result[1].endswith(".MB"):
                unrated.append(
                    [rate(result[0], configfile), encode_base64(result[1] + ";" + password), result[0] + " (3D-MB)"])

        hw_search = get_url(
            decode_base64('aHR0cDovL2hkLXdvcmxkLm9yZw==') + '/search/' + bl_query + "+3D+1080p" + '/feed/rss2/',
            configfile, dbfile)
        hw_results = re.findall(r'<title>(.*?)<\/title>\n.*?<link>(.*?)<\/link>', hw_search)
        password = decode_base64("aGQtd29ybGQub3Jn")
        for result in hw_results:
            unrated.append(
                [rate(result[0], configfile), encode_base64(result[1] + ";" + password), result[0] + " (3D-HW)"])

        ha_search = decode_base64('aHR0cDovL3d3dy5oZC1hcmVhLm9yZy8/cz1zZWFyY2gmcT0=') + bl_query + "&c=1080p"
        ha_results = ha_search_results(ha_search, configfile, dbfile)
        password = decode_base64("aGQtYXJlYS5vcmc=")
        for result in ha_results:
            if "3d" in result[0].lower():
                unrated.append(
                    [rate(result[0], configfile), encode_base64(result[1] + ";" + password), result[0] + " (3D-HA)"])

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
    return html.unescape(unescape)


def best_result_bl(title, configfile, dbfile):
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
        r = re.sub(r'\(.*\)', '', r).strip()
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
        quality = conf.get('quality')
        if "480p" not in quality and best_title and not re.search(
                r'^' + title.replace(" ", ".") + r'.(\d{4}|German|\d{3,4}p).*',
                best_title):
            best_title = None
        elif "480p" in quality and best_title and re.search(
                r'^' + title.replace(" ", ".") + r'.(\d{4}|German|\d{3,4}p).*',
                best_title):
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


def download_bl(payload, device, configfile, dbfile):
    payload = decode_base64(payload).split(";")
    link = payload[0]
    password = payload[1]
    url = get_url(link, configfile, dbfile)
    config = RssConfig('MB', configfile)
    db = RssDb(dbfile, 'rsscrawler')

    soup = BeautifulSoup(url, 'lxml')
    download = soup.find("div", {"id": "content"})
    try:
        key = re.findall(r'Permanent Link: (.*?)"', str(download)).pop()
        url_hosters = re.findall(r'href="([^"\'>]*)".+?(.+?)<', str(download))
    except:
        items_head = soup.find("div", {"class": "topbox"})
        key = items_head.contents[1].a["title"]
        items_download = soup.find("div", {"class": "download"})
        url_hosters = []
        download = items_download.find_all("span", {"style": "display:inline;"}, text=True)
        for link in download:
            link = link.a
            text = link.text.strip()
            if text:
                url_hosters.append([str(link["href"]), str(text)])

    links = {}
    for url_hoster in reversed(url_hosters):
        if not decode_base64("bW92aWUtYmxvZy4=") in url_hoster[0] and "https://goo.gl/" not in url_hoster[0]:
            link_hoster = url_hoster[1].lower().replace('target="_blank">', '').replace(" ", "-")
            if check_hoster(link_hoster, configfile):
                links[link_hoster] = url_hoster[0]
    download_links = list(links.values())

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
                try:
                    imdb_id = search_results[0][0]
                except:
                    imdb_id = False
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
            if not bl.dual_download(key, password):
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
                if not bl.dual_download(key, password) and not englisch:
                    logging.debug(
                        "%s - Kein zweisprachiges Release gefunden! Breche ab." % key)

    if download_links:
        if staffel:
            if myjd_download(configfile, dbfile, device, key, "RSScrawler", download_links, password):
                db.store(
                    key.replace(".COMPLETE", "").replace(".Complete", ""),
                    'notdl' if config.get(
                        'enforcedl') and '.dl.' not in key.lower() else 'added'
                )
                log_entry = '[Staffel] - ' + key.replace(".COMPLETE", "").replace(".Complete", "")
                logging.info(log_entry)
                notify([log_entry], configfile)
                return True
        elif '.3d.' in key.lower():
            retail = False
            if config.get('cutoff') and '.COMPLETE.' not in key.lower():
                if config.get('enforcedl'):
                    if cutoff(key, '2', dbfile):
                        retail = True
            if myjd_download(configfile, dbfile, device, key, "RSScrawler/3Dcrawler", download_links, password):
                db.store(
                    key,
                    'notdl' if config.get(
                        'enforcedl') and '.dl.' not in key.lower() else 'added'
                )
                log_entry = '[Suche/Film] - ' + (
                    'Retail/' if retail else "") + '3D - ' + key
                logging.info(log_entry)
                notify([log_entry], configfile)
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
            if myjd_download(configfile, dbfile, device, key, "RSScrawler", download_links, password):
                db.store(
                    key,
                    'notdl' if config.get(
                        'enforcedl') and '.dl.' not in key.lower() else 'added'
                )
                log_entry = '[Suche/Film] - ' + ('Englisch - ' if englisch and not retail else "") + (
                    'Englisch/Retail - ' if englisch and retail else "") + (
                                'Retail - ' if not englisch and retail else "") + key
                logging.info(log_entry)
                notify([log_entry], configfile)
                return True
    else:
        return False


def download_sj(sj_id, special, device, configfile, dbfile):
    url = get_url(decode_base64("aHR0cDovL3Nlcmllbmp1bmtpZXMub3JnLz9jYXQ9") + str(sj_id), configfile, dbfile)
    try:
        season_pool = re.findall(r'<h2>Staffeln:(.*?)<h2>Feeds', url).pop()
    except:
        logging.debug(u'Keine Staffeln gefunden.')
        return False
    season_links = re.findall(
        r'href="(.{1,125})">.{1,90}(Staffel|Season).*?(\d{1,2}-?\d{1,2}|\d{1,2})', season_pool)
    try:
        title = html_to_str(re.findall(r'<title>(.*?) » ', url).pop())
    except:
        logging.debug(u'Kein Serientitel gefunden.')
        return False

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
        if len(dl[0]) == 1:
            sxx = "S0" + str(dl[0])
        else:
            sxx = "S" + str(dl[0])
        link = dl[1]
        if sxx not in found_seasons:
            found_seasons[sxx] = link

    something_found = False
    best_matching_links = []
    sxx_retry = sxx.replace("S0", "S")

    for sxx, link in found_seasons.items():
        config = RssConfig('SJ', configfile)
        quality = config.get('quality')
        url = get_url(link, configfile, dbfile)

        soup = BeautifulSoup(url, 'lxml')

        results = soup.findAll('strong', text=re.compile(r'.*' + sxx + r'.*' + quality + r'.*'))
        if not results:
            results = soup.findAll('strong', text=re.compile(r'.*' + sxx_retry + r'.*' + quality + r'.*'))
        pakete = rated_titles(results, configfile)

        results = soup.findAll('strong', text=re.compile(r'.*' + sxx + r'.*E\d{1,3}.*?' + quality + r'.*'))
        if not results:
            results = soup.findAll('strong',
                                   text=re.compile(r'.*' + sxx_retry + r'E\d{1,3}.*?' + quality + r'.*'))
        folgen = rated_titles(results, configfile)

        results = soup.findAll('strong', text=re.compile(r'.*' + sxx + r'.*'))
        if not results:
            results = soup.findAll('strong', text=re.compile(r'.*' + sxx_retry + r'.*'))
        lq_pakete = rated_titles(results, configfile)

        results = soup.findAll('strong', text=re.compile(r'.*' + sxx + r'.*E\d{1,3}.*?'))
        if not results:
            results = soup.findAll('strong',
                                   text=re.compile(r'.*' + sxx_retry + r'.*E\d{1,3}.*?'))
        lq_folgen = rated_titles(results, configfile)

        if special and "e" in special.lower():
            pakete = []
            lq_pakete = []

        if pakete:
            add = best_links(pakete)
            for a in add:
                best_matching_links.append(a)
        elif folgen:
            add = best_links(folgen)
            for a in add:
                best_matching_links.append(a)
        elif lq_pakete:
            add = best_links(lq_pakete)
            for a in add:
                best_matching_links.append(a)
        elif lq_folgen:
            add = best_links(lq_folgen)
            for a in add:
                best_matching_links.append(a)

        notify_array = []
        for best_link in best_matching_links:
            dl_title = best_link[0]
            dl_link = best_link[1]
            db = RssDb(dbfile, 'rsscrawler')
            if myjd_download(configfile, dbfile, device, dl_title, "RSScrawler", dl_link,
                             decode_base64("c2VyaWVuanVua2llcy5vcmc=")):
                something_found = True
                db.store(dl_title, 'added')
                log_entry = '[Suche/Serie] - ' + dl_title
                logging.info(log_entry)
                notify_array.append(log_entry)
            else:
                return False

        notify(notify_array, configfile)

    if not something_found:
        return False
    return True


def rated_titles(results, configfile):
    to_return = []
    last_link = ""
    if results:
        for r in results:
            title = r.text.replace("Staffelpack ", "").replace("Staffelpack.", "")
            hosters = re.findall(r'<a href="([^"\'>]*)".+?\| (.+?)<', str(r.parent))
            for hoster in hosters:
                if check_hoster(hoster[1], configfile):
                    if hoster[0] not in last_link:
                        last_link = hoster[0]
                        score = rate(title, configfile)
                        to_return.append([score, title, hoster[0]])
    return to_return


def best_links(pakete):
    to_return = []
    highest_score = sorted(pakete, reverse=True)[0][0]
    for p in pakete:
        if p[0] == highest_score:
            to_return.append([p[1], p[2]])
    return to_return
