# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul durchsucht die Feeds aller Seiten des Typs content_all auf Basis einer standardisierten Struktur.

import hashlib
import re

from imdb import Cinemagoer as IMDb

from feedcrawler import internal
from feedcrawler.common import check_is_site
from feedcrawler.common import check_valid_release
from feedcrawler.common import fullhd_title
from feedcrawler.common import is_hevc
from feedcrawler.common import is_retail
from feedcrawler.db import ListDb
from feedcrawler.imdb import clean_imdb_id
from feedcrawler.imdb import get_imdb_id
from feedcrawler.imdb import get_original_language
from feedcrawler.myjd import myjd_download
from feedcrawler.notifiers import notify
from feedcrawler.sites.shared.internal_feed import add_decrypt_instead_of_download
from feedcrawler.sites.shared.internal_feed import by_page_download_link
from feedcrawler.sites.shared.internal_feed import fx_get_download_links
from feedcrawler.sites.shared.internal_feed import get_search_results
from feedcrawler.sites.shared.internal_feed import hw_get_download_links
from feedcrawler.sites.shared.internal_feed import nk_page_download_link
from feedcrawler.url import get_url


def get_movies_list(liste):
    cont = ListDb(liste).retrieve()
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
        self.settings.append(self.feedcrawler.get("english"))
        self.settings.append(self.feedcrawler.get("surround"))
        self.settings.append(self.hosters)
        for s in settings:
            self.settings.append(self.config.get(s))
        if self.filename == "IMDB":
            self.pattern = self.filename
        else:
            liste = get_movies_list(self.filename)
            self.pattern = r'(' + "|".join(liste).lower() + ').*'
    settings = str(self.settings) + str(self.pattern)
    return hashlib.sha256(settings.encode('ascii', 'ignore')).hexdigest()


def check_fallback_required(download_links):
    if download_links and len(download_links) == 1 and download_links[0]:
        return True
    else:
        return False


