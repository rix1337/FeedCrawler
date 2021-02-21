# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import feedparser
import hashlib
import re
from bs4 import BeautifulSoup

from rsscrawler.common import check_valid_release
from rsscrawler.common import fullhd_title
from rsscrawler.common import is_hevc
from rsscrawler.common import is_retail
from rsscrawler.db import ListDb
from rsscrawler.imdb import get_imdb_id
from rsscrawler.imdb import get_original_language
from rsscrawler.notifiers import notify
from rsscrawler.url import check_is_site
from rsscrawler.url import get_url


def get_movies_list(self, liste):
    cont = ListDb(self.dbfile, liste).retrieve()
    titles = []
    if cont:
        for title in cont:
            if title:
                title = title.replace(" ", ".")
                titles.append(title)
    return titles


def settings_hash(self, refresh):
    if refresh:
        settings = ["quality", "search", "ignore", "regex", "cutoff", "enforcedl", "crawlseasons", "seasonsquality",
                    "seasonpacks", "seasonssource", "imdbyear", "imdb", "hevc_retail", "retail_only", "hoster_fallback"]
        self.settings = []
        self.settings.append(self.rsscrawler.get("english"))
        self.settings.append(self.rsscrawler.get("surround"))
        self.settings.append(self.hosters)
        for s in settings:
            self.settings.append(self.config.get(s))
        if self.filename == "IMDB":
            self.pattern = self.filename
        else:
            liste = get_movies_list(self, self.filename)
            self.pattern = r'(' + "|".join(liste).lower() + ').*'
    settings = str(self.settings) + str(self.pattern)
    return hashlib.sha256(settings.encode('ascii', 'ignore')).hexdigest()


