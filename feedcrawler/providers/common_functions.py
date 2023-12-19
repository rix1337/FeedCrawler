# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt Funktionen zur Verfügung, die in vielen Modulen benötigt werden.

import base64
import datetime
import os
import re
import socket
import sys
from urllib.parse import urlparse

from feedcrawler.providers import gui
from feedcrawler.providers import shared_state
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.sqlite_database import FeedDb
from feedcrawler.providers.sqlite_database import ListDb


class Unbuffered(object):
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def writelines(self, datas):
        self.stream.writelines(datas)
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)


def check_hoster(to_check):
    if to_check:
        to_check = to_check.replace("ddownload", "ddl")
        hosters = CrawlerConfig("Hosters").get_section()
        for hoster in hosters:
            if hosters[hoster] == "True":
                if hoster in to_check.lower() or to_check.lower() in hoster:
                    return True
    return False


def check_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 0))
        ip = s.getsockname()[0]
    except:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def check_is_site(string):
    if not string:
        return False

    hostnames = CrawlerConfig('Hostnames')
    fx = hostnames.get('fx')
    sf = hostnames.get('sf')
    dw = hostnames.get('dw')
    hw = hostnames.get('hw')
    ff = hostnames.get('ff')
    by = hostnames.get('by')
    nk = hostnames.get('nk')
    nx = hostnames.get('nx')
    ww = hostnames.get('ww')
    sj = hostnames.get('sj')
    dj = hostnames.get('dj')
    dd = hostnames.get('dd')

    string = string.lower()

    if fx and fx in string:
        return "FX"
    elif sf and sf in string:
        return "SF"
    elif dw and dw in string:
        return "DW"
    elif hw and hw in string:
        return "HW"
    elif ff and ff in string:
        return "FF"
    elif by and by in string:
        return "BY"
    elif nk and nk in string:
        return "NK"
    elif nx and nx in string:
        return "NX"
    elif ww and ww in string:
        return "WW"
    elif sj and sj in string:
        return "SJ"
    elif dj and dj in string:
        return "DJ"
    elif dd and dd in string:
        return "DD"
    else:
        return False


