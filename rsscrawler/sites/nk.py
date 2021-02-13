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
from rsscrawler.fakefeed import fx_download_links
from rsscrawler.fakefeed import fx_feed_enricher
from rsscrawler.fakefeed import hs_feed_enricher
from rsscrawler.fakefeed import hs_search_to_soup
from rsscrawler.fakefeed import nk_feed_enricher
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
        self.by = self.hostnames.get('by')
        self.hw = self.hostnames.get('hw')
        self.hs = self.hostnames.get('hs')
        self.fx = self.hostnames.get('fx')
        self.nk = self.hostnames.get('nk')

        self.BY_URL = 'https://' + self.by + '/feed/'
        self.BY_FEED_URLS = [self.BY_URL]
        self.HW_URL = 'https://' + self.hw + '/feed/'
        self.HW_FEED_URLS = [self.HW_URL]
        self.HS_URL = 'https://' + self.hs + '/feed'
        self.HS_FEED_URLS = [self.HS_URL]
        self.FX_URL = 'https://' + self.fx
        self.FX_FEED_URLS = [self.FX_URL]
        self.NK_URL = 'https://' + self.nk + '/'
        self.NK_FEED_URLS = [self.NK_URL]

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
            page_url = self.BY_URL + "?paged=" + str(i)
            if page_url not in self.BY_FEED_URLS:
                self.BY_FEED_URLS.append(page_url)
            i += 1

        i = 2
        while i <= search:
            page_url = self.HW_URL + "?paged=" + str(i)
            if page_url not in self.HW_FEED_URLS:
                self.HW_FEED_URLS.append(page_url)
            i += 1

        i = 2
        while i <= search:
            page_url = self.HS_URL + "?paged=" + str(i)
            if page_url not in self.HS_FEED_URLS:
                self.HS_FEED_URLS.append(page_url)
            i += 1

        i = 2
        while i <= search:
            page_url = self.FX_URL + "/page/" + str(i)
            if page_url not in self.FX_FEED_URLS:
                self.FX_FEED_URLS.append(page_url)
            i += 1

        i = 2
        while i <= search:
            page_url = self.NK_URL + "page-" + str(i)
            if page_url not in self.NK_FEED_URLS:
                self.NK_FEED_URLS.append(page_url)
            i += 1

        self.cdc = RssDb(self.dbfile, 'cdc')

        self.last_set_all = self.cdc.retrieve("ALLSet-" + self.filename)
        self.headers_by = {'If-Modified-Since': str(self.cdc.retrieve("BYHeaders-" + self.filename))}
        self.headers_hw = {'If-Modified-Since': str(self.cdc.retrieve("HWHeaders-" + self.filename))}
        self.headers_hs = {'If-Modified-Since': str(self.cdc.retrieve("HSHeaders-" + self.filename))}
        self.headers_fx = {'If-Modified-Since': str(self.cdc.retrieve("FXHeaders-" + self.filename))}
        self.headers_nk = {'If-Modified-Since': str(self.cdc.retrieve("NKHeaders-" + self.filename))}

        self.last_sha_by = self.cdc.retrieve("BY-" + self.filename)
        self.last_sha_hw = self.cdc.retrieve("HW-" + self.filename)
        self.last_sha_hs = self.cdc.retrieve("HS-" + self.filename)
        self.last_sha_fx = self.cdc.retrieve("FX-" + self.filename)
        self.last_sha_nk = self.cdc.retrieve("NK-" + self.filename)
        settings = ["quality", "search", "ignore", "regex", "cutoff", "crawl3d", "crawl3dtype", "enforcedl",
                    "crawlseasons", "seasonsquality", "seasonpacks", "seasonssource", "imdbyear", "imdb",
                    "hevc_retail", "retail_only", "hoster_fallback"]
        self.settings = []
        self.settings.append(self.rsscrawler.get("english"))
        self.settings.append(self.rsscrawler.get("surround"))
        self.settings.append(self.hosters)
        for s in settings:
            self.settings.append(self.config.get(s))
        self.i_by_done = False
        self.i_hw_done = False
        self.i_hs_done = False
        self.i_fx_done = False
        self.i_nk_done = False
        self.by_done = False
        self.hw_done = False
        self.hs_done = False
        self.fx_done = False
        self.nk_done = False
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

            if site == "BY":
                if self.i_by_done:
                    self.log_debug(
                        site + "-Feed ab hier bereits gecrawlt (" + post.title + ") - breche BY-Suche ab!")
                    return added_items
            elif site == "HW":
                if self.i_hw_done:
                    self.log_debug(
                        site + "-Feed ab hier bereits gecrawlt (" + post.title + ") - breche HW-Suche ab!")
                    return added_items
            elif site == "HS":
                if self.i_hs_done:
                    self.log_debug(
                        site + "-Feed ab hier bereits gecrawlt (" + post.title + ") " + "- breche HS-Suche ab!")
                    return added_items
            elif site == "FX":
                if self.i_fx_done:
                    self.log_debug(
                        site + "-Feed ab hier bereits gecrawlt (" + post.title + ") " + "- breche FX-Suche ab!")
                    return added_items
            else:
                if self.i_nk_done:
                    self.log_debug(
                        site + "-Feed ab hier bereits gecrawlt (" + post.title + ") " + "- breche NK-Suche ab!")
                    return added_items

            concat = post.title + post.published + settings + score
            sha = hashlib.sha256(concat.encode(
                'ascii', 'ignore')).hexdigest()
            if ("BY" in site and sha == self.last_sha_by) or ("HW" in site and sha == self.last_sha_hw) or (
                    "HS" in site and sha == self.last_sha_hs) or ("FX" in site and sha == self.last_sha_fx) or (
                    "NK" in site and sha == self.last_sha_nk):
                if "BY" in site:
                    self.i_by_done = True
                elif "HW" in site:
                    self.i_hw_done = True
                elif "HS" in site:
                    self.i_hs_done = True
                elif "FX" in site:
                    self.i_fx_done = True
                else:
                    self.i_nk_done = True

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
                            if "BY" in site:
                                password = self.by
                            elif "HW" in site:
                                password = self.hw
                            elif "HS" in site:
                                password = self.hs
                            elif "FX" in site:
                                password = self.fx.split('.')[0]
                            else:
                                password = self.nk.split('.')[0].capitalize()

                            if "FX" not in site:
                                download_pages = self.get_download_links(content)
                            else:
                                download_pages = fx_download_links(content, post.title, self.configfile)

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
        if "BY" in site:
            password = self.by
        elif "HW" in site:
            password = self.hw
        elif "HS" in site:
            password = self.hs
        elif "FX" in site:
            password = self.fx.split('.')[0]
        else:
            password = self.nk.split('.')[0].capitalize()
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

            if site == "BY":
                if self.by_done:
                    self.log_debug(
                        site + "-Feed ab hier bereits gecrawlt (" + post.title + ") " + "- breche BY-Suche ab!")
                    return added_items
            elif site == "HW":
                if self.hw_done:
                    self.log_debug(
                        site + "-Feed ab hier bereits gecrawlt (" + post.title + ") " + "- breche HW-Suche ab!")
                    return added_items
            elif site == "HS":
                if self.hs_done:
                    self.log_debug(
                        site + "-Feed ab hier bereits gecrawlt (" + post.title + ") " + "- breche HS-Suche ab!")
                    return added_items
            elif site == "FX":
                if self.fx_done:
                    self.log_debug(
                        site + "-Feed ab hier bereits gecrawlt (" + post.title + ") " + "- breche FX-Suche ab!")
                    return added_items
            else:
                if self.nk_done:
                    self.log_debug(
                        site + "-Feed ab hier bereits gecrawlt (" + post.title + ") " + "- breche NK-Suche ab!")
                    return added_items

            concat = post.title + post.published + settings + liste
            sha = hashlib.sha256(concat.encode(
                'ascii', 'ignore')).hexdigest()
            if ("BY" in site and sha == self.last_sha_by) or ("HW" in site and sha == self.last_sha_hw) or (
                    "HS" in site and sha == self.last_sha_hs) or ("FX" in site and sha == self.last_sha_fx) or (
                    "NK" in site and sha == self.last_sha_nk):
                if "BY" in site:
                    self.by_done = True
                elif "HW" in site:
                    self.hw_done = True
                elif "HS" in site:
                    self.hs_done = True
                elif "FX" in site:
                    self.fx_done = True
                else:
                    self.nk_done = True

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
        if self.by:
            search_results.append(feedparser.parse(
                get_url('https://' + self.by + '/search/' + search_title + "/feed/rss2/",
                        self.configfile, self.dbfile, self.scraper)))
        if self.hw:
            search_results.append(feedparser.parse(
                get_url('https://' + self.hw + '/search/' + search_title + "/feed/rss2/",
                        self.configfile, self.dbfile, self.scraper)))
        if self.hs:
            search_results.append(hs_search_to_soup('https://' + self.hs + '/search/' + search_title + '/feed/',
                                                    self.configfile, self.dbfile, self.scraper))
        if self.fx:
            search_results.append(feedparser.parse(
                get_url('https://' + self.fx + '/search/' + search_title + "/feed/rss2/",
                        self.configfile, self.dbfile, self.scraper)))

        i = 0
        for content in search_results:
            i += 1

            site = check_is_site(str(content), self.configfile)
            if not site:
                site = ""

            for (key, value) in self.adhoc_search(content, feedsearch_title):
                if is_hevc(key) and "1080p" in key:
                    if i < 3:
                        download_links = self.get_download_links(value)
                    else:
                        # FX
                        download_links = fx_download_links(content, key, self.configfile)
                    if download_links:
                        for download_link in download_links:
                            if self.by.split('.')[0] in download_link:
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
        if self.by:
            search_results.append(feedparser.parse(
                get_url('https://' + self.by + '/search/' + search_title + "/feed/rss2/",
                        self.configfile, self.dbfile, self.scraper)))
        if self.hw:
            search_results.append(feedparser.parse(
                get_url('https://' + self.hw + '/search/' + search_title + "/feed/rss2/",
                        self.configfile, self.dbfile, self.scraper)))
        if self.hs:
            search_results.append(hs_search_to_soup('https://' + self.hs + '/search/' + search_title + '/feed/',
                                                    self.configfile, self.dbfile, self.scraper))
        if self.fx:
            search_results.append(feedparser.parse(
                get_url('https://' + self.fx + '/search/' + search_title + "/feed/rss2/",
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
                # this enables automatic remuxing of 720p files with a 1080p dual language version
                if ".720p." in key.lower():
                    path_suffix = "/Remux"
                else:
                    path_suffix = ""
                if i < 3:
                    download_links = self.get_download_links(value)
                else:
                    # FX
                    download_links = fx_download_links(content, key, self.configfile)
                if download_links:
                    for download_link in download_links:
                        if self.by.split('.')[0] in download_link:
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
                if self.by.split('.')[0] in download_link:
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
        if "FX" not in site:
            download_links = self.get_download_links(content)
        else:
            download_links = fx_download_links(content, key, self.configfile)
        if download_links:
            for download_link in download_links:
                if self.by.split('.')[0] in download_link:
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
        by_urls = []
        hw_urls = []
        hs_urls = []
        fx_urls = []
        nk_urls = []

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

        if self.by:
            for URL in self.BY_FEED_URLS:
                by_urls.append(URL)
        if self.hw:
            for URL in self.HW_FEED_URLS:
                hw_urls.append(URL)
        if self.hs:
            for URL in self.HS_FEED_URLS:
                hs_urls.append(URL)
        if self.fx:
            for URL in self.FX_FEED_URLS:
                fx_urls.append(URL)
        if self.nk:
            for URL in self.NK_FEED_URLS:
                nk_urls.append(URL)

        if not self.pattern:
            self.log_debug(
                "Liste ist leer. Stoppe Suche für Filme! (" + self.filename + ")")
            return self.device

        if self.filename == 'IMDB' and imdb == 0:
            self.log_debug(
                "IMDB-Suchwert ist 0. Stoppe Suche für Filme! (" + self.filename + ")")
            return self.device

        by_304 = False
        try:
            first_by = get_url_headers(by_urls[0], self.configfile, self.dbfile, self.headers_by, self.scraper)
            self.scraper = first_by[1]
            first_by = first_by[0]
            first_page_by = feedparser.parse(first_by.content)
            if first_by.status_code == 304:
                by_304 = True
        except:
            by_304 = True
            first_page_by = False
            self.log_debug("Fehler beim Abruf von BY - breche BY-Suche ab!")

        hw_304 = False
        try:
            first_hw = get_url_headers(hw_urls[0], self.configfile, self.dbfile, self.headers_hw, self.scraper)
            self.scraper = first_hw[1]
            first_hw = first_hw[0]
            first_page_hw = feedparser.parse(first_hw.content)
            if first_hw.status_code == 304:
                hw_304 = True
        except:
            hw_304 = True
            first_page_hw = False
            self.log_debug("Fehler beim Abruf von HW - breche HW-Suche ab!")

        hs_304 = False
        try:
            first_hs = get_url_headers(hs_urls[0], self.configfile, self.dbfile, self.headers_hs, self.scraper)
            self.scraper = first_hs[1]
            first_hs = first_hs[0]
            first_page_hs = hs_feed_enricher(first_hs.content, self.configfile, self.dbfile, self.scraper)
            if first_hs.status_code == 304:
                hs_304 = True
        except:
            hs_304 = True
            first_page_hs = False
            self.log_debug("Fehler beim Abruf von HS - breche HS-Suche ab!")

        fx_304 = False
        try:
            first_fx = get_url_headers(fx_urls[0], self.configfile, self.dbfile, self.headers_fx, self.scraper)
            self.scraper = first_fx[1]
            first_fx = first_fx[0]
            first_page_fx = fx_feed_enricher(first_fx.content, self.configfile)
            if first_fx.status_code == 304:
                fx_304 = True
        except:
            fx_304 = True
            first_page_fx = False
            self.log_debug("Fehler beim Abruf von FX - breche FX-Suche ab!")

        nk_304 = False
        try:
            first_nk = get_url_headers(nk_urls[0], self.configfile, self.dbfile, self.headers_nk, self.scraper)
            self.scraper = first_nk[1]
            first_nk = first_nk[0]
            first_page_nk = nk_feed_enricher(first_nk.content, self.NK_URL, self.configfile, self.dbfile,
                                             self.scraper)
            if first_nk.status_code == 304:
                nk_304 = True
        except:
            nk_304 = True
            first_page_nk = False
            self.log_debug("Fehler beim Abruf von NK - breche NK-Suche ab!")

        set_all = self.settings_hash(False)

        if self.last_set_all == set_all:
            if by_304 and hw_304 and hs_304 and fx_304 and nk_304:
                self.log_debug("Alle Blog-Feeds seit letztem Aufruf nicht aktualisiert - breche Suche ab!")
                return self.device
            if by_304:
                by_urls = []
                self.log_debug("BY-Feed seit letztem Aufruf nicht aktualisiert - breche BY-Suche ab!")
            if hw_304:
                hw_urls = []
                self.log_debug("HW-Feed seit letztem Aufruf nicht aktualisiert - breche HW-Suche ab!")
            if hs_304:
                hs_urls = []
                self.log_debug("HS-Feed seit letztem Aufruf nicht aktualisiert - breche HS-Suche ab!")
            if fx_304:
                fx_urls = []
                self.log_debug("FX-Feed seit letztem Aufruf nicht aktualisiert - breche FX-Suche ab!")
            if nk_304:
                nk_urls = []
                self.log_debug("NK-Feed seit letztem Aufruf nicht aktualisiert - breche NK-Suche ab!")

        sha_by = None
        sha_hw = None
        sha_hs = None
        sha_fx = None
        sha_nk = None

        if self.filename != 'IMDB':
            if not by_304 and first_page_by:
                for i in first_page_by.entries:
                    concat_by = i.title + i.published + str(self.settings) + str(self.pattern)
                    sha_by = hashlib.sha256(concat_by.encode('ascii', 'ignore')).hexdigest()
                    break
            if not hw_304 and first_page_hw:
                for i in first_page_hw.entries:
                    concat_hw = i.title + i.published + str(self.settings) + str(self.pattern)
                    sha_hw = hashlib.sha256(concat_hw.encode('ascii', 'ignore')).hexdigest()
                    break
            if not hs_304 and first_page_hs:
                for i in first_page_hs.entries:
                    concat_hs = i.title + i.published + str(self.settings) + str(self.pattern)
                    sha_hs = hashlib.sha256(concat_hs.encode('ascii', 'ignore')).hexdigest()
                    break
            if not fx_304 and first_page_fx:
                for i in first_page_fx.entries:
                    concat_fx = i.title + i.published + str(self.settings) + str(self.pattern)
                    sha_fx = hashlib.sha256(concat_fx.encode('ascii', 'ignore')).hexdigest()
                    break
            if not nk_304 and first_page_nk:
                for i in first_page_nk.entries:
                    concat_nk = i.title + i.published + str(self.settings) + str(self.pattern)
                    sha_nk = hashlib.sha256(concat_nk.encode('ascii', 'ignore')).hexdigest()
                    break
        else:
            if not by_304 and first_page_by:
                for i in first_page_by.entries:
                    concat_by = i.title + i.published + str(self.settings) + str(self.imdb)
                    sha_by = hashlib.sha256(concat_by.encode('ascii', 'ignore')).hexdigest()
                    break
            if not hw_304 and first_page_hw:
                for i in first_page_hw.entries:
                    concat_hw = i.title + i.published + str(self.settings) + str(self.imdb)
                    sha_hw = hashlib.sha256(concat_hw.encode('ascii', 'ignore')).hexdigest()
                    break
            if not hs_304 and first_page_hs:
                for i in first_page_hs.entries:
                    concat_hs = i.title + i.published + str(self.settings) + str(self.imdb)
                    sha_hs = hashlib.sha256(concat_hs.encode('ascii', 'ignore')).hexdigest()
                    break
            if not fx_304 and first_page_fx:
                for i in first_page_fx.entries:
                    concat_fx = i.title + i.published + str(self.settings) + str(self.pattern)
                    sha_fx = hashlib.sha256(concat_fx.encode('ascii', 'ignore')).hexdigest()
                    break
            if not nk_304 and first_page_nk:
                for i in first_page_nk.entries:
                    concat_nk = i.title + i.published + str(self.settings) + str(self.pattern)
                    sha_nk = hashlib.sha256(concat_nk.encode('ascii', 'ignore')).hexdigest()
                    break

        added_items = []
        if self.filename == "IMDB":
            if imdb > 0:
                i = 0
                for url in by_urls:
                    if not self.i_by_done:
                        if i == 0 and first_page_by:
                            by_parsed_url = first_page_by
                        else:
                            by_parsed_url = feedparser.parse(
                                get_url(url, self.configfile, self.dbfile, self.scraper))
                        found = self.imdb_search(imdb, by_parsed_url, "BY")
                        if found:
                            for f in found:
                                added_items.append(f)
                        i += 1
                i = 0
                for url in hw_urls:
                    if not self.i_hw_done:
                        if i == 0 and first_page_hw:
                            hw_parsed_url = first_page_hw
                        else:
                            hw_parsed_url = feedparser.parse(
                                get_url(url, self.configfile, self.dbfile, self.scraper))
                        found = self.imdb_search(imdb, hw_parsed_url, "HW")
                        if found:
                            for f in found:
                                added_items.append(f)
                        i += 1
                i = 0
                for url in hs_urls:
                    if not self.i_hs_done:
                        if i == 0 and first_page_hs:
                            hs_parsed_url = first_page_hs
                        else:
                            hs_parsed_url = hs_feed_enricher(
                                get_url(url, self.configfile, self.dbfile, self.scraper), self.configfile, self.dbfile,
                                self.scraper)
                        found = self.imdb_search(imdb, hs_parsed_url, "HS")
                        if found:
                            for f in found:
                                added_items.append(f)
                        i += 1
                i = 0
                for url in fx_urls:
                    if not self.i_fx_done:
                        if i == 0 and first_page_fx:
                            fx_parsed_url = first_page_fx
                        else:
                            fx_parsed_url = fx_feed_enricher(
                                get_url(url, self.configfile, self.dbfile, self.scraper), self.configfile)
                        found = self.imdb_search(imdb, fx_parsed_url, "FX")
                        if found:
                            for f in found:
                                added_items.append(f)
                        i += 1
                for url in nk_urls:
                    if not self.i_nk_done:
                        if i == 0 and first_page_nk:
                            nk_parsed_url = first_page_nk
                        else:
                            nk_parsed_url = nk_feed_enricher(
                                get_url(url, self.configfile, self.dbfile, self.scraper), self.NK_URL, self.configfile,
                                self.dbfile,
                                self.scraper)
                        found = self.imdb_search(imdb, nk_parsed_url, "NK")
                        if found:
                            for f in found:
                                added_items.append(f)
                        i += 1
        else:
            i = 0
            for url in by_urls:
                if not self.by_done:
                    if i == 0 and first_page_by:
                        by_parsed_url = first_page_by
                    else:
                        by_parsed_url = feedparser.parse(
                            get_url(url, self.configfile, self.dbfile, self.scraper))
                    found = self.feed_search(by_parsed_url, "BY")
                    if found:
                        for f in found:
                            added_items.append(f)
                    i += 1
            i = 0
            for url in hw_urls:
                if not self.hw_done:
                    if i == 0 and first_page_hw:
                        hw_parsed_url = first_page_hw
                    else:
                        hw_parsed_url = feedparser.parse(
                            get_url(url, self.configfile, self.dbfile, self.scraper))
                    found = self.feed_search(hw_parsed_url, "HW")
                    if found:
                        for f in found:
                            added_items.append(f)
                    i += 1
            i = 0
            for url in hs_urls:
                if not self.hs_done:
                    if i == 0 and first_page_hs:
                        hs_parsed_url = first_page_hs
                    else:
                        hs_parsed_url = hs_feed_enricher(
                            get_url(url, self.configfile, self.dbfile, self.scraper), self.configfile, self.dbfile,
                            self.scraper)
                    found = self.feed_search(hs_parsed_url, "HS")
                    if found:
                        for f in found:
                            added_items.append(f)
                    i += 1
            i = 0
            for url in fx_urls:
                if not self.fx_done:
                    if i == 0 and first_page_fx:
                        fx_parsed_url = first_page_fx
                    else:
                        fx_parsed_url = fx_feed_enricher(
                            get_url(url, self.configfile, self.dbfile, self.scraper), self.configfile)
                    found = self.feed_search(fx_parsed_url, "FX")
                    if found:
                        for f in found:
                            added_items.append(f)
                    i += 1
            for url in nk_urls:
                if not self.nk_done:
                    if i == 0 and first_page_nk:
                        nk_parsed_url = first_page_nk
                    else:
                        nk_parsed_url = nk_feed_enricher(
                            get_url(url, self.configfile, self.dbfile, self.scraper), self.NK_URL, self.configfile,
                            self.dbfile,
                            self.scraper)
                    found = self.feed_search(nk_parsed_url, "NK")
                    if found:
                        for f in found:
                            added_items.append(f)
                    i += 1

        settings_changed = False
        if set_all:
            new_set_all = self.settings_hash(True)
            if set_all == new_set_all:
                self.cdc.delete("ALLSet-" + self.filename)
                self.cdc.store("ALLSet-" + self.filename, new_set_all)
            else:
                settings_changed = True
        if sha_by:
            if not self.dl_unsatisfied and not settings_changed:
                self.cdc.delete("BY-" + self.filename)
                self.cdc.store("BY-" + self.filename, sha_by)
            else:
                self.log_debug(
                    "Für ein oder mehrere Release(s) wurde kein zweisprachiges gefunden. Setze kein neues BY-CDC!")
        if sha_hw:
            if not self.dl_unsatisfied and not settings_changed:
                self.cdc.delete("HW-" + self.filename)
                self.cdc.store("HW-" + self.filename, sha_hw)
            else:
                self.log_debug(
                    "Für ein oder mehrere Release(s) wurde kein zweisprachiges gefunden. Setze kein neues HW-CDC!")
        if sha_hs:
            if not self.dl_unsatisfied and not settings_changed:
                self.cdc.delete("HS-" + self.filename)
                self.cdc.store("HS-" + self.filename, sha_hs)
            else:
                self.log_debug(
                    "Für ein oder mehrere Release(s) wurde kein zweisprachiges gefunden. Setze kein neues HS-CDC!")
        if sha_fx:
            if not self.dl_unsatisfied and not settings_changed:
                self.cdc.delete("FX-" + self.filename)
                self.cdc.store("FX-" + self.filename, sha_fx)
            else:
                self.log_debug(
                    "Für ein oder mehrere Release(s) wurde kein zweisprachiges gefunden. Setze kein neues FX-CDC!")
        if sha_nk:
            if not self.dl_unsatisfied and not settings_changed:
                self.cdc.delete("NK-" + self.filename)
                self.cdc.store("NK-" + self.filename, sha_nk)
            else:
                self.log_debug(
                    "Für ein oder mehrere Release(s) wurde kein zweisprachiges gefunden. Setze kein neues NK-CDC!")
        if not by_304:
            try:
                header = first_by.headers['Last-Modified']
            except KeyError:
                header = False
            if header:
                self.cdc.delete("BYHeaders-" + self.filename)
                self.cdc.store("BYHeaders-" + self.filename, header)
        if not hw_304:
            try:
                header = first_hw.headers['Last-Modified']
            except KeyError:
                header = False
            if header:
                self.cdc.delete("HWHeaders-" + self.filename)
                self.cdc.store("HWHeaders-" + self.filename, header)
        if not hs_304:
            try:
                header = first_hs.headers['Last-Modified']
            except KeyError:
                header = False
            if header:
                self.cdc.delete("HSHeaders-" + self.filename)
                self.cdc.store("HSHeaders-" + self.filename, header)
        if not fx_304:
            try:
                header = first_fx.headers['Last-Modified']
            except KeyError:
                header = False
            if header:
                self.cdc.delete("FXHeaders-" + self.filename)
                self.cdc.store("FXHeaders-" + self.filename, header)
        if not nk_304:
            try:
                header = first_nk.headers['Last-Modified']
            except KeyError:
                header = False
            if header:
                self.cdc.delete("NKHeaders-" + self.filename)
                self.cdc.store("NKHeaders-" + self.filename, header)

        return self.device
