# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import cloudscraper
import logging
import re
from bs4 import BeautifulSoup
from rapidfuzz import fuzz

from rsscrawler.common import sanitize, is_retail, decode_base64, check_is_site, check_hoster
from rsscrawler.config import RssConfig
from rsscrawler.db import ListDb, RssDb
from rsscrawler.fakefeed import fx_download_links
from rsscrawler.myjd import myjd_download
from rsscrawler.notifiers import notify
from rsscrawler.search.search import get, logger
from rsscrawler.sites.by import BL
from rsscrawler.url import get_url


def best_result_bl(title, configfile, dbfile):
    title = sanitize(title)
    try:
        bl_results = get(title, configfile, dbfile, bl_only=True)[0]
    except:
        return False
    results = []
    i = len(bl_results)

    j = 0
    while i > 0:
        try:
            q = "result" + str(j + 1000)
            results.append(bl_results.get(q).get('title'))
        except:
            pass
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
            best_match = i + 1000
        i += 1
    best_match = 'result' + str(best_match)
    best_result = bl_results.get(best_match)
    if best_result:
        best_title = best_result.get('title')
        if not re.match(r"^" + title.replace(" ", ".") + r".*$", best_title, re.IGNORECASE):
            best_title = False
        best_payload = best_result.get('payload')
    else:
        best_title = None
        best_payload = None
    if not best_title:
        logger.debug(u'Kein Treffer für die Suche nach ' + title + '! Suchliste ergänzt.')
        liste = "MB_Filme"
        cont = ListDb(dbfile, liste).retrieve()
        if not cont:
            cont = ""
        if title not in cont:
            ListDb(dbfile, liste).store(title)
        return False
    if not is_retail(best_title, 1, dbfile):
        logger.debug(u'Kein Retail-Release für die Suche nach ' + title + ' gefunden! Suchliste ergänzt.')
        liste = "MB_Filme"
        cont = ListDb(dbfile, liste).retrieve()
        if not cont:
            cont = ""
        if title not in cont:
            ListDb(dbfile, liste).store(title)
        return best_payload
    else:
        logger.debug('Bester Treffer fuer die Suche nach ' + title + ' ist ' + best_title)
        return best_payload