def check_valid_release(title, retail_only, hevc_retail):
    if retail_only:
        if not is_retail(title, False):
            return False

    if ".German" in title:
        search_title = title.split(".German")[0]
    elif ".GERMAN" in title:
        search_title = title.split(".GERMAN")[0]
    else:
        try:
            quality = re.findall(r"\d{3,4}p", title)[0]
            search_title = title.split(quality)[0]
        except:
            return True

    results = []

    db = FeedDb('FeedCrawler')
    title_with_episodes = re.findall(r'.*\.s\d{1,3}(e\d{1,3}(?!-|E|e\d{1,3}).*\d{1,3})\..*', title, re.IGNORECASE)

    if title_with_episodes:
        episodes_in_title = re.findall(r'E(\d{1,3})', title_with_episodes[0])
        required_episodes = list(range(int(episodes_in_title[0]), int(episodes_in_title[-1]) + 1))

        for episode_in_title in episodes_in_title:
            episode_name = search_title.replace(title_with_episodes[0], "E" + episode_in_title)
            episode_name = re.findall(r'.*\.s\d{1,3}e\d{1,3}(\..*)', episode_name, re.IGNORECASE)
            if episode_name:
                search_title = search_title.replace(episode_name[0], "")
            multiple_search_title = search_title.replace(title_with_episodes[0], "")
            multiple_results = db.retrieve_all_beginning_with(multiple_search_title)
            try:
                for result in multiple_results:
                    episodes = re.findall(r'E(\d{1,3})', result)
                    if episodes:
                        int_episodes = []
                        for ep in episodes:
                            int_episodes.append(int(ep))
                        if len(int_episodes) > 1:
                            sorted_eps = sorted(int_episodes)
                            min_ep = sorted_eps[0]
                            max_ep = sorted_eps[-1]
                            all_episodes = list(range(min_ep, max_ep + 1))
                        else:
                            all_episodes = list(int_episodes)
                        if set(required_episodes).issubset(all_episodes):
                            for ep in all_episodes:
                                if ep == int(episode_in_title):
                                    results = results + [result]
            except:
                print("Fehler in Folgen-Erkennung. Bitte Issue auf GitHub öffnen: " + title)

            season_search_title = search_title.replace(title_with_episodes[0], "") + "."
            season_results = db.retrieve_all_beginning_with(season_search_title)
            results = results + db.retrieve_all_beginning_with(search_title) + season_results
    else:
        db = FeedDb('FeedCrawler')
        results = db.retrieve_all_beginning_with(search_title)

    results = list(set(results))

    if not results:
        return True

    bluray_tags = [".bd-rip.", ".br-rip.", ".bdrip.", "brrip", ".bluray-rip.", ".bluray.", ".bd-disk.", ".bd.", ".bd5.",
                   ".bd9.", ".bd25.", ".bd50."]
    web_tags = [".web.", ".web-rip.", ".webrip.", ".vod-rip.", ".webdl.", ".web-dl.", ".ddc.", ".webhd.", ".web-hd.",
                ".amazonhd.", ".amazonuhd.", ".webuhd.", ".amazonhd.", ".amazonuhd.", ".ituneshd.", ".itunesuhd.",
                ".hbomaxhd.", ".hbomaxuhd."]
    trash_tags = [".cam.", ".cam-rip.", ".ts.", ".telesync.", ".wp.", ".workprint.", ".tc.", ".telecine.", ".vhs-rip.",
                  ".tv-rip.", ".hdtv-rip.", ".hdtv.", ".tvrip.", ".hdtvrip.", ".sat-rip.", ".dvb-rip.", ".ds-rip.",
                  ".scr.", ".screener.", ".dvdscr.", ".dvdscreener.", ".bdscr.", ".r5.", ".dvdrip.", ".dvd."]

    unknown = []
    trash = []
    web = []
    bluray = []
    retail = []

    # Get all previously found Releases and categorize them by their tags
    for r in results:
        if any(s in r.lower() for s in bluray_tags):
            if is_retail(r, False):
                retail.append(r)
            else:
                bluray.append(r)
        elif any(s in r.lower() for s in web_tags):
            web.append(r)
        elif any(s in r.lower() for s in trash_tags):
            trash.append(r)
        else:
            unknown.append(r)

    # Categorize the current Release by its tag to check if a release of the same or better category was already found
    # If no release is in the higher category, propers are allowed anytime
    # If no HEVC is available in the current category or higher and the current release is HEVC, it will be allowed
    if any(s in title.lower() for s in bluray_tags):
        if is_retail(r, False):
            if len(retail) > 0:
                if hevc_retail:
                    if is_hevc(title):
                        no_hevc = True
                        for r in retail:
                            if is_hevc(r):
                                no_hevc = False
                        if no_hevc:
                            return True
                if ".proper" in title.lower():
                    return True
                return False
        else:
            if len(retail) == 0 and len(bluray) > 0:
                if ".proper" in title.lower():
                    return True
            if len(retail) > 0 or len(bluray) > 0:
                if hevc_retail:
                    if is_hevc(title):
                        no_hevc = True
                        for r in retail + bluray:
                            if is_hevc(r):
                                no_hevc = False
                        if no_hevc:
                            return True
                return False
    elif any(s in title.lower() for s in web_tags):
        if len(retail) == 0 and len(bluray) == 0 and len(web) > 0:
            if ".proper" in title.lower():
                return True
        if len(retail) > 0 or len(bluray) > 0 or len(web) > 0:
            if hevc_retail:
                if is_hevc(title):
                    no_hevc = True
                    for r in retail + bluray + web:
                        if is_hevc(r):
                            no_hevc = False
                    if no_hevc:
                        return True
            return False
    elif any(s in title.lower() for s in trash_tags):
        if len(retail) == 0 and len(bluray) == 0 and len(web) == 0 and len(trash) > 0:
            if ".proper" in title.lower():
                return True
        if len(retail) > 0 or len(bluray) > 0 or len(web) > 0 or len(trash) > 0:
            return False
    else:
        if len(retail) == 0 and len(bluray) == 0 and len(web) == 0 and len(trash) == 0 and len(unknown) > 0:
            if ".proper" in title.lower():
                return True
        if len(retail) > 0 or len(bluray) > 0 or len(web) > 0 or len(trash) > 0 or len(unknown) > 0:
            return False

    return True


