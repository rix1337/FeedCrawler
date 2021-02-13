# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import feedparser
import hashlib
import re

from rsscrawler.common import check_hoster
from rsscrawler.common import check_valid_release
from rsscrawler.common import fullhd_title
from rsscrawler.common import is_hevc
from rsscrawler.common import is_retail
from rsscrawler.config import RssConfig
from rsscrawler.db import ListDb
from rsscrawler.db import RssDb
from rsscrawler.imdb import get_imdb_id
from rsscrawler.imdb import get_original_language
from rsscrawler.myjd import myjd_download
from rsscrawler.notifiers import notify
from rsscrawler.url import check_is_site
from rsscrawler.url import get_url
from rsscrawler.url import get_url_headers


class BL:
    _INTERNAL_NAME = 'MB'
    SUBSTITUTE = r"[&#\s/]"

    def __init__(self, configfile, dbfile, device, logging, scraper, filename):
        self.configfile = configfile
        self.dbfile = dbfile
        self.device = device

        self.hostnames = RssConfig('Hostnames', self.configfile)
        self.url = self.hostnames.get('by')

        self.URL = 'https://' + self.url + '/feed/'
        self.FEED_URLS = [self.URL]

        self.config = RssConfig(self._INTERNAL_NAME, self.configfile)
        self.rsscrawler = RssConfig("RSScrawler", self.configfile)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.scraper = scraper
        self.filename = filename
        self.pattern = False
        self.db = RssDb(self.dbfile, 'rsscrawler')
        self.hevc_retail = self.config.get("hevc_retail")
        self.retail_only = self.config.get("retail_only")
        self.hosters = RssConfig("Hosters", configfile).get_section()
        self.hoster_fallback = self.config.get("hoster_fallback")

        search = int(RssConfig(self._INTERNAL_NAME, self.configfile).get("search"))
        i = 2
        while i <= search:
            page_url = self.URL + "?paged=" + str(i)
            if page_url not in self.FEED_URLS:
                self.FEED_URLS.append(page_url)
            i += 1

        self.cdc = RssDb(self.dbfile, 'cdc')

        self.last_set_all = self.cdc.retrieve("ALLSet-" + self.filename)
        self.headers_by = {'If-Modified-Since': str(self.cdc.retrieve("BYHeaders-" + self.filename))}

        self.last_sha_by = self.cdc.retrieve("BY-" + self.filename)
        settings = ["quality", "search", "ignore", "regex", "cutoff", "crawl3d", "crawl3dtype", "enforcedl",
                    "crawlseasons", "seasonsquality", "seasonpacks", "seasonssource", "imdbyear", "imdb",
                    "hevc_retail", "retail_only", "hoster_fallback"]
        self.settings = []
        self.settings.append(self.rsscrawler.get("english"))
        self.settings.append(self.rsscrawler.get("surround"))
        self.settings.append(self.hosters)
        for s in settings:
            self.settings.append(self.config.get(s))
        self.search_imdb_done = False
        self.search_regular_done = False
        self.dl_unsatisfied = False

        try:
            self.imdb = float(self.config.get('imdb'))
        except:
            self.imdb = 0.0

    def settings_hash(self, refresh):
        if refresh:
            settings = ["quality", "search", "ignore", "regex", "cutoff", "crawl3d", "crawl3dtype", "enforcedl",
                        "crawlseasons", "seasonsquality", "seasonpacks", "seasonssource", "imdbyear", "imdb",
                        "hevc_retail", "retail_only", "hoster_fallback"]
            self.settings = []
            self.settings.append(self.rsscrawler.get("english"))
            self.settings.append(self.rsscrawler.get("surround"))
            self.settings.append(self.hosters)
            for s in settings:
                self.settings.append(self.config.get(s))
            if self.filename == "IMDB":
                self.pattern = self.filename
            else:
                liste = self.get_movies_list(self.filename)
                self.pattern = r'(' + "|".join(liste).lower() + ').*'
        settings = str(self.settings) + str(self.pattern)
        return hashlib.sha256(settings.encode('ascii', 'ignore')).hexdigest()

    def get_movies_list(self, liste):
        cont = ListDb(self.dbfile, liste).retrieve()
        titles = []
        if cont:
            for title in cont:
                if title:
                    title = title.replace(" ", ".")
                    titles.append(title)
        return titles

    def get_download_links(self, content):
        url_hosters = re.findall(r'href="([^"\'>]*)".+?(.+?)<', content)
        links = {}
        for url_hoster in reversed(url_hosters):
            hoster = url_hoster[1].lower().replace('target="_blank">', '').replace(" ", "-")
            if check_hoster(hoster, self.configfile):
                links[hoster] = url_hoster[0]
        if self.hoster_fallback and not links:
            for url_hoster in reversed(url_hosters):
                hoster = url_hoster[1].lower().replace('target="_blank">', '').replace(" ", "-")
                links[hoster] = url_hoster[0]
        return list(links.values())

    def adhoc_search(self, feed, title):
        ignore = "|".join(
            [r"\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if self.config.get(
            "ignore") else r"^unmatchable$"

        s = re.sub(self.SUBSTITUTE, ".", title).lower()
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
                                if is_retail(post.title, False, False):
                                    self.log_debug(
                                        "%s - Release ist 1080p-HEVC-Retail" % post.title)
                                    found = False
                    if found:
                        self.log_debug(
                            "%s - Release ignoriert (basierend auf ignore-Einstellung)" % post.title)
                        continue
                    yield post.title, content

    def imdb_search(self, imdb, feed, site):
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
                    site + "-Feed ab hier bereits gecrawlt (" + post.title + ") - breche BY-Suche ab!")
                return added_items

            concat = post.title + post.published + settings + score
            sha = hashlib.sha256(concat.encode(
                'ascii', 'ignore')).hexdigest()
            if sha == self.last_sha_by:
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
                    if '.3d.' not in post.title.lower():
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
                                    if is_retail(post.title, False, False):
                                        self.log_debug(
                                            "%s - Qualität ignoriert (Release ist 1080p-HEVC-Retail)" % post.title)
                                        hevc_retail = True
                                        quality_match = True
                        if not quality_match:
                            self.log_debug(
                                "%s - Release ignoriert (falsche Aufloesung)" % post.title)
                            continue
                    else:
                        if not self.config.get('crawl3d'):
                            self.log_debug(
                                "%s - Release ignoriert (3D-Suche deaktiviert)" % post.title)
                            return
                        if self.config.get('crawl3d'):
                            if not re.search(quality_set, post.title.lower()):
                                continue
                            if not self.config.get("crawl3dtype"):
                                c3d_type = "hsbs"
                            else:
                                c3d_type = self.config.get("crawl3dtype")
                            if c3d_type == "hsbs":
                                if re.match(r'.*\.(H-OU|HOU)\..*', post.title):
                                    self.log_debug(
                                        "%s - Release ignoriert (Falsches 3D-Format)" % post.title)
                                    continue
                            elif c3d_type == "hou":
                                if not re.match(r'.*\.(H-OU|HOU)\..*', post.title):
                                    self.log_debug(
                                        "%s - Release ignoriert (Falsches 3D-Format)" % post.title)
                                    continue
                        else:
                            continue

                    ignore = "|".join(
                        [r"\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if self.config.get(
                        "ignore") else r"^unmatchable$"
                    found = re.search(ignore, post.title.lower())
                    if found:
                        if self.hevc_retail:
                            if is_hevc(post.title) and "1080p" in post.title:
                                if is_retail(post.title, False, False):
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
                    if years_in_title > 0:
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
                        search_url = "http://www.imdb.com/find?q=" + search_title
                        search_page = get_url(search_url, self.configfile, self.dbfile, self.scraper)
                        search_results = re.findall(
                            r'<td class="result_text"> <a href="\/title\/(tt[0-9]{7,9})\/\?ref_=fn_al_tt_\d" >(.*?)<\/a>.*? \((\d{4})\)..(.{9})',
                            search_page)
                        no_series = False
                        total_results = len(search_results)
                        if total_results == 0:
                            imdb_url = ""
                        else:
                            while total_results > 0:
                                attempt = 0
                                for result in search_results:
                                    if result[3] == "TV Series":
                                        no_series = False
                                        total_results -= 1
                                        attempt += 1
                                    else:
                                        no_series = True
                                        imdb_url = "http://www.imdb.com/title/" + \
                                                   search_results[attempt][0]
                                        title_year = search_results[attempt][2]
                                        total_results = 0
                                        break
                            if no_series is False:
                                self.log_debug(
                                    "%s - Keine passende Film-IMDB-Seite gefunden" % post.title)

                    imdb_details = ""
                    min_year = self.config.get("imdbyear")
                    if min_year:
                        if len(title_year) > 0:
                            if title_year < min_year:
                                self.log_debug(
                                    "%s - Release ignoriert (Film zu alt)" % post.title)
                                continue
                        elif len(imdb_url) > 0:
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
                    if len(imdb_url) > 0:
                        if len(imdb_details) == 0:
                            imdb_details = get_url(imdb_url, self.configfile, self.dbfile, self.scraper)
                        if not imdb_details:
                            self.log_debug(
                                "%s - Release ignoriert (Film zu alt)" % post.title)
                            continue
                        vote_count = re.findall(
                            r'ratingCount">(.*?)<\/span>', imdb_details)
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
                        download_score = re.findall(
                            r'ratingValue">(.*?)<\/span>', imdb_details)
                        download_score = float(download_score[0].replace(
                            ",", "."))
                        if download_score > imdb:
                            password = self.url

                            download_pages = self.get_download_links(content)

                            if '.3d.' not in post.title.lower():
                                found = self.imdb_download(
                                    post.title, download_pages, str(download_score), imdb_url, imdb_details,
                                    password, site, hevc_retail)
                            else:
                                found = self.imdb_download(
                                    post.title, download_pages, str(download_score), imdb_url, imdb_details,
                                    password, site, hevc_retail)
                            if found:
                                for i in found:
                                    added_items.append(i)
        return added_items

    def feed_search(self, feed, site):
        if not self.pattern:
            return
        added_items = []
        password = self.url
        ignore = "|".join(
            [r"\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if self.config.get(
            "ignore") else r"^unmatchable$"

        if "Regex" not in self.filename:
            s = re.sub(self.SUBSTITUTE, ".", "^" + self.pattern + r'.(\d{4}|German|\d{3,4}p).*').lower()
        else:
            s = re.sub(self.SUBSTITUTE, ".", self.pattern).lower()
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
                    site + "-Feed ab hier bereits gecrawlt (" + post.title + ") " + "- breche BY-Suche ab!")
                return added_items

            concat = post.title + post.published + settings + liste
            sha = hashlib.sha256(concat.encode(
                'ascii', 'ignore')).hexdigest()
            if sha == self.last_sha_by:
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
                                    if is_retail(post.title, False, False):
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
                                        if is_retail(post.title, False, False):
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
                                found = self.feed_download(post.title, content, password, site, hevc_retail)
                                if found:
                                    for i in found:
                                        added_items.append(i)
                        elif self.filename == 'MB_3D':
                            if '.3d.' in post.title.lower():
                                if self.config.get('crawl3d'):
                                    if not re.search(ss, post.title.lower()):
                                        continue
                                    if not self.config.get("crawl3dtype"):
                                        c3d_type = "hsbs"
                                    else:
                                        c3d_type = self.config.get("crawl3dtype")
                                    if c3d_type == "hsbs":
                                        if re.match(r'.*\.(H-OU|HOU)\..*', post.title):
                                            self.log_debug(
                                                "%s - Release ignoriert (Falsches 3D-Format)" % post.title)
                                            continue
                                    elif c3d_type == "hou":
                                        if not re.match(r'.*\.(H-OU|HOU)\..*', post.title):
                                            self.log_debug(
                                                "%s - Release ignoriert (Falsches 3D-Format)" % post.title)
                                            continue
                                    found = True
                                else:
                                    continue
                            if found:
                                if self.filename == 'MB_Staffeln' and '.complete.' not in post.title.lower():
                                    continue
                                episode = re.search(
                                    r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', post.title.lower())
                                if episode:
                                    self.log_debug(
                                        "%s - Release ignoriert (Serienepisode)" % post.title)
                                    continue
                                found = self.feed_download(post.title, content, password, site, hevc_retail)
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
                                if "FX" not in site:
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
                                found = self.feed_download(post.title, content, password, site, hevc_retail)
                                if found:
                                    for i in found:
                                        added_items.append(i)
                        else:
                            found = self.feed_download(post.title, content, password, site, hevc_retail)
                            if found:
                                for i in found:
                                    added_items.append(i)
        return added_items

    def hevc_download(self, title, password):
        search_title = fullhd_title(title).split('.German', 1)[0].replace(".", " ").replace(" ", "+")
        feedsearch_title = fullhd_title(title).split('.German', 1)[0]
        search_results = []
        if self.url:
            search_results.append(feedparser.parse(
                get_url('https://' + self.url + '/search/' + search_title + "/feed/rss2/",
                        self.configfile, self.dbfile, self.scraper)))

        i = 0
        for content in search_results:
            i += 1

            site = check_is_site(str(content), self.configfile)
            if not site:
                site = ""

            for (key, value) in self.adhoc_search(content, feedsearch_title):
                if is_hevc(key) and "1080p" in key:
                    download_links = self.get_download_links(value)
                    if download_links:
                        for download_link in download_links:
                            if self.url.split('.')[0] in download_link:
                                self.log_debug("Fake-Link erkannt!")
                                break
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
                                dual_found = self.dual_download(key, password, True)
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
                                    dual_found = self.dual_download(key, password, True)
                                    if dual_found and ".1080p." in key:
                                        return
                                    elif not dual_found and not englisch:
                                        self.log_debug(
                                            "%s - Kein zweisprachiges HEVC-Release gefunden! Breche ab." % key)
                                        self.dl_unsatisfied = True
                                        return

                        if self.filename == 'MB_Filme' or 'IMDB':
                            if self.config.get('cutoff') and is_retail(key, '1', self.dbfile):
                                retail = True
                            elif is_retail(key, False, False):
                                retail = True
                            else:
                                retail = False
                            if retail:
                                self.device = myjd_download(self.configfile, self.dbfile, self.device, key,
                                                            "RSScrawler/Filme",
                                                            download_links,
                                                            password)
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
                        elif self.filename == 'MB_3D':
                            if self.config.get('cutoff') and is_retail(key, '2', self.dbfile):
                                retail = True
                            elif is_retail(key, False, False):
                                retail = True
                            else:
                                retail = False
                            if retail:
                                self.device = myjd_download(self.configfile, self.dbfile, self.device, key,
                                                            "RSScrawler/3D-Filme",
                                                            download_links,
                                                            password)
                                if self.device:
                                    self.db.store(
                                        key,
                                        'added'
                                    )
                                    log_entry = '[Film' + (
                                        '/Retail' if retail else "") + '/3D/HEVC] - ' + key + ' - [' + site + ']'
                                    self.log_info(log_entry)
                                    notify([log_entry], self.configfile)
                                    return log_entry
                        elif self.filename == 'MB_Regex':
                            if re.search(r'\.S(\d{1,3})(\.|-|E)', key):
                                path = "RSScrawler/Serien"
                            elif '.3d.' in key:
                                path = "RSScrawler/3D-Filme"
                            else:
                                path = "RSScrawler/Filme"
                            self.device = myjd_download(self.configfile, self.dbfile, self.device, key,
                                                        path,
                                                        download_links,
                                                        password)
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
                            self.device = myjd_download(self.configfile, self.dbfile, self.device, key,
                                                        "RSScrawler",
                                                        download_links,
                                                        password)
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
                            wrong_hoster = '[HEVC-Suche/Hoster fehlt] - ' + key
                            if 'wrong_hoster' not in storage:
                                print(wrong_hoster)
                                self.db.store(key, 'wrong_hoster')
                                notify([wrong_hoster], self.configfile)
                            else:
                                self.log_debug(wrong_hoster)

    def dual_download(self, title, password, hevc=False):
        search_title = \
            fullhd_title(title).split('.x264-', 1)[0].split('.h264-', 1)[0].split('.h265-', 1)[0].split('.x265-', 1)[
                0].split('.HEVC-', 1)[0].replace(".", " ").replace(" ", "+")
        feedsearch_title = \
            fullhd_title(title).split('.x264-', 1)[0].split('.h264-', 1)[0].split('.h265-', 1)[0].split('.x265-', 1)[
                0].split('.HEVC-', 1)[0]
        search_results = []
        if self.url:
            search_results.append(feedparser.parse(
                get_url('https://' + self.url + '/search/' + search_title + "/feed/rss2/",
                        self.configfile, self.dbfile, self.scraper)))

        i = 0
        for content in search_results:
            i += 1

            site = check_is_site(str(content), self.configfile)
            if not site:
                site = ""

            for (key, value) in self.adhoc_search(content, feedsearch_title):
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
                download_links = self.get_download_links(value)
                if download_links:
                    for download_link in download_links:
                        if self.url.split('.')[0] in download_link:
                            self.log_debug("Fake-Link erkannt!")
                            break
                    storage = self.db.retrieve_all(key)
                    storage_replaced = self.db.retrieve_all(key.replace(".COMPLETE", "").replace(".Complete", ""))
                    if 'added' in storage or 'notdl' in storage or 'added' in storage_replaced or 'notdl' in storage_replaced:
                        self.log_debug(
                            "%s - zweisprachiges Release ignoriert (bereits gefunden)" % key)
                        return True
                    elif self.filename == 'MB_Filme' or 'IMDB':
                        retail = False
                        if self.config.get('cutoff'):
                            if self.config.get('enforcedl'):
                                if is_retail(key, '1', self.dbfile):
                                    retail = True
                            else:
                                if is_retail(key, '0', self.dbfile):
                                    retail = True
                        self.device = myjd_download(self.configfile, self.dbfile, self.device, key,
                                                    "RSScrawler/Filme" + path_suffix, download_links, password)
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
                    elif self.filename == 'MB_3D':
                        retail = False
                        if self.config.get('cutoff'):
                            if is_retail(key, '2', self.dbfile):
                                retail = True
                        self.device = myjd_download(self.configfile, self.dbfile, self.device, key,
                                                    "RSScrawler/3D-Filme" + path_suffix, download_links, password)
                        if self.device:
                            self.db.store(
                                key,
                                'added'
                            )
                            log_entry = '[Film' + (
                                '/Retail' if retail else "") + '/3D/Zweisprachig] - ' + key + ' - [' + site + ']'
                            self.log_info(log_entry)
                            notify([log_entry], self.configfile)
                            return log_entry
                    elif self.filename == 'MB_Regex':
                        if re.search(r'\.S(\d{1,3})(\.|-|E)', key):
                            path = "RSScrawler/Serien"
                        elif '.3d.' in key:
                            path = "RSScrawler/3D-Filme"
                        else:
                            path = "RSScrawler/Filme"
                        self.device = myjd_download(self.configfile, self.dbfile, self.device, key,
                                                    path + path_suffix, download_links, password)
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
                        self.device = myjd_download(self.configfile, self.dbfile, self.device, key,
                                                    "RSScrawler" + path_suffix, download_links, password)
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
                        wrong_hoster = '[DL-Suche/Hoster fehlt] - ' + key
                        if 'wrong_hoster' not in storage:
                            print(wrong_hoster)
                            self.db.store(key, 'wrong_hoster')
                            notify([wrong_hoster], self.configfile)
                        else:
                            self.log_debug(wrong_hoster)

    def imdb_download(self, key, download_links, score, imdb_url, imdb_details, password, site, hevc_retail):
        added_items = []
        if not hevc_retail:
            if self.hevc_retail:
                if not is_hevc(key) and is_retail(key, False, False):
                    if self.hevc_download(key, password):
                        self.log_debug(
                            "%s - Release ignoriert (stattdessen 1080p-HEVC-Retail gefunden)" % key)
                        return
        if download_links:
            for download_link in download_links:
                if self.url.split('.')[0] in download_link:
                    self.log_debug("Fake-Link erkannt!")
                    break
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
                    dual_found = self.dual_download(key, password)
                    if dual_found:
                        added_items.append(dual_found)
                        if ".1080p." in key:
                            return added_items
                    elif not dual_found and not englisch:
                        self.log_debug(
                            "%s - Kein zweisprachiges Release gefunden!" % key)
                        return

            if '.3d.' not in key.lower():
                retail = False
                if (self.config.get('enforcedl') and '.dl.' in key.lower()) or not self.config.get(
                        'enforcedl'):
                    if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                        if self.config.get('enforcedl'):
                            if is_retail(key, '1', self.dbfile):
                                retail = True
                        else:
                            if is_retail(key, '0', self.dbfile):
                                retail = True
                self.device = myjd_download(self.configfile, self.dbfile, self.device, key, "RSScrawler/Filme",
                                            download_links, password)
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
                                    '/HEVC' if hevc_retail else '') + '] - ' + key + ' - [' + site + ']'
                    self.log_info(log_entry)
                    notify([log_entry], self.configfile)
                    added_items.append(log_entry)
            else:
                retail = False
                if (self.config.get('enforcedl') and '.dl.' in key.lower()) or not self.config.get(
                        'enforcedl'):
                    if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                        if self.config.get('enforcedl'):
                            if is_retail(key, '2', self.dbfile):
                                retail = True
                self.device = myjd_download(self.configfile, self.dbfile, self.device, key, "RSScrawler/3D-Filme",
                                            download_links,
                                            password)
                if self.device:
                    self.db.store(
                        key,
                        'notdl' if self.config.get(
                            'enforcedl') and '.dl.' not in key.lower() else 'added'
                    )
                    log_entry = '[IMDB ' + score + '/Film' + (
                        '/Retail' if retail else "") + '/3D' + (
                                    '/HEVC' if hevc_retail else '') + '] - ' + key + ' - [' + site + ']'
                    self.log_info(log_entry)
                    notify([log_entry], self.configfile)
                    added_items.append(log_entry)
        else:
            storage = self.db.retrieve_all(key)
            if 'added' not in storage and 'notdl' not in storage:
                wrong_hoster = '[' + site + '/Hoster fehlt] - ' + key
                if 'wrong_hoster' not in storage:
                    print(wrong_hoster)
                    self.db.store(key, 'wrong_hoster')
                    notify([wrong_hoster], self.configfile)
                else:
                    self.log_debug(wrong_hoster)
        return added_items

    def feed_download(self, key, content, password, site, hevc_retail):
        added_items = []
        if not hevc_retail:
            if self.hevc_retail:
                if not is_hevc(key) and is_retail(key, False, False):
                    if self.hevc_download(key, password):
                        self.log_debug(
                            "%s - Release ignoriert (stattdessen 1080p-HEVC-Retail gefunden)" % key)
                        return
        download_links = self.get_download_links(content)
        if download_links:
            for download_link in download_links:
                if self.url.split('.')[0] in download_link:
                    self.log_debug("Fake-Link erkannt!")
                    break
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
                    dual_found = self.dual_download(key, password)
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
                        dual_found = self.dual_download(key, password)
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
                        if self.config.get('enforcedl'):
                            if is_retail(key, '1', self.dbfile):
                                retail = True
                        else:
                            if is_retail(key, '0', self.dbfile):
                                retail = True
                else:
                    if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                        if is_retail(key, '0', self.dbfile):
                            retail = True
                self.device = myjd_download(self.configfile, self.dbfile, self.device, key, "RSScrawler/Filme",
                                            download_links, password)
                if self.device:
                    self.db.store(
                        key,
                        'notdl' if self.config.get(
                            'enforcedl') and '.dl.' not in key.lower() else 'added'
                    )
                    log_entry = '[Film' + ('/Englisch' if englisch and not retail else '') + (
                        '/Englisch/Retail' if englisch and retail else '') + (
                                    '/Retail' if not englisch and retail else '') + (
                                    '/HEVC' if hevc_retail else '') + '] - ' + key + ' - [' + site + ']'
                    self.log_info(log_entry)
                    notify([log_entry], self.configfile)
                    added_items.append(log_entry)
            elif self.filename == 'MB_3D':
                retail = False
                if (self.config.get('enforcedl') and '.dl.' in key.lower()) or not self.config.get(
                        'enforcedl'):
                    if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                        if self.config.get('enforcedl'):
                            if is_retail(key, '2', self.dbfile):
                                retail = True
                else:
                    if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                        if is_retail(key, '2', self.dbfile):
                            retail = True
                self.device = myjd_download(self.configfile, self.dbfile, self.device, key, "RSScrawler/3D-Filme",
                                            download_links,
                                            password)
                if self.device:
                    self.db.store(
                        key,
                        'notdl' if self.config.get(
                            'enforcedl') and '.dl.' not in key.lower() else 'added'
                    )
                    log_entry = '[Film - ' + (
                        '/Retail' if retail else "") + '/3D - ' + (
                                    '/HEVC' if hevc_retail else '') + ']' + key + ' - [' + site + ']'
                    self.log_info(log_entry)
                    notify([log_entry], self.configfile)
                    added_items.append(log_entry)
            elif self.filename == 'MB_Staffeln':
                self.device = myjd_download(self.configfile, self.dbfile, self.device, key, "RSScrawler",
                                            download_links, password)
                if self.device:
                    self.db.store(
                        key.replace(".COMPLETE", "").replace(
                            ".Complete", ""),
                        'notdl' if self.config.get(
                            'enforcedl') and '.dl.' not in key.lower() else 'added'
                    )
                    log_entry = '[Staffel] - ' + key.replace(".COMPLETE", "").replace(".Complete",
                                                                                      "") + ' - [' + site + ']'
                    self.log_info(log_entry)
                    notify([log_entry], self.configfile)
                    added_items.append(log_entry)
            else:
                if re.search(r'\.S(\d{1,3})(\.|-|E)', key):
                    path = "RSScrawler/Serien"
                elif '.3d.' in key:
                    path = "RSScrawler/3D-Filme"
                else:
                    path = "RSScrawler/Filme"
                self.device = myjd_download(self.configfile, self.dbfile, self.device, key, path,
                                            download_links, password)
                if self.device:
                    self.db.store(
                        key,
                        'notdl' if self.config.get(
                            'enforcedl') and '.dl.' not in key.lower() else 'added'
                    )
                    log_entry = '[Film/Serie/RegEx] - ' + key + ' - [' + site + ']'
                    self.log_info(log_entry)
                    notify([log_entry], self.configfile)
                    added_items.append(log_entry)
        else:
            storage = self.db.retrieve_all(key)
            if 'added' not in storage and 'notdl' not in storage:
                wrong_hoster = '[' + site + '/Hoster fehlt] - ' + key
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
            liste = self.get_movies_list(self.filename)
            if liste:
                self.pattern = r'(' + "|".join(liste).lower() + ').*'
        elif self.filename == 'MB_Regex':
            if not self.config.get('regex'):
                self.log_debug(
                    "Regex deaktiviert. Stoppe Suche für Filme! (" + self.filename + ")")
                return self.device
            liste = self.get_movies_list(self.filename)
            if liste:
                self.pattern = r'(' + "|".join(liste).lower() + ').*'
        elif self.filename == "IMDB":
            self.pattern = self.filename
        else:
            if self.filename == 'MB_3D':
                if not self.config.get('crawl3d'):
                    self.log_debug(
                        "3D-Suche deaktiviert. Stoppe Suche für Filme! (" + self.filename + ")")
                    return self.device
            liste = self.get_movies_list(self.filename)
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
            first_page_raw = get_url_headers(urls[0], self.configfile, self.dbfile, self.headers_by, self.scraper)
            self.scraper = first_page_raw[1]
            first_page_raw = first_page_raw[0]
            first_page_content = feedparser.parse(first_page_raw.content)
            if first_page_raw.status_code == 304:
                loading_304 = True
        except:
            loading_304 = True
            first_page_content = False
            self.log_debug("Fehler beim Abruf von BY - breche BY-Suche ab!")

        set_all = self.settings_hash(False)

        if self.last_set_all == set_all:
            if loading_304:
                urls = []
                self.log_debug("BY-Feed seit letztem Aufruf nicht aktualisiert - breche BY-Suche ab!")

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
                            by_parsed_url = first_page_content
                        else:
                            by_parsed_url = feedparser.parse(
                                get_url(url, self.configfile, self.dbfile, self.scraper))
                        found = self.imdb_search(imdb, by_parsed_url, "BY")
                        if found:
                            for f in found:
                                added_items.append(f)
                        i += 1
        else:
            i = 0
            for url in urls:
                if not self.search_regular_done:
                    if i == 0 and first_page_content:
                        by_parsed_url = first_page_content
                    else:
                        by_parsed_url = feedparser.parse(
                            get_url(url, self.configfile, self.dbfile, self.scraper))
                    found = self.feed_search(by_parsed_url, "BY")
                    if found:
                        for f in found:
                            added_items.append(f)
                    i += 1
            i = 0

        settings_changed = False
        if set_all:
            new_set_all = self.settings_hash(True)
            if set_all == new_set_all:
                self.cdc.delete("ALLSet-" + self.filename)
                self.cdc.store("ALLSet-" + self.filename, new_set_all)
            else:
                settings_changed = True
        if sha:
            if not self.dl_unsatisfied and not settings_changed:
                self.cdc.delete("BY-" + self.filename)
                self.cdc.store("BY-" + self.filename, sha)
            else:
                self.log_debug(
                    "Für ein oder mehrere Release(s) wurde kein zweisprachiges gefunden. Setze kein neues BY-CDC!")
        if not loading_304:
            try:
                header = first_page_raw.headers['Last-Modified']
            except KeyError:
                header = False
            if header:
                self.cdc.delete("BYHeaders-" + self.filename)
                self.cdc.store("BYHeaders-" + self.filename, header)

        return self.device
