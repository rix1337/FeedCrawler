# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337
# Enthält Code von:
# https://github.com/zapp-brannigan/

import hashlib
import re

import feedparser
import six

from rsscrawler.common import cutoff
from rsscrawler.common import decode_base64
from rsscrawler.common import fullhd_title
from rsscrawler.common import retail_sub
from rsscrawler.myjd import myjd_download
from rsscrawler.rssconfig import RssConfig
from rsscrawler.rssdb import ListDb
from rsscrawler.rssdb import RssDb
from rsscrawler.url import get_url
from rsscrawler.url import get_url_headers


class BL:
    _INTERNAL_NAME = 'MB'
    MB_URL = decode_base64("aHR0cDovL21vdmllLWJsb2cudG8vZmVlZC8=")
    MB_FEED_URLS = [MB_URL]
    HW_URL = decode_base64("aHR0cDovL2hkLXdvcmxkLm9yZy9mZWVkLw==")
    HW_FEED_URLS = [HW_URL]
    SUBSTITUTE = r"[&#\s/]"

    def __init__(self, configfile, dbfile, device, logging, filename):
        self.configfile = configfile
        self.dbfile = dbfile
        self.device = device
        self.config = RssConfig(self._INTERNAL_NAME, self.configfile)
        self.device = device
        self.rsscrawler = RssConfig("RSScrawler", self.configfile)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.filename = filename
        self.allInfos = self.filename
        self.db = RssDb(self.dbfile, 'rsscrawler')
        self.db_retail = RssDb(self.dbfile, 'retail')
        self.hoster = re.compile(self.config.get("hoster"))

        search = int(RssConfig(self._INTERNAL_NAME, self.configfile).get("search"))
        self.historical = False
        if search == 99:
            self.historical = True
            search = 3
        i = 2
        while i <= search:
            self.MB_FEED_URLS.append(self.MB_URL + "?paged=" + str(i))
            i += 1

        i = 2
        while i <= search:
            self.HW_FEED_URLS.append(self.HW_URL + "?paged=" + str(i))
            i += 1

        self.cdc = RssDb(self.dbfile, 'cdc')

        self.last_set_mbhw = self.cdc.retrieve("MBHWSet-" + self.filename)
        self.headers_mb = {'If-Modified-Since': str(self.cdc.retrieve("MBHeaders-" + self.filename))}
        self.headers_hw = {'If-Modified-Since': str(self.cdc.retrieve("HWHeaders-" + self.filename))}

        self.last_sha_mb = self.cdc.retrieve("MB-" + self.filename)
        self.last_sha_hw = self.cdc.retrieve("HW-" + self.filename)
        settings = ["quality", "ignore", "search", "regex", "cutoff", "crawl3d", "crawl3dtype", "enforcedl",
                    "crawlseasons", "seasonsquality", "seasonpacks", "seasonssource", "imdbyear", "imdb", "hoster"]
        self.settings = []
        self.settings.append(self.rsscrawler.get("english"))
        self.settings.append(self.rsscrawler.get("surround"))
        for s in settings:
            self.settings.append(self.config.get(s))
        self.i_mb_done = False
        self.i_hw_done = False
        self.mb_done = False
        self.hw_done = False
        self.dl_unsatisfied = False

        try:
            self.imdb = float(self.config.get('imdb'))
        except:
            self.imdb = 0.0
        self.dictWithNamesAndLinks = {}
        self.empty_list = False

    def read_input(self, liste):
        cont = ListDb(self.dbfile, liste).retrieve()
        if not cont:
            self.empty_list = True
            return ""
        else:
            return cont

    def get_patterns(self, patterns, **kwargs):
        if not patterns:
            self.empty_list = True
        if kwargs:
            return {line: (kwargs['quality'], kwargs['rg'], kwargs['sf']) for line in patterns}
        return {x: x for x in patterns}

    def get_download_links(self, content):
        url_hosters = re.findall(r'href="([^"\'>]*)".+?(.+?)<', content)
        links = {}
        for url_hoster in reversed(url_hosters):
            url = decode_base64("bW92aWUtYmxvZy50by8=")
            if url not in url_hoster[0] and "https://goo.gl/" not in url_hoster[0]:
                hoster = url_hoster[1].lower().replace('target="_blank">', '')
                if re.match(self.hoster, hoster):
                    links[hoster] = url_hoster[0]
        return links.values() if six.PY2 else list(links.values())

    def dual_search(self, feed, title):
        ignore = "|".join(
            [r"\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if self.config.get(
            "ignore") else r"^unmatchable$"

        s = re.sub(self.SUBSTITUTE, ".", title).lower()
        for post in feed.entries:
            found = re.search(s, post.title.lower())
            if found:
                content = post.content[0].value
                found = re.search(ignore, post.title.lower())
                if found:
                    self.log_debug(
                        "%s - zweisprachiges Release ignoriert (basierend auf ignore-Einstellung)" % post.title)
                    continue
                yield (post.title, content, title)

    def imdb_search(self, imdb, feed, site):
        added_items = []
        settings = str(self.settings)
        score = str(self.imdb)
        for post in feed.entries:
            concat = post.title + post.published + \
                     settings + score
            sha = hashlib.sha256(concat.encode(
                'ascii', 'ignore')).hexdigest()
            if ("MB" in site and sha == self.last_sha_mb) or ("HW" in site and sha == self.last_sha_hw):
                self.log_debug(
                    site + "-Feed ab hier bereits gecrawlt (" + post.title + ") - breche Suche ab!")
                if "MB" in site:
                    self.i_mb_done = True
                elif "HW" in site:
                    self.i_hw_done = True
                break
            content = post.content[0].value
            if "mkv" in content.lower():
                post_imdb = re.findall(
                    r'.*?(?:href=.?http(?:|s):\/\/(?:|www\.)imdb\.com\/title\/(tt[0-9]{7,9}).*?).*?(\d(?:\.|\,)\d)(?:.|.*?)<\/a>.*?',
                    content)

                if post_imdb:
                    post_imdb = post_imdb.pop()
                replaced = retail_sub(post.title)
                retailtitle = self.db_retail.retrieve(replaced[0])
                retailyear = self.db_retail.retrieve(replaced[1])
                if str(self.db.retrieve(post.title)) == 'added' or str(self.db.retrieve(post.title)) == 'notdl' or str(
                        self.db.retrieve(post.title.replace(".COMPLETE", "").replace(".Complete", ""))) == 'added':
                    self.log_debug(
                        "%s - Release ignoriert (bereits gefunden)" % post.title)
                    continue
                elif retailtitle == 'retail' or retailyear == 'retail':
                    self.log_debug(
                        "%s - Release ignoriert (Retail-Release bereits gefunden)" % post.title)
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
                        self.log_debug(
                            "%s - Release ignoriert (falsche Aufloesung)" % post.title)
                        continue
                else:
                    if not self.config.get('crawl3d'):
                        self.log_debug(
                            "%s - Release ignoriert (3D-Suche deaktiviert)" % post.title)
                        return
                    if self.config.get('crawl3d') and ("1080p" in post.title.lower() or "1080i" in post.title.lower()):
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

                download_pages = self.get_download_links(content)

                if post_imdb:
                    download_imdb = "http://www.imdb.com/title/" + post_imdb[0]
                else:
                    download_imdb = ""
                    try:
                        search_title = \
                            re.findall(r"(.*?)(?:\.(?:(?:19|20)\d{2})|\.German|\.\d{3,4}p|\.S(?:\d{1,3})\.)",
                                       post.title)[
                                0].replace(
                                ".", "+").replace("ae", u"ä").replace("oe", u"ö").replace("ue", u"ü").replace("Ae",
                                                                                                              u"Ä").replace(
                                "Oe", u"Ö").replace("Ue", u"Ü")
                    except:
                        break
                    search_url = "http://www.imdb.com/find?q=" + search_title
                    search_page = get_url(search_url, self.configfile, self.dbfile)
                    search_results = re.findall(
                        r'<td class="result_text"> <a href="\/title\/(tt[0-9]{7,9})\/\?ref_=fn_al_tt_\d" >(.*?)<\/a>.*? \((\d{4})\)..(.{9})',
                        search_page)
                    no_series = False
                    total_results = len(search_results)
                    if total_results == 0:
                        download_imdb = ""
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
                                    download_imdb = "http://www.imdb.com/title/" + \
                                                    search_results[attempt][0]
                                    title_year = search_results[attempt][2]
                                    total_results = 0
                                    break
                        if no_series is False:
                            self.log_debug(
                                "%s - Keine passende Film-IMDB-Seite gefunden" % post.title)

                details = ""
                min_year = self.config.get("imdbyear")
                if min_year:
                    if len(title_year) > 0:
                        if title_year < min_year:
                            self.log_debug(
                                "%s - Release ignoriert (Film zu alt)" % post.title)
                            continue
                    elif len(download_imdb) > 0:
                        details = get_url(download_imdb, self.configfile, self.dbfile)
                        if not details:
                            self.log_debug(
                                "%s - Fehler bei Aufruf der IMDB-Seite" % post.title)
                            continue
                        title_year = re.findall(
                            r"<title>(?:.*) \(((?:19|20)\d{2})\) - IMDb<\/title>", details)
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
                if len(download_imdb) > 0:
                    if len(details) == 0:
                        details = get_url(download_imdb, self.configfile, self.dbfile)
                    if not details:
                        self.log_debug(
                            "%s - Release ignoriert (Film zu alt)" % post.title)
                        continue
                    vote_count = re.findall(
                        r'ratingCount">(.*?)<\/span>', details)
                    if not vote_count:
                        self.log_debug(
                            "%s - Wertungsanzahl nicht ermittelbar" % post.title)
                        continue
                    else:
                        vote_count = int(vote_count[0].replace(
                            ".", "").replace(",", ""))
                    if vote_count < 1500:
                        self.log_debug(
                            post.title + " - Release ignoriert (Weniger als 1500 IMDB-Votes: " + str(vote_count) + ")")
                        continue
                    download_score = re.findall(
                        r'ratingValue">(.*?)<\/span>', details)
                    download_score = float(download_score[0].replace(
                        ",", "."))
                    if download_score > imdb:
                        if '.3d.' not in post.title.lower():
                            found = self.imdb_download(
                                post.title, download_pages, str(download_score), download_imdb, details)
                        else:
                            found = self.imdb_download(
                                post.title, download_pages, str(download_score), download_imdb, details)
                        for i in found:
                            added_items.append(i)
        return added_items

    def feed_search(self, feed, site):
        if self.empty_list:
            return
        ignore = "|".join(
            [r"\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if self.config.get(
            "ignore") else r"^unmatchable$"

        for key in self.allInfos:
            s = re.sub(self.SUBSTITUTE, ".", "^" + key).lower()
            settings = str(self.settings)
            liste = str(self.allInfos)
            for post in feed.entries:
                concat = post.title + post.published + \
                         settings + liste
                sha = hashlib.sha256(concat.encode(
                    'ascii', 'ignore')).hexdigest()
                if ("MB" in site and sha == self.last_sha_mb) or ("HW" in site and sha == self.last_sha_hw):
                    if not self.historical:
                        self.log_debug(
                            site + "-Feed ab hier bereits gecrawlt (" + post.title + ") " + "- breche Suche nach '" + key + "' ab!")
                        if "MB" in site:
                            self.mb_done = True
                        elif "HW" in site:
                            self.hw_done = True
                        break

                found = re.search(s, post.title.lower())
                if found:
                    content = post.content[0].value
                    if re.search(r'.*([mM][kK][vV]).*', content):
                        found = re.search(ignore, post.title.lower())
                        if found:
                            self.log_debug(
                                "%s - Release ignoriert (basierend auf ignore-Einstellung)" % post.title)
                            continue
                        if self.rsscrawler.get("surround"):
                            if not re.match(r'.*\.(DTS|DD\+*51|DD\+*71|AC3\.5\.*1)\..*', post.title):
                                self.log_debug(
                                    post.title + " - Release ignoriert (kein Mehrkanalton)")
                                continue
                        ss = self.allInfos[key][0].lower()
                        if self.filename == 'MB_Filme':
                            if ss == "480p":
                                if "720p" in post.title.lower() or "1080p" in post.title.lower() or "1080i" in post.title.lower() or "2160p" in post.title.lower():
                                    continue
                                found = True
                            else:
                                found = re.search(ss, post.title.lower())
                            if found:
                                sss = r"[\.-]+" + self.allInfos[key][1].lower()
                                found = re.search(sss, post.title.lower())
                                if self.allInfos[key][2]:
                                    found = all([word in post.title.lower()
                                                 for word in self.allInfos[key][2]])
                                if found:
                                    episode = re.search(
                                        r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', post.title.lower())
                                    if episode:
                                        self.log_debug(
                                            "%s - Release ignoriert (Serienepisode)" % post.title)
                                        continue
                                    yield (post.title, content, key)
                        elif self.filename == 'MB_3D':
                            if '.3d.' in post.title.lower():
                                if self.config.get('crawl3d') and (
                                        "1080p" in post.title.lower() or "1080i" in post.title.lower()):
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
                                sss = r"[\.-]+" + self.allInfos[key][1].lower()
                                found = re.search(sss, post.title.lower())
                                if self.allInfos[key][2]:
                                    found = all([word in post.title.lower()
                                                 for word in self.allInfos[key][2]])
                                if found:
                                    episode = re.search(
                                        r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', post.title.lower())
                                    if episode:
                                        self.log_debug(
                                            "%s - Release ignoriert (Serienepisode)" % post.title)
                                        continue
                                    yield (post.title, content, key)

                        elif self.filename == 'MB_Staffeln':
                            validsource = re.search(self.config.get(
                                "seasonssource"), post.title.lower())
                            if not validsource:
                                self.log_debug(
                                    post.title + " - Release hat falsche Quelle")
                                continue
                            if ".complete." not in post.title.lower():
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
                            ss = self.allInfos[key][0].lower()

                            if ss == "480p":
                                if "720p" in post.title.lower() or "1080p" in post.title.lower() or "1080i" in post.title.lower() or "2160p" in post.title.lower():
                                    continue
                                found = True
                            else:
                                found = re.search(ss, post.title.lower())
                            if found:
                                sss = r"[\.-]+" + self.allInfos[key][1].lower()
                                found = re.search(sss, post.title.lower())

                                if self.allInfos[key][2]:
                                    found = all([word in post.title.lower()
                                                 for word in self.allInfos[key][2]])
                                if found:
                                    episode = re.search(
                                        r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', post.title.lower())
                                    if episode:
                                        self.log_debug(
                                            "%s - Release ignoriert (Serienepisode)" % post.title)
                                        continue
                                    yield (post.title, content, key)
                        else:
                            yield (post.title, content, key)

    def dual_download(self, title):
        search_title = fullhd_title(title).split('.x264-', 1)[0].split('.h264-', 1)[0].replace(".", " ").replace(" ",
                                                                                                                 "+")
        search_url = decode_base64("aHR0cDovL21vdmllLWJsb2cudG8vc2VhcmNoLw==") + search_title + "/feed/rss2/"
        feedsearch_title = fullhd_title(title).split('.x264-', 1)[0].split('.h264-', 1)[0]
        if '.dl.' not in feedsearch_title.lower():
            self.log_debug(
                "%s - Release ignoriert (nicht zweisprachig, da wahrscheinlich nicht Retail)" % feedsearch_title)
            return False
        for (key, value, pattern) in self.dual_search(
                feedparser.parse(get_url(search_url, self.configfile, self.dbfile)),
                feedsearch_title):
            download_links = self.get_download_links(value)
            if download_links:
                for download_link in download_links:
                    if decode_base64("bW92aWUtYmxvZy50by8=") in download_link:
                        self.log_debug("Fake-Link erkannt!")
                        break
                if str(self.db.retrieve(key)) == 'added' or str(self.db.retrieve(key)) == 'dl' or str(
                        self.db.retrieve(key.replace(".COMPLETE", "").replace(".Complete", ""))) == 'added':
                    self.log_debug(
                        "%s - zweisprachiges Release ignoriert (bereits gefunden)" % key)
                    return True
                elif self.filename == 'MB_Filme' or 'IMDB':
                    retail = False
                    if self.config.get('cutoff'):
                        if self.config.get('enforcedl'):
                            if cutoff(key, '1', self.dbfile):
                                retail = True
                        else:
                            if cutoff(key, '0', self.dbfile):
                                retail = True
                    if myjd_download(self.configfile, self.device, key, "RSScrawler/Remux", download_links, ""):
                        self.db.store(
                            key,
                            'dl' if self.config.get(
                                'enforcedl') and '.dl.' in key.lower() else 'added'
                        )
                        log_entry = '[Film] - <b>' + (
                            'Retail/' if retail else "") + 'Zweisprachig</b> - ' + key
                        self.log_info(log_entry)
                        return log_entry
                elif self.filename == 'MB_3D':
                    retail = False
                    if self.config.get('cutoff'):
                        if cutoff(key, '2', self.dbfile):
                            retail = True
                    if myjd_download(self.configfile, self.device, key, "RSScrawler/3Dcrawler", download_links, ""):
                        self.db.store(
                            key,
                            'dl' if self.config.get(
                                'enforcedl') and '.dl.' in key.lower() else 'added'
                        )
                        log_entry = '[Film] - <b>' + (
                            'Retail/' if retail else "") + '3D/Zweisprachig</b> - ' + key
                        self.log_info(log_entry)
                        return log_entry
                elif self.filename == 'MB_Regex':
                    if myjd_download(self.configfile, self.device, key, "RSScrawler/Remux", download_links, ""):
                        self.db.store(
                            key,
                            'dl' if self.config.get(
                                'enforcedl') and '.dl.' in key.lower() else 'added'
                        )
                        log_entry = '[Film/Serie/RegEx] - <b>Zweisprachig</b> - ' + key
                        self.log_info(log_entry)
                        return log_entry
                else:
                    if myjd_download(self.configfile, self.device, key, "RSScrawler/Remux", download_links, ""):
                        self.db.store(
                            key,
                            'dl' if self.config.get(
                                'enforcedl') and '.dl.' in key.lower() else 'added'
                        )
                        log_entry = '[Staffel] - <b>Zweisprachig</b> - ' + key
                        self.log_info(log_entry)
                        return log_entry

    def imdb_download(self, key, download_links, score, download_imdb, details):
        if download_links:
            added_items = []
            for download_link in download_links:
                url = decode_base64("bW92aWUtYmxvZy50by8=")
                if url in download_link:
                    self.log_debug("Fake-Link erkannt!")
                    break
            englisch = False
            if "*englisch*" in key.lower():
                key = key.replace(
                    '*ENGLISCH*', '').replace("*Englisch*", "")
                englisch = True
                if not self.rsscrawler.get('english'):
                    self.log_debug(
                        "%s - Englische Releases deaktiviert" % key)
                    return
            if self.config.get('enforcedl') and '.dl.' not in key.lower():
                original_language = ""
                if len(details) > 0:
                    original_language = re.findall(
                        r"Language:<\/h4>\n.*?\n.*?url'>(.*?)<\/a>", details)
                    if original_language:
                        original_language = original_language[0]
                    else:
                        self.log_debug(
                            "%s - Originalsprache nicht ermittelbar" % key)
                elif len(download_imdb) > 0:
                    details = get_url(download_imdb, self.configfile, self.dbfile)
                    if not details:
                        self.log_debug(
                            "%s - Originalsprache nicht ermittelbar" % key)
                    original_language = re.findall(
                        r"Language:<\/h4>\n.*?\n.*?url'>(.*?)<\/a>", details)
                    if original_language:
                        original_language = original_language[0]
                    else:
                        self.log_debug(
                            "%s - Originalsprache nicht ermittelbar" % key)

                if original_language == "German":
                    self.log_debug(
                        "%s - Originalsprache ist Deutsch. Breche Suche nach zweisprachigem Release ab!" % key)
                else:
                    dual_found = self.dual_download(key)
                    if dual_found:
                        added_items.append(dual_found)
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
                            if cutoff(key, '1', self.dbfile):
                                retail = True
                        else:
                            if cutoff(key, '0', self.dbfile):
                                retail = True
                if myjd_download(self.configfile, self.device, key, "RSScrawler", download_links, ""):
                    self.db.store(
                        key,
                        'notdl' if self.config.get(
                            'enforcedl') and '.dl.' not in key.lower() else 'added'
                    )
                    log_entry = '[IMDB ' + score + '/Film] - ' + (
                        '<b>Englisch</b> - ' if englisch and not retail else "") + (
                                    '<b>Englisch/Retail</b> - ' if englisch and retail else "") + (
                                    '<b>Retail</b> - ' if not englisch and retail else "") + key
                    self.log_info(log_entry)
                    added_items.append(log_entry)
            else:
                retail = False
                if (self.config.get('enforcedl') and '.dl.' in key.lower()) or not self.config.get(
                        'enforcedl'):
                    if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                        if self.config.get('enforcedl'):
                            if cutoff(key, '2', self.dbfile):
                                retail = True
                if myjd_download(self.configfile, self.device, key, "RSScrawler/3Dcrawler", download_links, ""):
                    self.db.store(
                        key,
                        'notdl' if self.config.get(
                            'enforcedl') and '.dl.' not in key.lower() else 'added'
                    )
                    log_entry = '[IMDB ' + score + '/Film] - <b>' + (
                        'Retail/' if retail else "") + '3D</b> - ' + key
                    self.log_info(log_entry)
                    added_items.append(log_entry)
            return added_items

    def feed_download(self, key, content):
        download_links = self.get_download_links(content)
        if download_links:
            added_items = []
            for download_link in download_links:
                url = decode_base64("bW92aWUtYmxvZy50by8=")
                if url in download_link:
                    self.log_debug("Fake-Link erkannt!")
                    break
            replaced = retail_sub(key)
            retailtitle = self.db_retail.retrieve(replaced[0])
            retailyear = self.db_retail.retrieve(replaced[1])
            if str(self.db.retrieve(key)) == 'added' or str(self.db.retrieve(key)) == 'notdl' or str(
                    self.db.retrieve(key.replace(".COMPLETE", "").replace(".Complete", ""))) == 'added':
                self.log_debug(
                    "%s - Release ignoriert (bereits gefunden)" % key)
                return
            elif retailtitle == 'retail' or retailyear == 'retail':
                self.log_debug(
                    "%s - Release ignoriert (Retail-Release bereits gefunden)" % key)
                return
            englisch = False
            if "*englisch*" in key.lower():
                key = key.replace(
                    '*ENGLISCH*', '').replace("*Englisch*", "")
                englisch = True
                if not self.rsscrawler.get('english'):
                    self.log_debug(
                        "%s - Englische Releases deaktiviert" % key)
                    return
            if self.config.get('enforcedl') and '.dl.' not in key.lower():
                imdb_id = re.findall(
                    r'.*?(?:href=.?http(?:|s):\/\/(?:|www\.)imdb\.com\/title\/(tt[0-9]{7,9}).*?).*?(\d(?:\.|\,)\d)(?:.|.*?)<\/a>.*?',
                    content)

                if imdb_id:
                    imdb_id = imdb_id[0][0]
                else:
                    search_title = re.findall(
                        r"(.*?)(?:\.(?:(?:19|20)\d{2})|\.German|\.\d{3,4}p|\.S(?:\d{1,3})\.)", key)[0].replace(".", "+")
                    search_url = "http://www.imdb.com/find?q=" + search_title
                    search_page = get_url(search_url, self.configfile, self.dbfile)
                    search_results = re.findall(
                        r'<td class="result_text"> <a href="\/title\/(tt[0-9]{7,9})\/\?ref_=fn_al_tt_\d" >(.*?)<\/a>.*? \((\d{4})\)..(.{9})',
                        search_page)
                    total_results = len(search_results)
                    if self.filename == 'MB_Staffeln':
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
                            self.log_debug(
                                "%s - Keine passende Film-IMDB-Seite gefunden" % key)
                if not imdb_id:
                    dual_found = self.dual_download(key)
                    if dual_found:
                        added_items.append(dual_found)
                    else:
                        self.log_debug(
                            "%s - Kein zweisprachiges Release gefunden." % key)
                        self.dl_unsatisfied = True
                else:
                    if isinstance(imdb_id, list):
                        imdb_id = imdb_id.pop()
                    imdb_url = "http://www.imdb.com/title/" + imdb_id
                    details = get_url(imdb_url, self.configfile, self.dbfile)
                    if not details:
                        self.log_debug(
                            "%s - Originalsprache nicht ermittelbar" % key)
                    original_language = re.findall(
                        r"Language:<\/h4>\n.*?\n.*?url'>(.*?)<\/a>", details)
                    if original_language:
                        original_language = original_language[0]
                    if original_language == "German":
                        self.log_debug(
                            "%s - Originalsprache ist Deutsch. Breche Suche nach zweisprachigem Release ab!" % key)
                    else:
                        dual_found = self.dual_download(key)
                        if dual_found:
                            added_items.append(dual_found)
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
                            if cutoff(key, '1', self.dbfile):
                                retail = True
                        else:
                            if cutoff(key, '0', self.dbfile):
                                retail = True
                else:
                    if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                        if cutoff(key, '0', self.dbfile):
                            retail = True
                if myjd_download(self.configfile, self.device, key, "RSScrawler", download_links, ""):
                    self.db.store(
                        key,
                        'notdl' if self.config.get(
                            'enforcedl') and '.dl.' not in key.lower() else 'added'
                    )
                    log_entry = '[Film] - ' + ('<b>Englisch</b> - ' if englisch and not retail else "") + (
                        '<b>Englisch/Retail</b> - ' if englisch and retail else "") + (
                                    '<b>Retail</b> - ' if not englisch and retail else "") + key
                    self.log_info(log_entry)
                    added_items.append(log_entry)
            elif self.filename == 'MB_3D':
                retail = False
                if (self.config.get('enforcedl') and '.dl.' in key.lower()) or not self.config.get(
                        'enforcedl'):
                    if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                        if self.config.get('enforcedl'):
                            if cutoff(key, '2', self.dbfile):
                                retail = True
                else:
                    if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                        if cutoff(key, '2', self.dbfile):
                            retail = True
                if myjd_download(self.configfile, self.device, key, "RSScrawler/3Dcrawler", download_links, ""):
                    self.db.store(
                        key,
                        'notdl' if self.config.get(
                            'enforcedl') and '.dl.' not in key.lower() else 'added'
                    )
                    log_entry = '[Film] - <b>' + (
                        'Retail/' if retail else "") + '3D</b> - ' + key
                    self.log_info(log_entry)
                    added_items.append(log_entry)
            elif self.filename == 'MB_Staffeln':
                if myjd_download(self.configfile, self.device, key, "RSScrawler", download_links, ""):
                    self.db.store(
                        key.replace(".COMPLETE", "").replace(
                            ".Complete", ""),
                        'notdl' if self.config.get(
                            'enforcedl') and '.dl.' not in key.lower() else 'added'
                    )
                    log_entry = '[Staffel] - ' + key.replace(".COMPLETE", "").replace(".Complete", "")
                    self.log_info(log_entry)
                    added_items.append(log_entry)
            else:
                if myjd_download(self.configfile, self.device, key, "RSScrawler", download_links, ""):
                    self.db.store(
                        key,
                        'notdl' if self.config.get(
                            'enforcedl') and '.dl.' not in key.lower() else 'added'
                    )
                    log_entry = '[Film/Serie/RegEx] - ' + key
                    self.log_info(log_entry)
                    added_items.append(log_entry)
            return added_items

    def periodical_task(self):
        imdb = self.imdb
        mb_urls = []
        hw_urls = []

        if self.filename == 'MB_Staffeln':
            if not self.config.get('crawlseasons'):
                return
            self.allInfos = dict(
                set({key: value for (key, value) in self.get_patterns(
                    self.read_input(self.filename),
                    quality=self.config.get('seasonsquality'), rg='.*', sf='.complete.'
                ).items()}.items()
                    )
            )
        elif self.filename == 'MB_Regex':
            if not self.config.get('regex'):
                return
            self.allInfos = dict(
                set({key: value for (key, value) in self.get_patterns(
                    self.read_input(self.filename)
                ).items()}.items()
                    ) if self.config.get('regex') else []
            )
        elif self.filename == "IMDB":
            self.allInfos = self.filename
        else:
            if self.filename == 'MB_3D':
                if not self.config.get('crawl3d'):
                    return
            self.allInfos = dict(
                set({key: value for (key, value) in self.get_patterns(
                    self.read_input(self.filename), quality=self.config.get('quality'), rg='.*', sf=None
                ).items()}.items()
                    )
            )
        if self.filename != 'MB_Regex' and self.filename != 'IMDB':
            if self.historical:
                for xline in self.allInfos.keys():
                    if len(xline) > 0 and not xline.startswith("#"):
                        xn = xline.split(",")[0].replace(
                            ".", " ").replace(" ", "+")
                        mb_urls.append(
                            decode_base64('aHR0cDovL21vdmllLWJsb2cudG8=') + '/search/%s/feed/rss2/' % xn)
                        hw_urls.append(decode_base64('aHR0cDovL2hkLXdvcmxkLm9yZw==') + '/search/%s/feed/rss2/' % xn)
            else:
                for URL in self.MB_FEED_URLS:
                    mb_urls.append(URL)
                for URL in self.HW_FEED_URLS:
                    hw_urls.append(URL)
        else:
            for URL in self.MB_FEED_URLS:
                mb_urls.append(URL)
            for URL in self.HW_FEED_URLS:
                hw_urls.append(URL)

        if self.filename != 'IMDB':
            if self.empty_list:
                self.log_debug(
                    "Liste ist leer. Stoppe Suche für Filme! (" + self.filename + ")")
                return
        elif imdb == 0:
            self.log_debug(
                "IMDB-Suchwert ist 0. Stoppe Suche für Filme! (" + self.filename + ")")
            return

        mb_304 = False
        hw_304 = False

        try:
            first_mb = get_url_headers(mb_urls[0], self.configfile, self.dbfile, self.headers_mb)
            first_page_mb = feedparser.parse(first_mb.content)
        except:
            mb_304 = True
            self.log_error("Fehler beim Abruf von MB - breche Suche ab!")

        try:
            first_hw = get_url_headers(hw_urls[0], self.configfile, self.dbfile, self.headers_hw)
            first_page_hw = feedparser.parse(first_hw.content)
        except:
            hw_304 = True
            self.log_error("Fehler beim Abruf von HW - breche Suche ab!")

        if not mb_304:
            set_mbhw = str(self.settings) + str(self.allInfos)
            set_mbhw = hashlib.sha256(set_mbhw.encode('ascii', 'ignore')).hexdigest()
            if self.last_set_mbhw == set_mbhw:
                if first_mb.status_code == 304:
                    mb_304 = True
                    mb_urls = []
                    self.log_debug("MB-Feed seit letztem Aufruf nicht aktualisiert - breche Suche ab!")

        if not hw_304:
            set_mbhw = str(self.settings) + str(self.allInfos)
            set_mbhw = hashlib.sha256(set_mbhw.encode('ascii', 'ignore')).hexdigest()
            if self.last_set_mbhw == set_mbhw:
                if first_hw.status_code == 304:
                    hw_304 = True
                    hw_urls = []
                    self.log_debug("HW-Feed seit letztem Aufruf nicht aktualisiert - breche Suche ab!")

        if mb_304 and hw_304:
            return

        sha_mb = None
        sha_hw = None

        if not self.historical:
            if self.filename != 'IMDB':
                if not mb_304:
                    for i in first_page_mb.entries:
                        concat_mb = i.title + i.published + \
                                    str(self.settings) + str(self.allInfos)
                        sha_mb = hashlib.sha256(concat_mb.encode(
                            'ascii', 'ignore')).hexdigest()
                        break
                if not hw_304:
                    for i in first_page_mb.entries:
                        concat_hw = i.title + i.published + \
                                    str(self.settings) + str(self.allInfos)
                        sha_hw = hashlib.sha256(concat_hw.encode(
                            'ascii', 'ignore')).hexdigest()
                        break
            else:
                if not mb_304:
                    for i in first_page_mb.entries:
                        concat_mb = i.title + i.published + \
                                    str(self.settings) + str(self.imdb)
                        sha_mb = hashlib.sha256(concat_mb.encode(
                            'ascii', 'ignore')).hexdigest()
                        break
                if not hw_304:
                    for i in first_page_mb.entries:
                        concat_hw = i.title + i.published + \
                                    str(self.settings) + str(self.imdb)
                        sha_hw = hashlib.sha256(concat_hw.encode(
                            'ascii', 'ignore')).hexdigest()
                        break

                if not hw_304:
                    try:
                        first_post_hw = first_page_hw.entries[0]
                        concat_hw = first_post_hw.title + first_post_hw.published + str(self.settings) + str(self.imdb)
                        sha_hw = hashlib.sha256(concat_hw.encode(
                            'ascii', 'ignore')).hexdigest()
                    except:
                        sha_hw = None

        added_items = []
        if self.filename == "IMDB":
            if imdb > 0:
                i = 0
                for url in mb_urls:
                    if not self.i_mb_done:
                        if i == 0:
                            mb_parsed_url = first_page_mb
                        else:
                            mb_parsed_url = feedparser.parse(get_url(url, self.configfile, self.dbfile))
                        found = self.imdb_search(imdb, mb_parsed_url, "MB")
                        if found:
                            for f in found:
                                added_items.append(f)
                        i += 1
                i = 0
                for url in hw_urls:
                    if not self.i_hw_done:
                        if i == 0:
                            hw_parsed_url = first_page_hw
                        else:
                            hw_parsed_url = feedparser.parse(get_url(url, self.configfile, self.dbfile))
                        found = self.imdb_search(imdb, hw_parsed_url, "HW")
                        if found:
                            for f in found:
                                added_items.append(f)
                        i += 1
        else:
            i = 0
            for url in mb_urls:
                if not self.mb_done:
                    if i == 0:
                        mb_parsed_url = first_page_mb
                    else:
                        mb_parsed_url = feedparser.parse(get_url(url, self.configfile, self.dbfile))
                    for (key, value, pattern) in self.feed_search(mb_parsed_url, "MB"):
                        found = self.feed_download(key, value)
                        if found:
                            for f in found:
                                added_items.append(f)
                    i += 1
            i = 0
            for url in hw_urls:
                if not self.hw_done:
                    if i == 0:
                        hw_parsed_url = first_page_hw
                    else:
                        hw_parsed_url = feedparser.parse(get_url(url, self.configfile, self.dbfile))
                    for (key, value, pattern) in self.feed_search(hw_parsed_url, "HW"):
                        found = self.feed_download(key, value)
                        if found:
                            for f in found:
                                added_items.append(f)
                    i += 1

        self.cdc.delete("MBHWSet-" + self.filename)
        self.cdc.store("MBHWSet-" + self.filename, set_mbhw)
        if sha_mb:
            if not self.dl_unsatisfied:
                self.cdc.delete("MB-" + self.filename)
                self.cdc.store("MB-" + self.filename, sha_mb)
            else:
                self.log_debug(
                    "Für ein oder mehrere Release(s) wurde kein zweisprachiges gefunden. Setze kein neues MB-CDC!")
        if sha_hw:
            if not self.dl_unsatisfied:
                self.cdc.delete("HW-" + self.filename)
                self.cdc.store("HW-" + self.filename, sha_hw)
            else:
                self.log_debug(
                    "Für ein oder mehrere Release(s) wurde kein zweisprachiges gefunden. Setze kein neues HW-CDC!")
        if not mb_304:
            self.cdc.delete("MBHeaders-" + self.filename)
            self.cdc.store("MBHeaders-" + self.filename, first_mb.headers['Last-Modified'])
        if not hw_304:
            self.cdc.delete("HWHeaders-" + self.filename)
            self.cdc.store("HWHeaders-" + self.filename, first_hw.headers['Last-Modified'])

        return added_items