def check_is_ignored(title, ignore):
    if ignore:
        title = title.replace(" ", ".").lower()
        ignore_list = ignore.replace(" ", ".").lower().split(",")
        for i in ignore_list:
            if not i.startswith("."):
                i = "." + i
            if not i.endswith("."):
                i = i + "."
            if i in title:
                return True
    return False


def decode_base64(value):
    value = value.replace("-", "/")
    return base64.b64decode(value).decode()


def encode_base64(value):
    return base64.b64encode(value.encode("utf-8")).decode().replace("/", "-")


def fullhd_title(key):
    return key.replace("720p", "DL.1080p")


def get_to_decrypt(disabled=False):
    try:
        if disabled:
            to_decrypt = FeedDb('to_decrypt_disabled').retrieve_all_titles_unordered()
        else:
            to_decrypt = FeedDb('to_decrypt').retrieve_all_titles_unordered()

        if to_decrypt:
            hostnames = CrawlerConfig('Hostnames')
            sj = hostnames.get('sj')
            dj = hostnames.get('dj')
            fx = hostnames.get('fx')
            ff = hostnames.get('ff')
            sf = hostnames.get('sf')
            ww = hostnames.get('ww')

            easy_to_decrypt = list(filter(None, [sj, dj]))
            hard_to_decrypt = list(filter(None, [fx, ff, sf, ww]))

            packages = []

            def append_package(packages_to_append_to, package_to_append):
                title = package_to_append[0]
                try:
                    details = package_to_append[1].split('|')
                    url = details[0]
                    password = details[1]
                except:
                    url = package_to_append[1]
                    password = ""

                packages_to_append_to.append({
                    'name': title,
                    'url': url,
                    'password': password
                })
                return packages_to_append_to

            for package in to_decrypt:
                if any(urlparse(package[1]).netloc in td for td in easy_to_decrypt):
                    packages = append_package(packages, package)

            for package in to_decrypt:
                if not any(urlparse(package[1]).netloc in td for td in easy_to_decrypt) and not any(
                        urlparse(package[1]).netloc in td for td in hard_to_decrypt):
                    packages = append_package(packages, package)

            for package in to_decrypt:
                if any(urlparse(package[1]).netloc in td for td in hard_to_decrypt):
                    packages = append_package(packages, package)

            return packages
        else:
            return False
    except:
        return False


def is_hevc(key):
    key = key.lower()
    if "h265" in key or "x265" in key or "hevc" in key:
        return True
    else:
        return False


def is_retail(key, delete):
    retailfinder = re.search(
        r'(|.UNRATED.*|.Unrated.*|.Uncut.*|.UNCUT.*)(|.Directors.Cut.*|.Final.Cut.*|.DC.*|.REMASTERED.*|.EXTENDED.*|.Extended.*|.Theatrical.*|.THEATRICAL.*)(|.3D.*|.3D.HSBS.*|.3D.HOU.*|.HSBS.*|.HOU.*).(German|GERMAN)(|.AC3|.DTS|.DTS-HD)(|.DL)(|.AC3|.DTS|.DTS-HD)(|.NO.SUBS).(2160|1080|720)p.(UHD.|Ultra.HD.|)(HDDVD|BluRay)(|.HDR)(|.AVC|.AVC.REMUX|.x264|.h264|.x265|.h265|.HEVC)(|.REPACK|.RERiP|.REAL.RERiP)-.*',
        key)
    if retailfinder:
        # If this is False, just a retail check is desired
        if delete:
            remove(key)
        return True
    else:
        return False