def search_imdb(self, desired_rating, feed):
    added_items = []
    settings = str(self.settings)
    score = str(self.imdb)
    for post in feed.entries:
        try:
            content = post.content[0].value
        except:
            internal.logger.debug("Fehler beim Abruf von " + post.title + ": Kein Durchsuchbarer Inhalt gefunden.")
            content = False
        if content:
            post.title = post.title.strip(u'\u200b')

        if self.search_imdb_done:
            internal.logger.debug(
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
                    internal.logger.debug(
                        "%s - Release ignoriert (bereits gefunden)" % post.title)
                    continue
                elif not check_valid_release(post.title, self.retail_only, self.hevc_retail):
                    internal.logger.debug(
                        "%s - Release ignoriert (Gleiche oder bessere Quelle bereits vorhanden)" % post.title)
                    continue
                quality_set = self.config.get('quality')
                if '.3d.' in post.title.lower():
                    internal.logger.debug(
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
                                    internal.logger.debug(
                                        "%s - Qualität ignoriert (Release ist 1080p-HEVC-Retail)" % post.title)
                                    hevc_retail = True
                                    quality_match = True
                    if not quality_match:
                        internal.logger.debug(
                            "%s - Release ignoriert (falsche Auflösung)" % post.title)
                        continue

                ignore = "|".join(
                    [r"\.%s(\.|-)" % p for p in self.config.get("ignore").lower().split(',')]) if self.config.get(
                    "ignore") else r"^unmatchable$"
                found = re.search(ignore, post.title.lower())
                if found:
                    if self.hevc_retail:
                        if is_hevc(post.title) and "1080p" in post.title:
                            if is_retail(post.title, False):
                                internal.logger.debug(
                                    "%s - Filterliste ignoriert (Release ist 1080p-HEVC-Retail)" % post.title)
                                hevc_retail = True
                                found = False
                if found:
                    internal.logger.debug(
                        "%s - Release ignoriert (basierend auf ignore-Einstellung)" % post.title)
                    continue
                if self.feedcrawler.get("surround"):
                    if not re.match(r'.*\.(DTS|DD\+*51|DD\+*71|AC3\.5\.*1)\..*', post.title):
                        internal.logger.debug(
                            post.title + " - Release ignoriert (kein Mehrkanalton)")
                        continue
                season = re.search(r'\.S(\d{1,3})(\.|-|E)', post.title)
                if season:
                    internal.logger.debug(
                        "%s - Release ignoriert (IMDb sucht nur Filme)" % post.title)
                    continue

                imdb_data = False
                if post_imdb:
                    imdb_id = clean_imdb_id(post_imdb[0])
                    imdb_data = IMDb().get_movie(imdb_id)
                else:
                    try:
                        search_title = \
                            re.findall(r"(.*?)(?:\.(?:(?:19|20)\d{2})|\.German|\.\d{3,4}p|\.S(?:\d{1,3})\.)",
                                       post.title)[
                                0].replace(".", " ").replace("ae", u"ä").replace("oe", u"ö").replace("ue",
                                                                                                     u"ü").replace(
                                "Ae", u"Ä").replace("Oe", u"Ö").replace("Ue", u"Ü")
                        ia = IMDb()
                        results = ia.search_movie(search_title)
                    except:
                        results = False
                    if not results:
                        internal.logger.debug(
                            "%s - Keine passende Film-IMDb-Seite gefunden" % post.title)
                    else:
                        imdb_data = IMDb().get_movie(results[0].movieID)
                if imdb_data:
                    min_year = int(self.config.get("imdbyear"))
                    if min_year:
                        try:
                            if int(imdb_data.data["year"]) < min_year:
                                internal.logger.debug(
                                    "%s - Release ignoriert (Film zu alt)" % post.title)
                                continue
                        except:
                            internal.logger.debug("%s - Release ignoriert (Alter nicht ermittelbar)" % post.title)
                            continue
                    try:
                        if int("".join(re.findall('\d+', str(imdb_data.data["votes"])))) < 1500:
                            internal.logger.debug(
                                post.title + " - Release ignoriert (Weniger als 1500 IMDb-Votes)")
                            continue
                    except KeyError:
                        internal.logger.debug(
                            post.title + " - Release ignoriert (Konnte keine IMDb-Votes finden)")
                        continue
                    if float(str(imdb_data.data["rating"]).replace(",", ".")) > desired_rating:
                        download_links = False
                        if not download_links:
                            site = self._SITE
                            download_method = self.download_method
                            download_links = self.get_download_links_method(self, content, post.title)
                            if check_fallback_required(download_links):
                                download_method = add_decrypt_instead_of_download
                        found = download_imdb(self,
                                              post.title, download_links,
                                              str(imdb_data.data["rating"]).replace(",", "."),
                                              imdb_data.movieID, hevc_retail, site, download_method)
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
            internal.logger.debug("Fehler beim Abruf von " + post.title + ": Kein Durchsuchbarer Inhalt gefunden.")
            content = False
        if content:
            post.title = post.title.strip(u'\u200b')

        if self.search_regular_done:
            internal.logger.debug(
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
                                    internal.logger.debug(
                                        "%s - Filterliste ignoriert (Release ist 1080p-HEVC-Retail)" % post.title)
                                    hevc_retail = True
                                    found = False
                    if found:
                        internal.logger.debug(
                            "%s - Release ignoriert (basierend auf ignore-Einstellung)" % post.title)
                        continue
                    if self.feedcrawler.get("surround"):
                        if not re.match(r'.*\.(DTS|DD\+*51|DD\+*71|AC3\.5\.*1)\..*', post.title):
                            internal.logger.debug(
                                post.title + " - Release ignoriert (kein Mehrkanalton)")
                            continue
                    if self.filename == 'List_ContentAll_Seasons':
                        ss = self.config.get('seasonsquality')
                    elif 'Regex' not in self.filename:
                        ss = self.config.get('quality')
                    else:
                        ss = False
                    if self.filename == 'List_ContentAll_Movies':
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
                                        internal.logger.debug(
                                            "%s  - Qualität ignoriert (Release ist 1080p-HEVC-Retail)" % post.title)
                                        hevc_retail = True
                                        found = True
                        if found:
                            episode = re.search(
                                r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', post.title.lower())
                            if episode:
                                internal.logger.debug(
                                    "%s - Release ignoriert (Serienepisode)" % post.title)
                                continue
                            found = download_feed(self, post.title, content, hevc_retail)
                            if found:
                                for i in found:
                                    added_items.append(i)
                    elif self.filename == 'List_ContentAll_Seasons':
                        validsource = re.search(self.config.get(
                            "seasonssource"), post.title.lower())
                        if not validsource:
                            internal.logger.debug(
                                post.title + " - Release hat falsche Quelle")
                            continue
                        if ".complete." not in post.title.lower():
                            if "FX" not in self._SITE:
                                internal.logger.debug(
                                    post.title + " - Staffel noch nicht komplett")
                                continue
                        season = re.search(r"\.s\d", post.title.lower())
                        if not season:
                            internal.logger.debug(
                                post.title + " - Release ist keine Staffel")
                            continue
                        if not self.config.get("seasonpacks"):
                            staffelpack = re.search(
                                r"s\d.*(-|\.).*s\d", post.title.lower())
                            if staffelpack:
                                internal.logger.debug(
                                    "%s - Release ignoriert (Staffelpaket)" % post.title)
                                continue
                        if self.filename == 'List_ContentAll_Seasons':
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
                                internal.logger.debug(
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
    search_results = get_search_results(self, search_title)

    i = 0
    for result in search_results:
        i += 1

        key = result[0].replace(" ", ".")

        if feedsearch_title in key:
            payload = result[1].split("|")
            link = payload[0]
            password = payload[1]

            link_grabbed = False

            site = check_is_site(link)
            if not site:
                continue
            elif "BY" in site:
                get_download_links_method = by_page_download_link
                download_method = myjd_download
            elif "FX" in site:
                link = get_url(link)
                link_grabbed = True
                get_download_links_method = fx_get_download_links
                download_method = add_decrypt_instead_of_download
            elif "HW" in site:
                get_download_links_method = hw_get_download_links
                download_method = add_decrypt_instead_of_download
            elif "NK" in site:
                get_download_links_method = nk_page_download_link
                download_method = myjd_download
            else:
                continue

            if is_hevc(key) and "1080p" in key:
                download_links = get_download_links_method(self, link, key)
                if check_fallback_required(download_links):
                    download_method = add_decrypt_instead_of_download
                if download_links:
                    storage = self.db.retrieve_all(key)
                    storage_replaced = self.db.retrieve_all(key.replace(".COMPLETE", "").replace(".Complete", ""))
                    if 'added' in storage or 'notdl' in storage or 'added' in storage_replaced or 'notdl' in storage_replaced:
                        internal.logger.debug(
                            "%s - HEVC Release ignoriert (bereits gefunden)" % key)
                        return True

                    englisch = False
                    if "*englisch" in key.lower() or "*english" in key.lower():
                        key = key.replace(
                            '*ENGLISCH', '').replace("*Englisch", "").replace("*ENGLISH", "").replace("*English",
                                                                                                      "").replace(
                            "*", "")
                        englisch = True
                        if not self.feedcrawler.get('english'):
                            internal.logger.debug(
                                "%s - Englische Releases deaktiviert" % key)
                            return

                    if self.config.get('enforcedl') and '.dl.' not in key.lower():
                        if not link_grabbed:
                            link = get_url(link)
                        imdb_id = get_imdb_id(key, link, self.filename)
                        if not imdb_id:
                            dual_found = download_dual_language(self, key, True)
                            if dual_found and ".1080p." in key:
                                return
                            elif not dual_found and not englisch:
                                internal.logger.debug(
                                    "%s - Kein zweisprachiges HEVC-Release gefunden." % key)
                                self.dl_unsatisfied = True
                        else:
                            if isinstance(imdb_id, list):
                                imdb_id = imdb_id.pop()
                            if get_original_language(key, imdb_id):
                                dual_found = download_dual_language(self, key, True)
                                if dual_found and ".1080p." in key:
                                    return
                                elif not dual_found and not englisch:
                                    internal.logger.debug(
                                        "%s - Kein zweisprachiges HEVC-Release gefunden! Breche ab." % key)
                                    self.dl_unsatisfied = True
                                    return

                    if self.filename == 'List_ContentAll_Movies' or self.filename == 'IMDB':
                        if self.config.get('cutoff') and is_retail(key, True):
                            retail = True
                        elif is_retail(key, False):
                            retail = True
                        else:
                            retail = False
                        if retail:
                            if download_method(key, "FeedCrawler", download_links, password):
                                self.db.store(
                                    key,
                                    'added'
                                )
                                log_entry = '[Film' + (
                                    '/Retail' if retail else "") + '/HEVC] - ' + key + ' - [' + site + ']'
                                internal.logger.info(log_entry)
                                notify([log_entry])
                                return log_entry
                    elif self.filename == 'List_ContentAll_Movies_Regex':
                        if download_method(key, "FeedCrawler", download_links, password):
                            self.db.store(
                                key,
                                'added'
                            )
                            log_entry = '[Film/Serie/RegEx/HEVC] - ' + key + ' - [' + site + ']'
                            internal.logger.info(log_entry)
                            notify([log_entry])
                            return log_entry
                    else:
                        if download_method(key, "FeedCrawler", download_links, password):
                            self.db.store(
                                key,
                                'added'
                            )
                            log_entry = '[Staffel/HEVC] - ' + key + ' - [' + site + ']'
                            internal.logger.info(log_entry)
                            notify([log_entry])
                            return log_entry
                else:
                    storage = self.db.retrieve_all(key)
                    if 'added' not in storage and 'notdl' not in storage:
                        wrong_hoster = '[' + site + 'HEVC-Suche/Hoster fehlt] - ' + key
                        if 'wrong_hoster' not in storage:
                            print(wrong_hoster)
                            self.db.store(key, 'wrong_hoster')
                            notify([wrong_hoster])
                        else:
                            internal.logger.debug(wrong_hoster)


def download_dual_language(self, title, hevc=False):
    search_title = fullhd_title(title).split('.x264', 1)[0].split('.h264', 1)[0].split('.h265', 1)[0].split('.x265', 1)[
        0].split('.HEVC-', 1)[0].replace(".", " ").replace(" ", "+")
    feedsearch_title = \
        fullhd_title(title).split('.German', 1)[0].split('.x264', 1)[0].split('.h264', 1)[0].split('.h265', 1)[0].split(
            '.x265', 1)[
            0].split('.HEVC-', 1)[0]
    search_results = get_search_results(self, search_title)

    hevc_found = False
    for result in search_results:
        key = result[0].replace(" ", ".")
        if feedsearch_title in key and ".dl." in key.lower() and (hevc and is_hevc(key)):
            hevc_found = True

    i = 0
    for result in search_results:
        i += 1

        key = result[0].replace(" ", ".")

        if feedsearch_title in key:
            payload = result[1].split("|")
            link = payload[0]
            password = payload[1]

            site = check_is_site(link)
            if not site:
                continue
            elif "BY" in site:
                get_download_links_method = by_page_download_link
                download_method = myjd_download
            elif "FX" in site:
                link = get_url(link)
                get_download_links_method = fx_get_download_links
                download_method = add_decrypt_instead_of_download
            elif "HW" in site:
                get_download_links_method = hw_get_download_links
                download_method = add_decrypt_instead_of_download
            elif "NK" in site:
                get_download_links_method = nk_page_download_link
                download_method = myjd_download
            else:
                continue

            if ".dl." not in key.lower():
                internal.logger.debug(
                    "%s - Release ignoriert (nicht zweisprachig)" % key)
                continue
            if hevc and hevc_found and not is_hevc(key):
                internal.logger.debug(
                    "%s - zweisprachiges Release ignoriert (nicht HEVC)" % key)
                continue
            if ".720p." in key.lower():
                path_suffix = "/Remux"
            else:
                path_suffix = ""

            download_links = get_download_links_method(self, link, key)
            if check_fallback_required(download_links):
                download_method = add_decrypt_instead_of_download
            if download_links:
                storage = self.db.retrieve_all(key)
                storage_replaced = self.db.retrieve_all(key.replace(".COMPLETE", "").replace(".Complete", ""))
                if 'added' in storage or 'notdl' in storage or 'added' in storage_replaced or 'notdl' in storage_replaced:
                    internal.logger.debug(
                        "%s - zweisprachiges Release ignoriert (bereits gefunden)" % key)
                    return True
                elif self.filename == 'List_ContentAll_Movies' or self.filename == 'IMDB':
                    retail = False
                    if self.config.get('cutoff'):
                        if is_retail(key, True):
                            retail = True
                    if download_method(key, "FeedCrawler" + path_suffix, download_links, password):
                        self.db.store(
                            key,
                            'added'
                        )
                        log_entry = '[Film' + (
                            '/Retail' if retail else "") + '/Zweisprachig] - ' + key + ' - [' + site + ']'
                        internal.logger.info(log_entry)
                        notify([log_entry])
                        return log_entry
                elif self.filename == 'List_ContentAll_Movies_Regex':
                    if download_method(key, "FeedCrawler" + path_suffix, download_links, password):
                        self.db.store(
                            key,
                            'added'
                        )
                        log_entry = '[Film/Serie/RegEx/Zweisprachig] - ' + key + ' - [' + site + ']'
                        internal.logger.info(log_entry)
                        notify([log_entry])
                        return log_entry
                else:
                    if download_method(key, "FeedCrawler" + path_suffix, download_links, password):
                        self.db.store(
                            key,
                            'added'
                        )
                        log_entry = '[Staffel/Zweisprachig] - ' + key + ' - [' + site + ']'
                        internal.logger.info(log_entry)
                        notify([log_entry])
                        return log_entry
            else:
                storage = self.db.retrieve_all(key)
                if 'added' not in storage and 'notdl' not in storage:
                    wrong_hoster = '[' + site + 'DL-Suche/Hoster fehlt] - ' + key
                    if 'wrong_hoster' not in storage:
                        print(wrong_hoster)
                        self.db.store(key, 'wrong_hoster')
                        notify([wrong_hoster])
                    else:
                        internal.logger.debug(wrong_hoster)


def download_imdb(self, key, download_links, score, imdb_id, hevc_retail, site, download_method):
    key = key.replace(" ", ".")
    added_items = []
    if not hevc_retail:
        if self.hevc_retail:
            if not is_hevc(key) and is_retail(key, False):
                if download_hevc(self, key):
                    internal.logger.debug(
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
            if not self.feedcrawler.get('english'):
                internal.logger.debug(
                    "%s - Englische Releases deaktiviert" % key)
                return
        if self.config.get('enforcedl') and '.dl.' not in key.lower():
            if get_original_language(key, imdb_id):
                dual_found = download_dual_language(self, key, self.password)
                if dual_found:
                    added_items.append(dual_found)
                    if ".1080p." in key:
                        return added_items
                elif not dual_found and not englisch:
                    internal.logger.debug(
                        "%s - Kein zweisprachiges Release gefunden!" % key)
                    return

        if '.3d.' in key.lower():
            internal.logger.debug(
                "%s - Release ignoriert (3D-Film)" % key.title)
            return
        else:
            retail = False
            if (self.config.get('enforcedl') and '.dl.' in key.lower()) or not self.config.get(
                    'enforcedl'):
                if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                    if self.config.get('enforcedl'):
                        if is_retail(key, True):
                            retail = True
            if download_method(key, "FeedCrawler", download_links, self.password):
                self.db.store(
                    key,
                    'notdl' if self.config.get(
                        'enforcedl') and '.dl.' not in key.lower() else 'added'
                )
                log_entry = '[IMDb ' + score + '/Film' + (
                    '/Englisch - ' if englisch and not retail else "") + (
                                '/Englisch/Retail' if englisch and retail else "") + (
                                '/Retail' if not englisch and retail else "") + (
                                '/HEVC' if hevc_retail else '') + '] - ' + key + ' - [' + site + ']'
                internal.logger.info(log_entry)
                notify([log_entry])
                added_items.append(log_entry)
    else:
        storage = self.db.retrieve_all(key)
        if 'added' not in storage and 'notdl' not in storage:
            wrong_hoster = '[' + self._SITE + '/Hoster fehlt] - ' + key
            if 'wrong_hoster' not in storage:
                print(wrong_hoster)
                self.db.store(key, 'wrong_hoster')
                notify([wrong_hoster])
            else:
                internal.logger.debug(wrong_hoster)
    return added_items


def download_feed(self, key, content, hevc_retail):
    key = key.replace(" ", ".")
    added_items = []
    if not hevc_retail:
        if self.hevc_retail:
            if not is_hevc(key) and is_retail(key, False):
                if download_hevc(self, key):
                    internal.logger.debug(
                        "%s - Release ignoriert (stattdessen 1080p-HEVC-Retail gefunden)" % key)
                    return

    download_links = False
    if not download_links:
        site = self._SITE
        download_method = self.download_method
        download_links = self.get_download_links_method(self, content, key)
        if check_fallback_required(download_links):
            download_method = add_decrypt_instead_of_download
    if download_links:
        storage = self.db.retrieve_all(key)
        storage_replaced = self.db.retrieve_all(key.replace(".COMPLETE", "").replace(".Complete", ""))
        if 'added' in storage or 'notdl' in storage or 'added' in storage_replaced or 'notdl' in storage_replaced:
            internal.logger.debug(
                "%s - Release ignoriert (bereits gefunden)" % key)
            return
        elif not check_valid_release(key, self.retail_only, self.hevc_retail):
            internal.logger.debug(
                "%s - Release ignoriert (Gleiche oder bessere Quelle bereits vorhanden)" % key)
            return
        englisch = False
        if "*englisch*" in key.lower() or "*english*" in key.lower():
            key = key.replace(
                '*ENGLISCH*', '').replace("*Englisch*", "").replace("*ENGLISH*", "").replace("*English*", "")
            englisch = True
            if not self.feedcrawler.get('english'):
                internal.logger.debug(
                    "%s - Englische Releases deaktiviert" % key)
                return
        if self.config.get('enforcedl') and '.dl.' not in key.lower():
            imdb_id = get_imdb_id(key, content, self.filename)
            if not imdb_id:
                dual_found = download_dual_language(self, key, self.password)
                if dual_found:
                    added_items.append(dual_found)
                    if ".1080p." in key:
                        return added_items
                else:
                    internal.logger.debug(
                        "%s - Kein zweisprachiges Release gefunden." % key)
                    self.dl_unsatisfied = True
            else:
                if isinstance(imdb_id, list):
                    imdb_id = imdb_id.pop()
                if get_original_language(key, imdb_id):
                    dual_found = download_dual_language(self, key, self.password)
                    if dual_found:
                        added_items.append(dual_found)
                        if ".1080p." in key:
                            return added_items
                    elif not dual_found and not englisch:
                        internal.logger.debug(
                            "%s - Kein zweisprachiges Release gefunden! Breche ab." % key)
                        self.dl_unsatisfied = True
                        return
        if self.filename == 'List_ContentAll_Movies':
            retail = False
            if (self.config.get('enforcedl') and '.dl.' in key.lower()) or not self.config.get(
                    'enforcedl'):
                if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                    if is_retail(key, True):
                        retail = True
            else:
                if self.config.get('cutoff') and '.COMPLETE.' not in key.lower():
                    if is_retail(key, True):
                        retail = True
            if download_method(key, "FeedCrawler", download_links, self.password):
                self.db.store(
                    key,
                    'notdl' if self.config.get(
                        'enforcedl') and '.dl.' not in key.lower() else 'added'
                )
                log_entry = '[Film' + ('/Englisch' if englisch and not retail else '') + (
                    '/Englisch/Retail' if englisch and retail else '') + (
                                '/Retail' if not englisch and retail else '') + (
                                '/HEVC' if hevc_retail else '') + '] - ' + key + ' - [' + site + ']'
                internal.logger.info(log_entry)
                notify([log_entry])
                added_items.append(log_entry)
        elif self.filename == 'List_ContentAll_Seasons':
            if download_method(key, "FeedCrawler", download_links, self.password):
                self.db.store(
                    key.replace(".COMPLETE", "").replace(
                        ".Complete", ""),
                    'notdl' if self.config.get(
                        'enforcedl') and '.dl.' not in key.lower() else 'added'
                )
                log_entry = '[Staffel] - ' + key.replace(".COMPLETE", "").replace(".Complete",
                                                                                  "") + ' - [' + site + ']'
                internal.logger.info(log_entry)
                notify([log_entry])
                added_items.append(log_entry)
        else:
            if download_method(key, "FeedCrawler", download_links, self.password):
                self.db.store(
                    key,
                    'notdl' if self.config.get(
                        'enforcedl') and '.dl.' not in key.lower() else 'added'
                )
                log_entry = '[Film/Serie/RegEx] - ' + key + ' - [' + site + ']'
                internal.logger.info(log_entry)
                notify([log_entry])
                added_items.append(log_entry)
    else:
        storage = self.db.retrieve_all(key)
        if 'added' not in storage and 'notdl' not in storage:
            wrong_hoster = '[' + self._SITE + '/Hoster fehlt] - ' + key
            if 'wrong_hoster' not in storage:
                print(wrong_hoster)
                self.db.store(key, 'wrong_hoster')
                notify([wrong_hoster])
            else:
                internal.logger.debug(wrong_hoster)
    return added_items


def periodical_task(self):
    desired_rating = self.imdb
    urls = []

    if self.filename == 'List_ContentAll_Seasons':
        if not self.config.get('crawlseasons'):
            return
        liste = get_movies_list(self.filename)
        if liste:
            self.pattern = r'(' + "|".join(liste).lower() + ').*'
    elif self.filename == 'List_ContentAll_Movies_Regex':
        if not self.config.get('regex'):
            internal.logger.debug(
                "Regex deaktiviert. Stoppe Suche für Filme! (" + self.filename + ")")
            return
        liste = get_movies_list(self.filename)
        if liste:
            self.pattern = r'(' + "|".join(liste).lower() + ').*'
    elif self.filename == "IMDB":
        self.pattern = self.filename
    else:
        liste = get_movies_list(self.filename)
        if liste:
            self.pattern = r'(' + "|".join(liste).lower() + ').*'

    if self.url:
        for URL in self.FEED_URLS:
            urls.append(URL)
    else:
        internal.logger.debug("Kein Hostname gesetzt. Stoppe Suche für Filme! (" + self.filename + ")")
        return

    if not self.pattern:
        internal.logger.debug("Liste ist leer. Stoppe Suche für Filme! (" + self.filename + ")")
        return

    if self.filename == 'IMDB' and desired_rating == 0:
        internal.logger.debug("IMDb-Suchwert ist 0. Stoppe Suche für Filme! (" + self.filename + ")")
        return

    loading_304 = False
    try:
        first_page_raw = self.get_url_headers_method(urls[0], self.headers)
        first_page_content = self.get_feed_method(first_page_raw["text"])
        if first_page_raw["status_code"] == 304:
            loading_304 = True
    except:
        loading_304 = True
        first_page_content = False
        internal.logger.debug("Fehler beim Abruf von " + self._SITE + " - breche " + self._SITE + "-Suche ab!")

    set_all = settings_hash(self, False)

    if self.last_set_all == set_all:
        if loading_304:
            urls = []
            internal.logger.debug(
                self._SITE + "-Feed seit letztem Aufruf nicht aktualisiert - breche " + self._SITE + "-Suche ab!")

    sha = None

    if self.filename != 'IMDB':
        if not loading_304 and first_page_content:
            for i in first_page_content.entries:
                concat = i.title + i.published + str(self.settings) + str(self.pattern)
                sha = hashlib.sha256(concat.encode('ascii', 'ignore')).hexdigest()
                break
    else:
        if not loading_304 and first_page_content:
            for i in first_page_content.entries:
                concat = i.title + i.published + str(self.settings) + str(self.imdb)
                sha = hashlib.sha256(concat.encode('ascii', 'ignore')).hexdigest()
                break

    added_items = []
    if self.filename == "IMDB":
        if desired_rating > 0:
            i = 0
            for url in urls:
                if not self.search_imdb_done:
                    if i == 0 and first_page_content:
                        parsed_url = first_page_content
                    else:
                        parsed_url = self.get_feed_method(self.get_url_method(url))
                    found = search_imdb(self, desired_rating, parsed_url)
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
                    parsed_url = self.get_feed_method(self.get_url_method(url))
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
            internal.logger.debug(
                "Für ein oder mehrere Release(s) wurde kein zweisprachiges gefunden. Setze kein neues " + self._SITE + "-CDC!")
    if not loading_304:
        try:
            header = first_page_raw['headers']['Last-Modified']
        except:
            header = False
            internal.logger.debug(
                "Keine Header für das Abkürzen des nächsten Suchlaufs verfügbar auf " + self._SITE + ".")
        if header:
            self.cdc.delete(self._SITE + "Headers-" + self.filename)
            self.cdc.store(self._SITE + "Headers-" + self.filename, header)

    return
