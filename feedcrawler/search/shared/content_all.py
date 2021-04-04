# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337

import re
from bs4 import BeautifulSoup
from rapidfuzz import fuzz

from feedcrawler.common import sanitize, is_retail, decode_base64, check_is_site, check_hoster
from feedcrawler.config import RssConfig
from feedcrawler.db import ListDb, RssDb
from feedcrawler.myjd import myjd_download
from feedcrawler.notifiers import notify
from feedcrawler.search.search import get, logger
from feedcrawler.sites.shared.internal_feed import add_decrypt_instead_of_download
from feedcrawler.sites.shared.internal_feed import fx_get_download_links
from feedcrawler.url import get_redirected_url
from feedcrawler.url import get_url
from feedcrawler.url import get_urls_async


def get_best_result(title, configfile, dbfile):
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
    if not is_retail(best_title, dbfile):
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


def download(payload, device, configfile, dbfile):
    config = RssConfig('MB', configfile)
    db = RssDb(dbfile, 'feedcrawler')
    hostnames = RssConfig('Hostnames', configfile)
    by = hostnames.get('by')
    nk = hostnames.get('nk')

    payload = decode_base64(payload).split("|")
    link = payload[0]
    password = payload[1]

    site = check_is_site(link, configfile)
    if not site:
        return False
    elif "DW" in site:
        download_method = add_decrypt_instead_of_download
        download_links = [link]
        key = payload[1]
        password = payload[2]
    else:
        url = get_url(link, configfile, dbfile)
        if not url or "NinjaFirewall 429" in url:
            return False
        download_method = myjd_download
        soup = BeautifulSoup(url, 'lxml')

        if "BY" in site:
            key = soup.find("small").text
            links = soup.find_all("iframe")
            async_link_results = []
            for link in links:
                link = link["src"]
                if 'https://' + by in link:
                    async_link_results.append(link)
            async_link_results = get_urls_async(async_link_results, configfile, dbfile)
            links = async_link_results[0]
            url_hosters = []
            for link in links:
                if link:
                    link = BeautifulSoup(link, 'lxml').find("a", href=re.compile("/go\.php\?"))
                    if link:
                        url_hosters.append([link["href"], link.text.replace(" ", "")])
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
        if "FX" in site:
            class FX:
                configfile = ""

            FX.configfile = configfile
            download_links = fx_get_download_links(FX, url, key)
        else:
            for url_hoster in reversed(url_hosters):
                try:
                    link_hoster = url_hoster[1].lower().replace('target="_blank">', '').replace(" ", "-").replace(
                        "ddownload", "ddl")
                    if check_hoster(link_hoster, configfile):
                        link = url_hoster[0]
                        if by in link:
                            demasked_link = get_redirected_url(link, configfile, dbfile, False)
                            if demasked_link:
                                link = demasked_link
                        links[link_hoster] = link
                except:
                    pass
            if config.get("hoster_fallback") and not links:
                for url_hoster in reversed(url_hosters):
                    link_hoster = url_hoster[1].lower().replace('target="_blank">', '').replace(" ", "-").replace(
                        "ddownload", "ddl")
                    link = url_hoster[0]
                    if by in link:
                        demasked_link = get_redirected_url(link, configfile, dbfile, False)
                        if demasked_link:
                            link = demasked_link
                    links[link_hoster] = link
            download_links = list(links.values())

    englisch = False
    if "*englisch" in key.lower() or "*english" in key.lower():
        key = key.replace(
            '*ENGLISCH', '').replace("*Englisch", "").replace("*ENGLISH", "").replace("*English",
                                                                                      "").replace(
            "*", "")
        englisch = True

    staffel = re.search(r"s\d{1,2}(-s\d{1,2}|-\d{1,2}|\.)", key.lower())

    if download_links:
        if staffel:
            if download_method(configfile, dbfile, device, key, "FeedCrawler", download_links, password):
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
        else:
            retail = False
            if config.get('cutoff') and '.COMPLETE.' not in key.lower():
                if is_retail(key, dbfile):
                    retail = True
            if download_method(configfile, dbfile, device, key, "FeedCrawler", download_links, password):
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