def is_show(title):
    if re.search(r'S\d{1,3}E\d{1,3}', title, re.IGNORECASE) or re.search(r'S\d{1,3}', title, re.IGNORECASE):
        return True
    else:
        return False


def longest_substr(data):
    substr = ''
    if len(data) > 1 and len(data[0]) > 0:
        for i in range(len(data[0])):
            for j in range(len(data[0]) - i + 1):
                if j > len(substr) and all(data[0][i:i + j] in x for x in data):
                    substr = data[0][i:i + j]
    return substr


def readable_size(size):
    if size:  # integer byte value
        power = 2 ** 10
        n = 0
        powers = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
        while size > power:
            size /= power
            n += 1
        size = round(size, 2)
        size = str(size) + " " + powers[n] + 'B'
        return size
    else:
        return ""


def readable_time(time):
    try:
        if not time:
            time = 0
    except:
        time = 0
    time = str(datetime.timedelta(seconds=int(time)))
    if len(time) == 7:
        time = "0" + time
    return time


def remove(retailtitel):
    try:
        titles = retail_sub(retailtitel)
        retail = titles[0]
        retailyear = titles[1]
        liste = "List_ContentAll_Movies"
        cont = ListDb(liste).retrieve()
        new_cont = []
        if cont:
            for line in cont:
                if line.lower() == retailyear.lower() or line.lower() == retail.lower():
                    line = re.sub(r'^(' + re.escape(retailyear.lower()) + '|' + re.escape(retail.lower()) + ')', '',
                                  line.lower())
                if line:
                    new_cont.append(line)
        ListDb(liste).store_list(new_cont)

        hostnames = CrawlerConfig('Hostnames')
        fx = hostnames.get('fx')
        dw = hostnames.get("dw")
        hw = hostnames.get('hw')
        ff = hostnames.get('ff')
        by = hostnames.get('by')
        nk = hostnames.get('nk')
        nx = hostnames.get('nx')
        ww = hostnames.get('ww')

        fx = fx.replace("f", "F", 1).replace("d", "D", 1).replace("x", "X", 1)
        dw = dw.replace("d", "D", 2).replace("l", "L", 1).replace("w", "W", 1)
        hw = hw.replace("h", "H", 1).replace("d", "D", 1).replace("w", "W", 1)
        ff = ff.replace("f", "F", 2)
        by = by.replace("b", "B", 1)
        nk = nk.replace("n", "N", 1).replace("k", "K", 1)
        try:
            nx = ".".join([nx.split(".")[0].upper(), nx.split(".")[1]])
        except:
            pass
        ww = ww.replace("w", "W", 2)

        bl = ' / '.join(list(filter(None, [fx, dw, hw, ff, by, nk, nx, ww])))

        shared_state.logger.debug('[Retail] - Eintrag "' + retail + '" aus "Filme"-Liste (' + bl + ') entfernt.')
    except:
        print('Fehler beim Entfernen des Eintrages für ' + retailtitel + ' aus der Liste "Filme"!')


def remove_decrypt(title, disabled=False):
    try:
        if disabled:
            db = FeedDb('to_decrypt_disabled')
        else:
            db = FeedDb('to_decrypt')
        all_titles = db.retrieve_all_titles()
        for t in all_titles:
            if t[0].strip() == title.strip():
                db.delete(t[0])
                return True

            try:
                season_in_title = re.findall(r"s(\d{1,3})", t[0], re.IGNORECASE)
                season_package = re.findall(r"s\d{1,3}\.*-\.*s\d{1,3}", title.strip(), re.IGNORECASE)
                if season_in_title and season_package:
                    seasons_in_package = re.findall(r"s(\d{1,3})", season_package[0], re.IGNORECASE)
                    if int(season_in_title[0]) in range(int(seasons_in_package[0]), int(seasons_in_package[1]) + 1):
                        check_title = t[0].strip().lower().split('s' + season_in_title[0])[0]
                        if check_title in title.strip().lower():
                            db.delete(t[0])
                            return True
            except:
                pass
    except:
        pass
    return False