def adhoc_search(self, feed, title):
    ignore = "|".join(
        [r"\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if self.config.get(
        "ignore") else r"^unmatchable$"

    s = re.sub(self.SUBSTITUTE, "../..", title).lower()
    for post in feed.entries:
        found = re.search(s, post.title.lower())
        if found:
            try:
                content = post.content[0].value
            except:
                self.log_debug("Fehler beim Abruf von " + post.title + ": Kein Durchsuchbarer Inhalt gefunden.")
                content = False
            if content:
                found = re.search(ignore, post.title.lower())
                if found:
                    if self.hevc_retail:
                        if is_hevc(post.title) and "1080p" in post.title:
                            if is_retail(post.title, False):
                                self.log_debug(
                                    "%s - Release ist 1080p-HEVC-Retail" % post.title)
                                found = False
                if found:
                    self.log_debug(
                        "%s - Release ignoriert (basierend auf ignore-Einstellung)" % post.title)
                    continue
                yield post.title, content


def search_imdb(self, imdb, feed):
    added_items = []
    settings = str(self.settings)
    score = str(self.imdb)
    for post in feed.entries:
        try:
            content = post.content[0].value
        except:
            self.log_debug("Fehler beim Abruf von " + post.title + ": Kein Durchsuchbarer Inhalt gefunden.")
            content = False
        if content:
            post.title = post.title.strip(u'\u200b')

        if self.search_imdb_done:
            self.log_debug(
                self._SITE + "-Feed ab hier bereits gecrawlt (" + post.title + ") - breche " + self._SITE + "-Suche ab!")
            return added_items

        concat = post.title + post.published + settings + score
        sha = hashlib.sha256(concat.encode(
            'ascii', 'ignore')).hexdigest()
        if sha == self.last_sha:
            self.search_imdb_done = True

        if content:
            if "mkv" in content.lower():
                post_imdb = re.findall(
                    r'.*?(?:href=.?http(?:|s):\/\/(?:|www\.)imdb\.com\/title\/(tt[0-9]{7,9}).*?).*?(\d(?:\.|\,)\d)(?:.|.*?)<\/a>.*?',
                    content)

                hevc_retail = False
                if post_imdb:
                    post_imdb = post_imdb.pop()
                storage = self.db.retrieve_all(post.title)
                storage_replaced = self.db.retrieve_all(
                    post.title.replace(".COMPLETE", "").replace(".Complete", ""))
                if 'added' in storage or 'notdl' in storage or 'added' in storage_replaced or 'notdl' in storage_replaced:
                    self.log_debug(
                        "%s - Release ignoriert (bereits gefunden)" % post.title)
                    continue
                elif not check_valid_release(post.title, self.retail_only, self.hevc_retail, self.dbfile):
                    self.log_debug(
                        "%s - Release ignoriert (Gleiche oder bessere Quelle bereits vorhanden)" % post.title)
                    continue
                quality_set = self.config.get('quality')
                if '.3d.' in post.title.lower():
                    self.log_debug(
                        "%s - Release ignoriert (3D-Film)" % post.title)
                    return
                else:
                    if quality_set == "480p":
                        if "720p" in post.title.lower() or "1080p" in post.title.lower() or "1080i" in post.title.lower() or "2160p" in post.title.lower():
                            quality_match = False
                        else:
                            quality_match = True
                    else:
                        quality_match = re.search(
                            quality_set, post.title.lower())
                    if not quality_match:
                        if self.hevc_retail:
                            if is_hevc(post.title) and "1080p" in post.title:
                                if is_retail(post.title, False):
                                    self.log_debug(
                                        "%s - Qualität ignoriert (Release ist 1080p-HEVC-Retail)" % post.title)
                                    hevc_retail = True
                                    quality_match = True
                    if not quality_match:
                        self.log_debug(
                            "%s - Release ignoriert (falsche Aufloesung)" % post.title)
                        continue

                ignore = "|".join(
                    [r"\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if self.config.get(
                    "ignore") else r"^unmatchable$"
                found = re.search(ignore, post.title.lower())
                if found:
                    if self.hevc_retail:
                        if is_hevc(post.title) and "1080p" in post.title:
                            if is_retail(post.title, False):
                                self.log_debug(
                                    "%s - Filterliste ignoriert (Release ist 1080p-HEVC-Retail)" % post.title)
                                hevc_retail = True
                                found = False
                if found:
                    self.log_debug(
                        "%s - Release ignoriert (basierend auf ignore-Einstellung)" % post.title)
                    continue
                if self.rsscrawler.get("surround"):
                    if not re.match(r'.*\.(DTS|DD\+*51|DD\+*71|AC3\.5\.*1)\..*', post.title):
                        self.log_debug(
                            post.title + " - Release ignoriert (kein Mehrkanalton)")
                        continue
                season = re.search(r'\.S(\d{1,3})(\.|-|E)', post.title)
                if season:
                    self.log_debug(
                        "%s - Release ignoriert (IMDB sucht nur Filme)" % post.title)
                    continue

                year_in_title = re.findall(
                    r"\.((?:19|20)\d{2})\.", post.title)
                years_in_title = len(year_in_title)
                if years_in_title:
                    title_year = year_in_title[years_in_title - 1]
                else:
                    title_year = ""

                if post_imdb:
                    imdb_url = "http://www.imdb.com/title/" + post_imdb[0]
                else:
                    imdb_url = ""
                    try:
                        search_title = \
                            re.findall(r"(.*?)(?:\.(?:(?:19|20)\d{2})|\.German|\.\d{3,4}p|\.S(?:\d{1,3})\.)",
                                       post.title)[
                                0].replace(
                                ".", "+").replace("ae", u"ä").replace("oe", u"ö").replace("ue", u"ü").replace(
                                "Ae",
                                u"Ä").replace(
                                "Oe", u"Ö").replace("Ue", u"Ü")
                    except:
                        break
                    search_url = "http://www.imdb.com/find?q=" + search_title + "+" + title_year + "&s=tt&ref_=fn_al_tt_ex"
                    search_page = get_url(search_url, self.configfile, self.dbfile, self.scraper)
                    search_soup = BeautifulSoup(search_page, 'lxml')
                    try:
                        search_results = search_soup.find("table", {"class": "findList"}).findAll("td",
                                                                                                  {
                                                                                                      "class": "result_text"})
                    except:
                        try:
                            search_title = \
                                re.findall(r"(.*?)(?:\.(?:(?:19|20)\d{2})|\.German|\.\d{3,4}p|\.S(?:\d{1,3})\.)",
                                           post.title)[
                                    0].replace(
                                    ".", "+")
                        except:
                            break
                        search_url = "http://www.imdb.com/find?q=" + search_title + "+" + title_year + "&s=tt&ref_=fn_al_tt_ex"
                        search_page = get_url(search_url, self.configfile, self.dbfile, self.scraper)
                        search_soup = BeautifulSoup(search_page, 'lxml')
                        try:
                            search_results = search_soup.find("table", {"class": "findList"}).findAll("td",
                                                                                                      {
                                                                                                          "class": "result_text"})
                        except:
                            self.log_debug("%s - Kein passender IMDB-Eintrag gefunden" % post.title)
                            continue
                    found = False
                    for result in search_results:
                        if "TV Series" not in result.text:
                            found = True
                            href = result.find("a")
                            if not title_year:
                                title_year = re.findall(r"(\d{4})", href.next.next)[0]
                            imdb_url = "http://www.imdb.com" + href["href"]
                            break
                    if not found:
                        self.log_debug(
                            "%s - Keine passende Film-IMDB-Seite gefunden" % post.title)

                imdb_details = ""
                min_year = self.config.get("imdbyear")
                if min_year:
                    if title_year:
                        if title_year < min_year:
                            self.log_debug(
                                "%s - Release ignoriert (Film zu alt)" % post.title)
                            continue
                    elif imdb_url:
                        imdb_details = get_url(imdb_url, self.configfile, self.dbfile, self.scraper)
                        if not imdb_details:
                            self.log_debug(
                                "%s - Fehler bei Aufruf der IMDB-Seite" % post.title)
                            continue
                        title_year = re.findall(
                            r"<title>(?:.*) \(((?:19|20)\d{2})\) - IMDb<\/title>", imdb_details)
                        if not title_year:
                            self.log_debug(
                                "%s - Erscheinungsjahr nicht ermittelbar" % post.title)
                            continue
                        else:
                            title_year = title_year[0]
                        if title_year < min_year:
                            self.log_debug(
                                "%s - Release ignoriert (Film zu alt)" % post.title)
                            continue
                if imdb_url:
                    if not imdb_details:
                        imdb_details = get_url(imdb_url, self.configfile, self.dbfile, self.scraper)
                    if not imdb_details:
                        self.log_debug(
                            "%s - Fehler bei Aufruf der IMDB-Seite" % post.title)
                        continue
                    vote_count = re.findall(r'ratingCount">(.*?)<\/span>', imdb_details)
                    if not vote_count:
                        vote_count = re.findall(r'ratingCount.+?(\d{1,}),', imdb_details)
                    if not vote_count:
                        self.log_debug(
                            "%s - Wertungsanzahl nicht ermittelbar" % post.title)
                        continue
                    else:
                        vote_count = int(vote_count[0].replace(
                            ".", "").replace(",", ""))
                    if vote_count < 1500:
                        self.log_debug(
                            post.title + " - Release ignoriert (Weniger als 1500 IMDB-Votes: " + str(
                                vote_count) + ")")
                        continue
                    download_score = re.findall(r'ratingValue">(.*?)<\/span>', imdb_details)
                    if not download_score:
                        download_score = re.findall(r'ratingValue": "(.*?)"', imdb_details)
                        if not download_score:
                            self.log_debug(
                                "%s - IMDB-Wertung nicht ermittelbar" % post.title)
                            continue
                    download_score = float(download_score[0].replace(
                        ",", "."))
                    if download_score > imdb:
                        download_links = self.get_download_links_method(self, content, post.title)
                        found = download_imdb(self,
                                              post.title, download_links, str(download_score), imdb_url,
                                              imdb_details, hevc_retail)
                        if found:
                            for i in found:
                                added_items.append(i)
    return added_items


def search_feed(self, feed):
    if not self.pattern:
        return
    added_items = []
    ignore = "|".join(
        [r"\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if self.config.get(
        "ignore") else r"^unmatchable$"

    if "Regex" not in self.filename:
        s = re.sub(self.SUBSTITUTE, "../..", "^" + self.pattern + r'.(\d{4}|German|\d{3,4}p).*').lower()
    else:
        s = re.sub(self.SUBSTITUTE, "../..", self.pattern).lower()
    settings = str(self.settings)
    liste = str(self.pattern)
    for post in feed.entries:
        try:
            content = post.content[0].value
        except:
            self.log_debug("Fehler beim Abruf von " + post.title + ": Kein Durchsuchbarer Inhalt gefunden.")
            content = False
        if content:
            post.title = post.title.strip(u'\u200b')

        if self.search_regular_done:
            self.log_debug(
                self._SITE + "-Feed ab hier bereits gecrawlt (" + post.title + ") " + "- breche " + self._SITE + "-Suche ab!")
            return added_items

        concat = post.title + post.published + settings + liste
        sha = hashlib.sha256(concat.encode(
            'ascii', 'ignore')).hexdigest()
        if sha == self.last_sha:
            self.search_regular_done = True

        found = re.search(s, post.title.lower())

        if found:
            if content:
                if "mkv" in content.lower():
                    hevc_retail = False
                    found = re.search(ignore, post.title.lower())
                    if found:
                        if self.hevc_retail:
                            if is_hevc(post.title) and "1080p" in post.title:
                                if is_retail(post.title, False):
                                    self.log_debug(
                                        "%s - Filterliste ignoriert (Release ist 1080p-HEVC-Retail)" % post.title)
                                    hevc_retail = True
                                    found = False
                    if found:
                        self.log_debug(
                            "%s - Release ignoriert (basierend auf ignore-Einstellung)" % post.title)
                        continue
                    if self.rsscrawler.get("surround"):
                        if not re.match(r'.*\.(DTS|DD\+*51|DD\+*71|AC3\.5\.*1)\..*', post.title):
                            self.log_debug(
                                post.title + " - Release ignoriert (kein Mehrkanalton)")
                            continue
                    if self.filename == 'MB_Staffeln':
                        ss = self.config.get('seasonsquality')
                    elif 'Regex' not in self.filename:
                        ss = self.config.get('quality')
                    else:
                        ss = False
                    if self.filename == 'MB_Filme':
                        if ss == "480p":
                            if "720p" in post.title.lower() or "1080p" in post.title.lower() or "1080i" in post.title.lower() or "2160p" in post.title.lower():
                                continue
                            found = True
                        else:
                            found = re.search(ss, post.title.lower())
                        if not found:
                            if self.hevc_retail:
                                if is_hevc(post.title) and "1080p" in post.title:
                                    if is_retail(post.title, False):
                                        self.log_debug(
                                            "%s  - Qualität ignoriert (Release ist 1080p-HEVC-Retail)" % post.title)
                                        hevc_retail = True
                                        found = True
                        if found:
                            if self.filename == 'MB_Staffeln' and '.complete.' not in post.title.lower():
                                continue
                            episode = re.search(
                                r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', post.title.lower())
                            if episode:
                                self.log_debug(
                                    "%s - Release ignoriert (Serienepisode)" % post.title)
                                continue
                            found = download_feed(self, post.title, content, hevc_retail)
                            if found:
                                for i in found:
                                    added_items.append(i)
                    elif self.filename == 'MB_Staffeln':
                        validsource = re.search(self.config.get(
                            "seasonssource"), post.title.lower())
                        if not validsource:
                            self.log_debug(
                                post.title + " - Release hat falsche Quelle")
                            continue
                        if ".complete." not in post.title.lower():
                            if "FX" not in self._SITE:
                                self.log_debug(
                                    post.title + " - Staffel noch nicht komplett")
                                continue
                        season = re.search(r"\.s\d", post.title.lower())
                        if not season:
                            self.log_debug(
                                post.title + " - Release ist keine Staffel")
                            continue
                        if not self.config.get("seasonpacks"):
                            staffelpack = re.search(
                                r"s\d.*(-|\.).*s\d", post.title.lower())
                            if staffelpack:
                                self.log_debug(
                                    "%s - Release ignoriert (Staffelpaket)" % post.title)
                                continue
                        if self.filename == 'MB_Staffeln':
                            ss = self.config.get('seasonsquality')
                        elif 'Regex' not in self.filename:
                            ss = self.config.get('quality')
                        else:
                            ss = False
                        if ss == "480p":
                            if "720p" in post.title.lower() or "1080p" in post.title.lower() or "1080i" in post.title.lower() or "2160p" in post.title.lower():
                                continue
                            found = True
                        else:
                            found = re.search(ss, post.title.lower())
                        if found:
                            episode = re.search(
                                r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', post.title.lower())
                            if episode:
                                self.log_debug(
                                    "%s - Release ignoriert (Serienepisode)" % post.title)
                                continue
                            found = download_feed(self, post.title, content, hevc_retail)
                            if found:
                                for i in found:
                                    added_items.append(i)
                    else:
                        found = download_feed(self, post.title, content, hevc_retail)
                        if found:
                            for i in found:
                                added_items.append(i)
    return added_items


def download_hevc(self, title):
    search_title = fullhd_title(title).split('.German', 1)[0].replace(".", " ").replace(" ", "+")
    feedsearch_title = fullhd_title(title).split('.German', 1)[0]
    search_results = []
    if self.url:
        # ToDo: This is broken code (web search needs to be adapted)
        search_results.append(feedparser.parse(
            get_url('https://' + self.url + '/search/' + search_title + "/feed/rss2/",
                    self.configfile, self.dbfile, self.scraper)))

    i = 0
    for content in search_results:
        i += 1

        site = check_is_site(str(content), self.configfile)
        if not site:
            site = ""

        for (key, value) in adhoc_search(self, content, feedsearch_title):
            if is_hevc(key) and "1080p" in key:
                # ToDo This also is broken - since self.get_download_links_method is for the site and not self._SITE
                download_links = self.get_download_links_method(self, content, key)
                if download_links:
                    storage = self.db.retrieve_all(key)
                    storage_replaced = self.db.retrieve_all(key.replace(".COMPLETE", "").replace(".Complete", ""))
                    if 'added' in storage or 'notdl' in storage or 'added' in storage_replaced or 'notdl' in storage_replaced:
                        self.log_debug(
                            "%s - HEVC Release ignoriert (bereits gefunden)" % key)
                        return True

                    englisch = False
                    if "*englisch" in key.lower() or "*english" in key.lower():
                        key = key.replace(
                            '*ENGLISCH', '').replace("*Englisch", "").replace("*ENGLISH", "").replace("*English",
                                                                                                      "").replace(
                            "*", "")
                        englisch = True
                        if not self.rsscrawler.get('english'):
                            self.log_debug(
                                "%s - Englische Releases deaktiviert" % key)
                            return

                    if self.config.get('enforcedl') and '.dl.' not in key.lower():
                        imdb_id = get_imdb_id(key, content, self.filename, self.configfile, self.dbfile,
                                              self.scraper,
                                              self.log_debug)
                        if not imdb_id:
                            dual_found = download_dual_language(self, key, True)
                            if dual_found and ".1080p." in key:
                                return
                            elif not dual_found and not englisch:
                                self.log_debug(
                                    "%s - Kein zweisprachiges HEVC-Release gefunden." % key)
                                self.dl_unsatisfied = True
                        else:
                            if isinstance(imdb_id, list):
                                imdb_id = imdb_id.pop()
                            imdb_url = "http://www.imdb.com/title/" + imdb_id
                            imdb_details = get_url(imdb_url, self.configfile, self.dbfile, self.scraper)
                            if get_original_language(key, imdb_details, imdb_url, self.configfile, self.dbfile,
                                                     self.scraper,
                                                     self.log_debug):
                                dual_found = download_dual_language(self, key, True)
                                if dual_found and ".1080p." in key:
                                    return
                                elif not dual_found and not englisch:
                                    self.log_debug(
                                        "%s - Kein zweisprachiges HEVC-Release gefunden! Breche ab." % key)
                                    self.dl_unsatisfied = True
                                    return

                    if self.filename == 'MB_Filme' or 'IMDB':
                        if self.config.get('cutoff') and is_retail(key, self.dbfile):
                            retail = True
                        elif is_retail(key, False):
                            retail = True
                        else:
                            retail = False
                        if retail:
                            self.device = self.download_method(self.configfile, self.dbfile, self.device, key,
                                                               "RSScrawler",
                                                               download_links,
                                                               self.password)
                            if self.device:
                                self.db.store(
                                    key,
                                    'added'
                                )
                                log_entry = '[Film' + (
                                    '/Retail' if retail else "") + '/HEVC] - ' + key + ' - [' + site + ']'
                                self.log_info(log_entry)
                                notify([log_entry], self.configfile)
                                return log_entry
                    elif self.filename == 'MB_Regex':
                        self.device = self.download_method(self.configfile, self.dbfile, self.device, key,
                                                           "RSScrawler",
                                                           download_links,
                                                           self.password)
                        if self.device:
                            self.db.store(
                                key,
                                'added'
                            )
                            log_entry = '[Film/Serie/RegEx/HEVC] - ' + key + ' - [' + site + ']'
                            self.log_info(log_entry)
                            notify([log_entry], self.configfile)
                            return log_entry
                    else:
                        self.device = self.download_method(self.configfile, self.dbfile, self.device, key,
                                                           "RSScrawler",
                                                           download_links,
                                                           self.password)
                        if self.device:
                            self.db.store(
                                key,
                                'added'
                            )
                            log_entry = '[Staffel/HEVC] - ' + key + ' - [' + site + ']'
                            self.log_info(log_entry)
                            notify([log_entry], self.configfile)
                            return log_entry
                else:
                    storage = self.db.retrieve_all(key)
                    if 'added' not in storage and 'notdl' not in storage:
                        wrong_hoster = '[' + site + 'HEVC-Suche/Hoster fehlt] - ' + key
                        if 'wrong_hoster' not in storage:
                            print(wrong_hoster)
                            self.db.store(key, 'wrong_hoster')
                            notify([wrong_hoster], self.configfile)
                        else:
                            self.log_debug(wrong_hoster)


def download_dual_language(self, title, hevc=False):
    search_title = \
        fullhd_title(title).split('.x264-', 1)[0].split('.h264-', 1)[0].split('.h265-', 1)[0].split('.x265-', 1)[
            0].split('.HEVC-', 1)[0].replace(".", " ").replace(" ", "+")
    feedsearch_title = \
        fullhd_title(title).split('.x264-', 1)[0].split('.h264-', 1)[0].split('.h265-', 1)[0].split('.x265-', 1)[
            0].split('.HEVC-', 1)[0]
    search_results = []
    if self.url:
        # ToDo: This is broken code (web search needs to be adapted)
        search_results.append(feedparser.parse(
            get_url('https://' + self.url + '/search/' + search_title + "/feed/rss2/",
                    self.configfile, self.dbfile, self.scraper)))

    i = 0
    for content in search_results:
        i += 1

        site = check_is_site(str(content), self.configfile)
        if not site:
            site = ""

        for (key, value) in adhoc_search(self, content, feedsearch_title):
            if ".dl." not in key.lower():
                self.log_debug(
                    "%s - Release ignoriert (nicht zweisprachig)" % key)
                continue
            if hevc and not is_hevc(key):
                self.log_debug(
                    "%s - zweisprachiges Release ignoriert (nicht HEVC)" % key)
                continue
            if ".720p." in key.lower():
                path_suffix = "/Remux"
            else:
                path_suffix = ""
            # ToDo This also is broken - since self.get_download_links_method is for the site and not self._SITE
            download_links = self.get_download_links_method(self, content, key)
            if download_links:
                storage = self.db.retrieve_all(key)
                storage_replaced = self.db.retrieve_all(key.replace(".COMPLETE", "").replace(".Complete", ""))
                if 'added' in storage or 'notdl' in storage or 'added' in storage_replaced or 'notdl' in storage_replaced:
                    self.log_debug(
                        "%s - zweisprachiges Release ignoriert (bereits gefunden)" % key)
                    return True
                elif self.filename == 'MB_Filme' or 'IMDB':
                    retail = False
                    if self.config.get('cutoff'):
                        if is_retail(key, self.dbfile):
                            retail = True
                    self.device = self.download_method(self.configfile, self.dbfile, self.device, key,
                                                       "RSScrawler" + path_suffix, download_links, self.password)
                    if self.device:
                        self.db.store(
                            key,
                            'added'
                        )
                        log_entry = '[Film' + (
                            '/Retail' if retail else "") + '/Zweisprachig] - ' + key + ' - [' + site + ']'
                        self.log_info(log_entry)
                        notify([log_entry], self.configfile)
                        return log_entry
                elif self.filename == 'MB_Regex':
                    self.device = self.download_method(self.configfile, self.dbfile, self.device, key,
                                                       "RSScrawler" + path_suffix, download_links, self.password)
                    if self.device:
                        self.db.store(
                            key,
                            'added'
                        )
                        log_entry = '[Film/Serie/RegEx/Zweisprachig] - ' + key + ' - [' + site + ']'
                        self.log_info(log_entry)
                        notify([log_entry], self.configfile)
                        return log_entry
                else:
                    self.device = self.download_method(self.configfile, self.dbfile, self.device, key,
                                                       "RSScrawler" + path_suffix, download_links, self.password)
                    if self.device:
                        self.db.store(
                            key,
                            'added'
                        )
                        log_entry = '[Staffel/Zweisprachig] - ' + key + ' - [' + site + ']'
                        self.log_info(log_entry)
                        notify([log_entry], self.configfile)
                        return log_entry
            else:
                storage = self.db.retrieve_all(key)
                if 'added' not in storage and 'notdl' not in storage:
                    wrong_hoster = '[' + site + 'DL-Suche/Hoster fehlt] - ' + key
                    if 'wrong_hoster' not in storage:
                        print(wrong_hoster)
                        self.db.store(key, 'wrong_hoster')
                        notify([wrong_hoster], self.configfile)
                    else:
                        self.log_debug(wrong_hoster)


def download_imdb(self, key, download_links, score, imdb_url, imdb_details, hevc_retail):
    added_items = []
    if not hevc_retail:
        if self.hevc_retail:
            if not is_hevc(key) and is_retail(key, False):
                if download_hevc(self, key):
                    self.log_debug(
                        "%s - Release ignoriert (stattdessen 1080p-HEVC-Retail gefunden)" % key)
                    return
    if download_links:
        englisch = False
        if "*englisch" in key.lower() or "*english" in key.lower():
            key = key.replace(
                '*ENGLISCH', '').replace("*Englisch", "").replace("*ENGLISH", "").replace("*English",
                                                                                          "").replace(
                "*", "")
            englisch = True
            if not self.rsscrawler.get('english'):
                self.log_debug(
                    "%s - Englische Releases deaktiviert" % key)
                return
        if self.config.get('enforcedl') and '.dl.' not in key.lower():
            if get_original_language(key, imdb_details, imdb_url, self.configfile, self.dbfile, self.scraper,
                                     self.log_debug):
                dual_found = download_dual_language(self, key, self.password)
                if dual_found:
                    added_items.append(dual_found)
                    if ".1080p." in key:
                        return added_items
                elif not dual_found and not englisch:
                    self.log_debug(
                        "%s - Kein zweisprachiges Release gefunden!" % key)
                    return

        if '.3d.' in key.lower():
            self.log_debug(
                "%s - Release ignoriert (3D-Film)" % key.title)
            return
        else:
            retail = False
            if (self.config.get('enforcedl') and '.dl.' in key.lower()) or not self.config.get(
                    'enforcedl'):
                if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                    if self.config.get('enforcedl'):
                        if is_retail(key, self.dbfile):
                            retail = True
            self.device = self.download_method(self.configfile, self.dbfile, self.device, key, "RSScrawler",
                                               download_links, self.password)
            if self.device:
                self.db.store(
                    key,
                    'notdl' if self.config.get(
                        'enforcedl') and '.dl.' not in key.lower() else 'added'
                )
                log_entry = '[IMDB ' + score + '/Film' + (
                    '/Englisch - ' if englisch and not retail else "") + (
                                '/Englisch/Retail' if englisch and retail else "") + (
                                '/Retail' if not englisch and retail else "") + (
                                '/HEVC' if hevc_retail else '') + '] - ' + key + ' - [' + self._SITE + ']'
                self.log_info(log_entry)
                notify([log_entry], self.configfile)
                added_items.append(log_entry)
    else:
        storage = self.db.retrieve_all(key)
        if 'added' not in storage and 'notdl' not in storage:
            wrong_hoster = '[' + self._SITE + '/Hoster fehlt] - ' + key
            if 'wrong_hoster' not in storage:
                print(wrong_hoster)
                self.db.store(key, 'wrong_hoster')
                notify([wrong_hoster], self.configfile)
            else:
                self.log_debug(wrong_hoster)
    return added_items


def download_feed(self, key, content, hevc_retail):
    added_items = []
    if not hevc_retail:
        if self.hevc_retail:
            if not is_hevc(key) and is_retail(key, False):
                if download_hevc(self, key):
                    self.log_debug(
                        "%s - Release ignoriert (stattdessen 1080p-HEVC-Retail gefunden)" % key)
                    return
    download_links = self.get_download_links_method(self, content, key)
    if download_links:
        storage = self.db.retrieve_all(key)
        storage_replaced = self.db.retrieve_all(key.replace(".COMPLETE", "").replace(".Complete", ""))
        if 'added' in storage or 'notdl' in storage or 'added' in storage_replaced or 'notdl' in storage_replaced:
            self.log_debug(
                "%s - Release ignoriert (bereits gefunden)" % key)
            return
        elif not check_valid_release(key, self.retail_only, self.hevc_retail, self.dbfile):
            self.log_debug(
                "%s - Release ignoriert (Gleiche oder bessere Quelle bereits vorhanden)" % key)
            return
        englisch = False
        if "*englisch*" in key.lower() or "*english*" in key.lower():
            key = key.replace(
                '*ENGLISCH*', '').replace("*Englisch*", "").replace("*ENGLISH*", "").replace("*English*", "")
            englisch = True
            if not self.rsscrawler.get('english'):
                self.log_debug(
                    "%s - Englische Releases deaktiviert" % key)
                return
        if self.config.get('enforcedl') and '.dl.' not in key.lower():
            imdb_id = get_imdb_id(key, content, self.filename, self.configfile, self.dbfile, self.scraper,
                                  self.log_debug)
            if not imdb_id:
                dual_found = download_dual_language(self, key, self.password)
                if dual_found:
                    added_items.append(dual_found)
                    if ".1080p." in key:
                        return added_items
                else:
                    self.log_debug(
                        "%s - Kein zweisprachiges Release gefunden." % key)
                    self.dl_unsatisfied = True
            else:
                if isinstance(imdb_id, list):
                    imdb_id = imdb_id.pop()
                imdb_url = "http://www.imdb.com/title/" + imdb_id
                imdb_details = get_url(imdb_url, self.configfile, self.dbfile, self.scraper)
                if get_original_language(key, imdb_details, imdb_url, self.configfile, self.dbfile, self.scraper,
                                         self.log_debug):
                    dual_found = download_dual_language(self, key, self.password)
                    if dual_found:
                        added_items.append(dual_found)
                        if ".1080p." in key:
                            return added_items
                    elif not dual_found and not englisch:
                        self.log_debug(
                            "%s - Kein zweisprachiges Release gefunden! Breche ab." % key)
                        self.dl_unsatisfied = True
                        return
        if self.filename == 'MB_Filme':
            retail = False
            if (self.config.get('enforcedl') and '.dl.' in key.lower()) or not self.config.get(
                    'enforcedl'):
                if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                    if is_retail(key, self.dbfile):
                        retail = True
            else:
                if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                    if is_retail(key, self.dbfile):
                        retail = True
            self.device = self.download_method(self.configfile, self.dbfile, self.device, key, "RSScrawler",
                                               download_links, self.password)
            if self.device:
                self.db.store(
                    key,
                    'notdl' if self.config.get(
                        'enforcedl') and '.dl.' not in key.lower() else 'added'
                )
                log_entry = '[Film' + ('/Englisch' if englisch and not retail else '') + (
                    '/Englisch/Retail' if englisch and retail else '') + (
                                '/Retail' if not englisch and retail else '') + (
                                '/HEVC' if hevc_retail else '') + '] - ' + key + ' - [' + self._SITE + ']'
                self.log_info(log_entry)
                notify([log_entry], self.configfile)
                added_items.append(log_entry)
        elif self.filename == 'MB_Staffeln':
            self.device = self.download_method(self.configfile, self.dbfile, self.device, key, "RSScrawler",
                                               download_links, self.password)
            if self.device:
                self.db.store(
                    key.replace(".COMPLETE", "").replace(
                        ".Complete", ""),
                    'notdl' if self.config.get(
                        'enforcedl') and '.dl.' not in key.lower() else 'added'
                )
                log_entry = '[Staffel] - ' + key.replace(".COMPLETE", "").replace(".Complete",
                                                                                  "") + ' - [' + self._SITE + ']'
                self.log_info(log_entry)
                notify([log_entry], self.configfile)
                added_items.append(log_entry)
        else:
            self.device = self.download_method(self.configfile, self.dbfile, self.device, key, "RSScrawler",
                                               download_links, self.password)
            if self.device:
                self.db.store(
                    key,
                    'notdl' if self.config.get(
                        'enforcedl') and '.dl.' not in key.lower() else 'added'
                )
                log_entry = '[Film/Serie/RegEx] - ' + key + ' - [' + self._SITE + ']'
                self.log_info(log_entry)
                notify([log_entry], self.configfile)
                added_items.append(log_entry)
    else:
        storage = self.db.retrieve_all(key)
        if 'added' not in storage and 'notdl' not in storage:
            wrong_hoster = '[' + self._SITE + '/Hoster fehlt] - ' + key
            if 'wrong_hoster' not in storage:
                print(wrong_hoster)
                self.db.store(key, 'wrong_hoster')
                notify([wrong_hoster], self.configfile)
            else:
                self.log_debug(wrong_hoster)
    return added_items


def periodical_task(self):
    imdb = self.imdb
    urls = []

    if self.filename == 'MB_Staffeln':
        if not self.config.get('crawlseasons'):
            return self.device
        liste = get_movies_list(self, self.filename)
        if liste:
            self.pattern = r'(' + "|".join(liste).lower() + ').*'
    elif self.filename == 'MB_Regex':
        if not self.config.get('regex'):
            self.log_debug(
                "Regex deaktiviert. Stoppe Suche für Filme! (" + self.filename + ")")
            return self.device
        liste = get_movies_list(self, self.filename)
        if liste:
            self.pattern = r'(' + "|".join(liste).lower() + ').*'
    elif self.filename == "IMDB":
        self.pattern = self.filename
    else:
        liste = get_movies_list(self, self.filename)
        if liste:
            self.pattern = r'(' + "|".join(liste).lower() + ').*'

    if self.url:
        for URL in self.FEED_URLS:
            urls.append(URL)

    if not self.pattern:
        self.log_debug(
            "Liste ist leer. Stoppe Suche für Filme! (" + self.filename + ")")
        return self.device

    if self.filename == 'IMDB' and imdb == 0:
        self.log_debug(
            "IMDB-Suchwert ist 0. Stoppe Suche für Filme! (" + self.filename + ")")
        return self.device

    loading_304 = False
    try:
        first_page_raw = self.get_url_headers_method(urls[0], self.configfile, self.dbfile, self.headers, self.scraper)
        self.scraper = first_page_raw[1]
        first_page_raw = first_page_raw[0]
        first_page_content = self.get_feed_method(self, first_page_raw.content)
        if first_page_raw.status_code == 304:
            loading_304 = True
    except:
        loading_304 = True
        first_page_content = False
        self.log_debug("Fehler beim Abruf von " + self._SITE + " - breche " + self._SITE + "-Suche ab!")

    set_all = settings_hash(self, False)

    if self.last_set_all == set_all:
        if loading_304:
            urls = []
            self.log_debug(
                self._SITE + "-Feed seit letztem Aufruf nicht aktualisiert - breche " + self._SITE + "-Suche ab!")

    sha = None

    if self.filename != 'IMDB':
        if not loading_304 and first_page_content:
            for i in first_page_content.entries:
                concat_by = i.title + i.published + str(self.settings) + str(self.pattern)
                sha = hashlib.sha256(concat_by.encode('ascii', 'ignore')).hexdigest()
                break
    else:
        if not loading_304 and first_page_content:
            for i in first_page_content.entries:
                concat_by = i.title + i.published + str(self.settings) + str(self.imdb)
                sha = hashlib.sha256(concat_by.encode('ascii', 'ignore')).hexdigest()
                break

    added_items = []
    if self.filename == "IMDB":
        if imdb > 0:
            i = 0
            for url in urls:
                if not self.search_imdb_done:
                    if i == 0 and first_page_content:
                        parsed_url = first_page_content
                    else:
                        parsed_url = self.get_feed_method(self,
                                                          self.get_url_method(url, self.configfile, self.dbfile,
                                                                              self.scraper))
                    found = search_imdb(self, imdb, parsed_url)
                    if found:
                        for f in found:
                            added_items.append(f)
                    i += 1
    else:
        i = 0
        for url in urls:
            if not self.search_regular_done:
                if i == 0 and first_page_content:
                    parsed_url = first_page_content
                else:
                    parsed_url = self.get_feed_method(self, self.get_url_method(url, self.configfile, self.dbfile,
                                                                                self.scraper))
                found = search_feed(self, parsed_url)
                if found:
                    for f in found:
                        added_items.append(f)
                i += 1

    settings_changed = False
    if set_all:
        new_set_all = settings_hash(self, True)
        if set_all == new_set_all:
            self.cdc.delete("ALLSet-" + self.filename)
            self.cdc.store("ALLSet-" + self.filename, new_set_all)
        else:
            settings_changed = True
    if sha:
        if not self.dl_unsatisfied and not settings_changed:
            self.cdc.delete(self._SITE + "-" + self.filename)
            self.cdc.store(self._SITE + "-" + self.filename, sha)
        else:
            self.log_debug(
                "Für ein oder mehrere Release(s) wurde kein zweisprachiges gefunden. Setze kein neues " + self._SITE + "-CDC!")
    if not loading_304:
        try:
            header = first_page_raw.headers['Last-Modified']
        except KeyError:
            header = False
        if header:
            self.cdc.delete(self._SITE + "Headers-" + self.filename)
            self.cdc.store(self._SITE + "Headers-" + self.filename, header)

    return self.device