def download_bl(payload, device, configfile, dbfile):
    hostnames = RssConfig('Hostnames', configfile)
    mb = hostnames.get('mb')
    nk = hostnames.get('nk')
    fc = hostnames.get('fc').replace('www.', '').split('.')[0]

    payload = decode_base64(payload).split("|")
    link = payload[0]
    password = payload[1]
    url = get_url(link, configfile, dbfile)
    if not url or "NinjaFirewall 429" in url:
        return False

    config = RssConfig('MB', configfile)
    db = RssDb(dbfile, 'rsscrawler')
    soup = BeautifulSoup(url, 'lxml')

    site = check_is_site(link, configfile)
    if not site:
        return False
    else:
        if "MB" in site:
            if not fc:
                print(u"FC Hostname nicht gesetzt. MB kann keine Links finden!")
                return False
            key = soup.find("span", {"class": "fn"}).text
            hosters = soup.find_all("a", href=re.compile(fc))
            url_hosters = []
            for hoster in hosters:
                dl = hoster["href"]
                hoster = hoster.text
                url_hosters.append([dl, hoster])
        elif "HW" in site:
            if not fc:
                print(u"FC Hostname nicht gesetzt. MB kann keine Links finden!")
                return False
            key = re.findall(r'Permanent Link: (.*?)"', str(soup)).pop()
            hosters = soup.find_all("a", href=re.compile(fc))
            url_hosters = []
            for hoster in hosters:
                dl = hoster["href"]
                hoster = hoster.text
                url_hosters.append([dl, hoster])
        elif "HS" in site:
            download = soup.find("div", {"class": "entry-content"})
            key = soup.find("h2", {"class": "entry-title"}).text
            url_hosters = re.findall(r'href="([^"\'>]*)".+?(.+?)<', str(download))
        elif "NK" in site:
            key = soup.find("span", {"class": "subtitle"}).text
            url_hosters = []
            hosters = soup.find_all("a", href=re.compile("/go/"))
            for hoster in hosters:
                url_hosters.append(['https://' + nk + hoster["href"], hoster.text])
        elif "FX" in site:
            key = payload[1]
            password = payload[2]
        else:
            return False

        links = {}
        if "MB" in site or "HW" in site or "HS" in site or "NK" in site:
            for url_hoster in reversed(url_hosters):
                try:
                    if mb.split('.')[0] not in url_hoster[0] and "https://goo.gl/" not in url_hoster[0]:
                        link_hoster = url_hoster[1].lower().replace('target="_blank">', '').replace(" ", "-")
                        if check_hoster(link_hoster, configfile):
                            links[link_hoster] = url_hoster[0]
                except:
                    pass
            if config.get("hoster_fallback") and not links:
                for url_hoster in reversed(url_hosters):
                    if mb.split('.')[0] not in url_hoster[0] and "https://goo.gl/" not in url_hoster[0]:
                        link_hoster = url_hoster[1].lower().replace('target="_blank">', '').replace(" ", "-")
                        links[link_hoster] = url_hoster[0]
            download_links = list(links.values())
        elif "FX" in site:
            download_links = fx_download_links(url, key, configfile)

        englisch = False
        if "*englisch" in key.lower() or "*english" in key.lower():
            key = key.replace(
                '*ENGLISCH', '').replace("*Englisch", "").replace("*ENGLISH", "").replace("*English",
                                                                                          "").replace(
                "*", "")
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
                try:
                    search_title = re.findall(
                        r"(.*?)(?:\.(?:(?:19|20)\d{2})|\.German|\.\d{3,4}p|\.S(?:\d{1,3})\.)", key)[0].replace(".", "+")
                    search_url = "http://www.imdb.com/find?q=" + search_title
                    search_page = get_url(search_url, configfile, dbfile)
                    search_results = re.findall(
                        r'<td class="result_text"> <a href="\/title\/(tt[0-9]{7,9})\/\?ref_=fn_al_tt_\d" >(.*?)<\/a>.*? \((\d{4})\)..(.{9})',
                        search_page)
                    total_results = len(search_results)
                except:
                    return False
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
                        logger.debug(
                            "%s - Keine passende Film-IMDB-Seite gefunden" % key)

            if staffel:
                filename = 'MB_Staffeln'
            else:
                filename = 'MB_Filme'

            scraper = cloudscraper.create_scraper()
            blog = BL(configfile, dbfile, device, logging, scraper, filename=filename)

            if not imdb_id:
                if not blog.dual_download(key, password):
                    logger.debug(
                        "%s - Kein zweisprachiges Release gefunden." % key)
            else:
                if isinstance(imdb_id, list):
                    imdb_id = imdb_id.pop()
                imdb_url = "http://www.imdb.com/title/" + imdb_id
                details = get_url(imdb_url, configfile, dbfile)
                if not details:
                    logger.debug("%s - Originalsprache nicht ermittelbar" % key)
                original_language = re.findall(
                    r"Language:<\/h4>\n.*?\n.*?url'>(.*?)<\/a>", details)
                if original_language:
                    original_language = original_language[0]
                if original_language == "German":
                    logger.debug(
                        "%s - Originalsprache ist Deutsch. Breche Suche nach zweisprachigem Release ab!" % key)
                else:
                    if not blog.dual_download(key, password) and not englisch:
                        logger.debug(
                            "%s - Kein zweisprachiges Release gefunden!" % key)

        if download_links:
            if staffel:
                if myjd_download(configfile, dbfile, device, key, "RSScrawler", download_links, password):
                    db.store(
                        key.replace(".COMPLETE", "").replace(".Complete", ""),
                        'notdl' if config.get(
                            'enforcedl') and '.dl.' not in key.lower() else 'added'
                    )
                    log_entry = '[Suche/Staffel] - ' + key.replace(".COMPLETE", "").replace(".Complete",
                                                                                            "") + ' - [' + site + ']'
                    logger.info(log_entry)
                    notify([log_entry], configfile)
                    return True
            elif '.3d.' in key.lower():
                retail = False
                if config.get('cutoff') and '.COMPLETE.' not in key.lower():
                    if config.get('enforcedl'):
                        if is_retail(key, '2', dbfile):
                            retail = True
                if myjd_download(configfile, dbfile, device, key, "RSScrawler/3Dcrawler", download_links, password):
                    db.store(
                        key,
                        'notdl' if config.get(
                            'enforcedl') and '.dl.' not in key.lower() else 'added'
                    )
                    log_entry = '[Suche/Film' + (
                        '/Retail' if retail else "") + '/3D] - ' + key + ' - [' + site + ']'
                    logger.info(log_entry)
                    notify([log_entry], configfile)
                    return True
            else:
                retail = False
                if config.get('cutoff') and '.COMPLETE.' not in key.lower():
                    if config.get('enforcedl'):
                        if is_retail(key, '1', dbfile):
                            retail = True
                    else:
                        if is_retail(key, '0', dbfile):
                            retail = True
                if myjd_download(configfile, dbfile, device, key, "RSScrawler", download_links, password):
                    db.store(
                        key,
                        'notdl' if config.get(
                            'enforcedl') and '.dl.' not in key.lower() else 'added'
                    )
                    log_entry = '[Suche/Film' + ('/Englisch' if englisch and not retail else '') + (
                        '/Englisch/Retail' if englisch and retail else '') + (
                                    '/Retail' if not englisch and retail else '') + '] - ' + key + ' - [' + site + ']'
                    logger.info(log_entry)
                    notify([log_entry], configfile)
                    return [key]
        else:
            return False