def disable_decrypt(title):
    try:
        all_titles = FeedDb('to_decrypt').retrieve_all_titles()
        for t in all_titles:
            if t[0].strip() == title.strip():
                FeedDb('to_decrypt_disabled').store(t[0], t[1])
                FeedDb('to_decrypt').delete(t[0])
                return True

            try:
                season_in_title = re.findall(r"s(\d{1,3})", t[0], re.IGNORECASE)
                season_package = re.findall(r"s\d{1,3}\.*-\.*s\d{1,3}", title.strip(), re.IGNORECASE)
                if season_in_title and season_package:
                    seasons_in_package = re.findall(r"s(\d{1,3})", season_package[0], re.IGNORECASE)
                    if int(season_in_title[0]) in range(int(seasons_in_package[0]), int(seasons_in_package[1]) + 1):
                        check_title = t[0].strip().lower().split('s' + season_in_title[0])[0]
                        if check_title in title.strip().lower():
                            FeedDb('to_decrypt_disabled').store(t[0], t[1])
                            FeedDb('to_decrypt').delete(t[0])
                            return True
            except:
                pass
    except:
        pass
    return False


def enable_decrypt(title):
    try:
        all_titles = FeedDb('to_decrypt_disabled').retrieve_all_titles()
        for t in all_titles:
            if t[0].strip() == title.strip():
                FeedDb('to_decrypt').store(t[0], t[1])
                FeedDb('to_decrypt_disabled').delete(t[0])
                return True

            try:
                season_in_title = re.findall(r"s(\d{1,3})", t[0], re.IGNORECASE)
                season_package = re.findall(r"s\d{1,3}\.*-\.*s\d{1,3}", title.strip(), re.IGNORECASE)
                if season_in_title and season_package:
                    seasons_in_package = re.findall(r"s(\d{1,3})", season_package[0], re.IGNORECASE)
                    if int(season_in_title[0]) in range(int(seasons_in_package[0]), int(seasons_in_package[1]) + 1):
                        check_title = t[0].strip().lower().split('s' + season_in_title[0])[0]
                        if check_title in title.strip().lower():
                            FeedDb('to_decrypt').store(t[0], t[1])
                            FeedDb('to_decrypt_disabled').delete(t[0])
                            return True
            except:
                pass
    except:
        pass
    return False

def retail_sub(title):
    simplified = title.replace(".", " ")
    retail = re.sub(
        r'(|.UNRATED.*|.Unrated.*|.Uncut.*|.UNCUT.*)(|.Directors.Cut.*|.Final.Cut.*|.DC.*|.REMASTERED.*|.EXTENDED.*|.Extended.*|.Theatrical.*|.THEATRICAL.*)(|.3D.*|.3D.HSBS.*|.3D.HOU.*|.HSBS.*|.HOU.*)(|.)\d{4}(|.)(|.UNRATED.*|.Unrated.*|.Uncut.*|.UNCUT.*)(|.Directors.Cut.*|.Final.Cut.*|.DC.*|.REMASTERED.*|.EXTENDED.*|.Extended.*|.Theatrical.*|.THEATRICAL.*)(|.3D.*|.3D.HSBS.*|.3D.HOU.*|.HSBS.*|.HOU.*).(German|GERMAN)(|.AC3|.DTS|.DTS-HD)(|.DL)(|.AC3|.DTS)(|.NO.SUBS).(2160|1080|720)p.(UHD.|Ultra.HD.|)(HDDVD|BluRay)(|.HDR)(|.AVC|.AVC.REMUX|.x264|.h264|.x265|.h265|.HEVC)(|.REPACK|.RERiP|.REAL.RERiP)-.*',
        "", simplified)
    retailyear = re.sub(
        r'(|.UNRATED.*|.Unrated.*|.Uncut.*|.UNCUT.*)(|.Directors.Cut.*|.Final.Cut.*|.DC.*|.REMASTERED.*|.EXTENDED.*|.Extended.*|.Theatrical.*|.THEATRICAL.*)(|.3D.*|.3D.HSBS.*|.3D.HOU.*|.HSBS.*|.HOU.*).(German|GERMAN)(|.AC3|.DTS|.DTS-HD)(|.DL)(|.AC3|.DTS|.DTS-HD)(|.NO.SUBS).(2160|1080|720)p.(UHD.|Ultra.HD.|)(HDDVD|BluRay)(|.HDR)(|.AVC|.AVC.REMUX|.x264|.h264|.x265|.h265|.HEVC)(|.REPACK|.RERiP|.REAL.RERiP)-.*',
        "", simplified)
    return retail, retailyear


def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)


def configpath(configpath):
    pathfile = "FeedCrawler.conf"
    current_path = os.path.dirname(sys.argv[0])
    if configpath:
        f = open(pathfile, "w")
        f.write(configpath)
        f.close()
    elif os.path.exists(pathfile):
        f = open(pathfile, "r")
        configpath = f.readline()
    else:
        if shared_state.values["gui"]:
            configpath = gui.configpath_gui(current_path)
        else:
            print("Wo sollen Einstellungen und Logs abgelegt werden? Leer lassen, um den aktuellen Pfad zu nutzen.")
            configpath = input("Pfad angeben:")
        if len(configpath) > 0:
            f = open(pathfile, "w")
            f.write(configpath)
            f.close()
    if len(configpath) == 0:
        configpath = current_path
        configpath = configpath.replace("\\", "/")
        configpath = configpath[:-1] if configpath.endswith('/') else configpath
        f = open(pathfile, "w")
        f.write(configpath)
        f.close()
    configpath = configpath.replace("\\", "/")
    configpath = configpath[:-1] if configpath.endswith('/') else configpath
    if not os.path.exists(configpath):
        os.makedirs(configpath)
    return configpath


def site_blocked(url):
    db_status = FeedDb('site_status')
    site = check_is_site(url)
    for check_against in shared_state.values["sites"]:
        if site and check_against == site and db_status.retrieve(check_against + "_normal"):
            return True
    return False


def site_blocked_with_advanced_methods(url):
    db_status = FeedDb('site_status')
    site = check_is_site(url)
    for check_against in shared_state.values["sites"]:
        if site and check_against == site and db_status.retrieve(check_against + "_advanced"):
            return True
    return False


def simplified_search_term_in_title(search_term, release_title, no_numbers=False):
    if no_numbers:
        match_regex = r'[^a-zA-Z\s\-\.]'
    else:
        match_regex = r'[^a-zA-Z0-9\s\-\.]'

    def unify(string):
        return string.lower().replace(" (", "(").replace("ß", "ss").replace("ä", "ae").replace("ö", "oe").replace(
            "ü", "ue").replace(". ", " ").replace("+", ".").replace(" ", ".").replace("-.", "").strip()

    search_term = re.sub(match_regex, '', unify(search_term))
    release_title = re.sub(match_regex, '', unify(release_title))

    return search_term in release_title


def replace_umlauts(string):
    return string.replace("Ä", "Ae").replace("Ö", "Oe").replace("Ü", "Ue"). \
        replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")


def keep_alphanumeric_with_special_characters(string):
    string = replace_umlauts(string)
    return re.sub('[^0-9a-zA-Z\s\-+&]', '', string)


def keep_alphanumeric_with_regex_characters(string):
    string = replace_umlauts(string)
    return re.sub('[^0-9a-zA-Z\s\-.*+()|\[\]?!]', '', string)


def keep_numbers(string):
    return re.sub(r'\D', '', string)
