# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul durchsucht die Feeds aller Seiten des Typs content_all auf Basis einer standardisierten Struktur.

import hashlib
import re

import feedcrawler.external_sites.feed_search.sites.content_all_by as content_all_by
import feedcrawler.external_sites.feed_search.sites.content_all_fx as content_all_fx
import feedcrawler.external_sites.feed_search.sites.content_all_hw as content_all_hw
import feedcrawler.external_sites.feed_search.sites.content_all_nk as content_all_nk
from feedcrawler.external_sites.feed_search.shared import add_decrypt_instead_of_download
from feedcrawler.external_sites.metadata.imdb import get_rating
from feedcrawler.external_sites.metadata.imdb import get_votes
from feedcrawler.external_sites.metadata.imdb import get_year
from feedcrawler.external_sites.metadata.imdb import original_language_not_german
from feedcrawler.external_sites.web_search.content_all import get_search_results_for_feed_search
from feedcrawler.providers import shared_state
from feedcrawler.providers.common_functions import check_is_ignored
from feedcrawler.providers.common_functions import check_valid_release
from feedcrawler.providers.common_functions import fullhd_title
from feedcrawler.providers.common_functions import is_hevc
from feedcrawler.providers.common_functions import is_retail
from feedcrawler.providers.myjd_connection import myjd_download
from feedcrawler.providers.notifications import notify
from feedcrawler.providers.sqlite_database import ListDb
from feedcrawler.providers.url_functions import get_url


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
        if self.filename == "IMDb":
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
            shared_state.logger.debug("Fehler beim Abruf von " + post.title + ": Kein Durchsuchbarer Inhalt gefunden.")
            content = False
        if content:
            post.title = post.title.strip(u'\u200b')

        if self.search_imdb_done:
            shared_state.logger.debug(
                self._SITE + "-Feed ab hier bereits gecrawlt (" + post.title + ") - breche " + self._SITE + "-Suche ab!")
            return added_items

        concat = post.title + post.published + settings + score
        sha = hashlib.sha256(concat.encode(
            'ascii', 'ignore')).hexdigest()
        if sha == self.last_sha:
            self.search_imdb_done = True

        if content:
            if "mkv" in content.lower():
                hevc_retail = False
                storage = self.db.retrieve_all(post.title)
                storage_replaced = self.db.retrieve_all(
                    post.title.replace(".COMPLETE", "").replace(".Complete", ""))
                if 'added' in storage or 'notdl' in storage or 'added' in storage_replaced or 'notdl' in storage_replaced:
                    shared_state.logger.debug("%s - Release ignoriert (bereits gefunden)" % post.title)
                    continue
                elif not check_valid_release(post.title, self.retail_only, self.hevc_retail):
                    shared_state.logger.debug(
                        "%s - Release ignoriert (Gleiche oder bessere Quelle bereits vorhanden)" % post.title)
                    continue
                quality_set = self.config.get('quality')
                if '.3d.' in post.title.lower():
                    shared_state.logger.debug("%s - Release ignoriert (3D-Film)" % post.title)
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
                                    shared_state.logger.debug(
                                        "%s - Qualität ignoriert (Release ist 1080p-HEVC-Retail)" % post.title)
                                    hevc_retail = True
                                    quality_match = True
                    if not quality_match:
                        shared_state.logger.debug("%s - Release ignoriert (falsche Auflösung)" % post.title)
                        continue

                found = check_is_ignored(post.title, self.config.get("ignore"))
                if found:
                    if self.hevc_retail:
                        if is_hevc(post.title) and "1080p" in post.title:
                            if is_retail(post.title, False):
                                shared_state.logger.debug(
                                    "%s - Filterliste ignoriert (Release ist 1080p-HEVC-Retail)" % post.title)
                                hevc_retail = True
                                found = False
                if found:
                    shared_state.logger.debug("%s - Release ignoriert (aufgrund der Filterliste)" % post.title)
                    continue
                if self.feedcrawler.get("surround"):
                    if not re.match(r'.*\.(DTS|DD\+*51|DD\+*71|AC3\.5\.*1)\..*', post.title):
                        shared_state.logger.debug(post.title + " - Release ignoriert (kein Mehrkanalton)")
                        continue
                season = re.search(r'\.S(\d{1,3})(\.|-|E)', post.title)
                if season:
                    shared_state.logger.debug("%s - Release ignoriert (IMDb sucht nur Filme)" % post.title)
                    continue

                if post.imdb_id:
                    min_year = int(self.config.get("imdbyear"))
                    if min_year:
                        year = get_year(post.imdb_id)
                        if year:
                            if year < min_year:
                                shared_state.logger.debug("%s - Release ignoriert (Film zu alt)" % post.title)
                                continue
                        else:
                            shared_state.logger.debug("%s - Release ignoriert (Alter nicht ermittelbar)" % post.title)
                            continue
                    votes = get_votes(post.imdb_id)
                    if votes:
                        if votes < 1500:
                            shared_state.logger.debug(post.title + " - Release ignoriert (Weniger als 1500 IMDb-Votes)")
                            continue
                    else:
                        shared_state.logger.debug(post.title + " - Release ignoriert (Konnte keine IMDb-Votes finden)")
                        continue
                    rating = get_rating(post.imdb_id)
                    if rating and rating > desired_rating:
                        download_method = self.download_method
                        download_links = self.get_download_links_method(self, content, post.title)
                        if check_fallback_required(download_links):
                            download_method = add_decrypt_instead_of_download
                        found = download_imdb(self,
                                              post.title,
                                              download_links,
                                              post.source,
                                              post.imdb_id,
                                              post.size,
                                              hevc_retail,
                                              str(rating).replace(",", "."),
                                              download_method
                                              )
                        if found:
                            for i in found:
                                added_items.append(i)
    return added_items


def search_feed(self, feed):
    if not self.pattern:
        return
    added_items = []

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
            shared_state.logger.debug("Fehler beim Abruf von " + post.title + ": Kein Durchsuchbarer Inhalt gefunden.")
            content = False
        if content:
            post.title = post.title.strip(u'\u200b')

        if self.search_regular_done:
            shared_state.logger.debug(
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
                    found = check_is_ignored(post.title, self.config.get("ignore"))
                    if found:
                        if self.hevc_retail:
                            if is_hevc(post.title) and "1080p" in post.title:
                                if is_retail(post.title, False):
                                    shared_state.logger.debug(
                                        "%s - Filterliste ignoriert (Release ist 1080p-HEVC-Retail)" % post.title)
                                    hevc_retail = True
                                    found = False
                    if found:
                        shared_state.logger.debug("%s - Release ignoriert (aufgrund der Filterliste)" % post.title)
                        continue
                    if self.feedcrawler.get("surround"):
                        if not re.match(r'.*\.(DTS|DD\+*51|DD\+*71|AC3\.5\.*1)\..*', post.title):
                            shared_state.logger.debug(post.title + " - Release ignoriert (kein Mehrkanalton)")
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
                                        shared_state.logger.debug(
                                            "%s  - Qualität ignoriert (Release ist 1080p-HEVC-Retail)" % post.title)
                                        hevc_retail = True
                                        found = True
                        if found:
                            episode = re.search(
                                r'([\w\.\s]*s\d{1,2}e\d{1,2})[\w\.\s]*', post.title.lower())
                            if episode:
                                shared_state.logger.debug("%s - Release ignoriert (Serienepisode)" % post.title)
                                continue
                            found = download_feed(self, post.title, content, post.source, post.imdb_id, post.size,
                                                  hevc_retail)
                            if found:
                                for i in found:
                                    added_items.append(i)
                    elif self.filename == 'List_ContentAll_Seasons':
                        validsource = re.search(self.config.get(
                            "seasonssource"), post.title.lower())
                        if not validsource:
                            shared_state.logger.debug(post.title + " - Release hat falsche Quelle")
                            continue
                        if ".complete." not in post.title.lower():
                            if "FX" not in self._SITE and "DW" not in self._SITE:
                                shared_state.logger.debug(post.title + " - Staffel noch nicht komplett")
                                continue
                        season = re.search(r"\.s\d", post.title.lower())
                        if not season:
                            shared_state.logger.debug(post.title + " - Release ist keine Staffel")
                            continue
                        if not self.config.get("seasonpacks"):
                            staffelpack = re.search(
                                r"s\d.*(-|\.).*s\d", post.title.lower())
                            if staffelpack:
                                shared_state.logger.debug("%s - Release ignoriert (Staffelpaket)" % post.title)
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
                                shared_state.logger.debug("%s - Release ignoriert (Serienepisode)" % post.title)
                                continue
                            found = download_feed(self, post.title, content, post.source, post.imdb_id, post.size,
                                                  hevc_retail)
                            if found:
                                for i in found:
                                    added_items.append(i)
                    else:
                        found = download_feed(self, post.title, content, post.source, post.imdb_id, post.size,
                                              hevc_retail)
                        if found:
                            for i in found:
                                added_items.append(i)
    return added_items


def download_hevc(self, title, original_imdb_id):
    search_title = fullhd_title(title).split('.German', 1)[0].replace(".", " ").replace(" ", "+")
    feedsearch_title = fullhd_title(title).split('.German', 1)[0]
    search_results = get_search_results_for_feed_search(self, search_title)

    i = 0
    for result in search_results:
        i += 1

        key = result["title"]

        if feedsearch_title in key:
            link = result["link"]
            password = result["password"]
            site = result["site"]
            size = result["size"]
            source = result["source"]
            imdb_id = result["imdb_id"]

            if site == "BY":
                get_download_links_method = content_all_by.by_page_download_link
                download_method = myjd_download
            elif site == "FX":
                link = get_url(link)
                get_download_links_method = content_all_fx.fx_get_download_links
                download_method = add_decrypt_instead_of_download
            elif site == "HW":
                link = get_url(link)
                get_download_links_method = content_all_hw.hw_get_download_links
                download_method = add_decrypt_instead_of_download
            elif site == "NK":
                get_download_links_method = content_all_nk.nk_page_download_link
                download_method = myjd_download
            else:
                continue

            if original_imdb_id and imdb_id and imdb_id != original_imdb_id:
                shared_state.logger.debug("%s - Abweichende IMDb-IDs identifiziert! Breche ab." % key)
                continue

            if is_hevc(key) and "1080p" in key:
                download_links = get_download_links_method(self, link, key)
                if check_fallback_required(download_links):
                    download_method = add_decrypt_instead_of_download
                if download_links:
                    storage = self.db.retrieve_all(key)
                    storage_replaced = self.db.retrieve_all(key.replace(".COMPLETE", "").replace(".Complete", ""))
                    if 'added' in storage or 'notdl' in storage or 'added' in storage_replaced or 'notdl' in storage_replaced:
                        shared_state.logger.debug("%s - HEVC Release ignoriert (bereits gefunden)" % key)
                        return True

                    englisch = False
                    if "*englisch" in key.lower() or "*english" in key.lower():
                        key = key.replace(
                            '*ENGLISCH', '').replace("*Englisch", "").replace("*ENGLISH", "").replace("*English",
                                                                                                      "").replace(
                            "*", "")
                        englisch = True
                        if not self.feedcrawler.get('english'):
                            shared_state.logger.debug("%s - Englische Releases deaktiviert" % key)
                            continue

                    if self.config.get('enforcedl') and '.dl.' not in key.lower():
                        if not imdb_id:
                            dual_found = download_dual_language(self, key, imdb_id)
                            if dual_found and ".1080p." in key:
                                continue
                            elif not dual_found and not englisch:
                                shared_state.logger.debug("%s - Kein zweisprachiges HEVC-Release gefunden." % key)
                                self.dl_unsatisfied = True
                        else:
                            if original_language_not_german(imdb_id):
                                dual_found = download_dual_language(self, key, imdb_id)
                                if dual_found and ".1080p." in key:
                                    continue
                                elif not dual_found and not englisch:
                                    shared_state.logger.debug(
                                        "%s - Kein zweisprachiges HEVC-Release gefunden! Breche ab." % key)
                                    self.dl_unsatisfied = True
                                    continue

                    if self.filename == 'List_ContentAll_Movies' or self.filename == 'IMDb':
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
                                    '/Retail' if retail else "") + '/HEVC] - ' + key + ' - [' + site + '] - ' + size + ' - ' + source
                                shared_state.logger.info(log_entry)
                                notify([{"text": log_entry, "imdb_id": imdb_id}])
                                return True
                    elif self.filename == 'List_ContentAll_Movies_Regex':
                        if download_method(key, "FeedCrawler", download_links, password):
                            self.db.store(
                                key,
                                'added'
                            )
                            log_entry = '[Film/Serie/RegEx/HEVC] - ' + key + ' - [' + site + '] - ' + size + ' - ' + source
                            shared_state.logger.info(log_entry)
                            notify([{"text": log_entry, "imdb_id": imdb_id}])
                            return True
                    else:
                        if download_method(key, "FeedCrawler", download_links, password):
                            self.db.store(
                                key,
                                'added'
                            )
                            log_entry = '[Staffel/HEVC] - ' + key + ' - [' + site + '] - ' + size + ' - ' + source
                            shared_state.logger.info(log_entry)
                            notify([{"text": log_entry, "imdb_id": imdb_id}])
                            return True
                else:
                    storage = self.db.retrieve_all(key)
                    if 'added' not in storage and 'notdl' not in storage:
                        wrong_hoster = '[' + site + 'HEVC-Suche/Hoster fehlt] - ' + key
                        if 'wrong_hoster' not in storage:
                            print(wrong_hoster)
                            self.db.store(key, 'wrong_hoster')
                            notify([{"text": wrong_hoster}])
                        else:
                            shared_state.logger.debug(wrong_hoster)
    return False


def download_dual_language(self, title, original_imdb_id):
    hevc = is_hevc(title)

    search_title = fullhd_title(title).split('.x264', 1)[0].split('.h264', 1)[0].split('.h265', 1)[0].split('.x265', 1)[
        0].split('.HEVC-', 1)[0].replace(".", " ").replace(" ", "+")
    feedsearch_title = \
        fullhd_title(title).split('.German', 1)[0].split('.x264', 1)[0].split('.h264', 1)[0].split('.h265', 1)[0].split(
            '.x265', 1)[
            0].split('.HEVC-', 1)[0]
    search_results = get_search_results_for_feed_search(self, search_title)

    hevc_found = False
    for result in search_results:
        key = result["title"]
        if feedsearch_title in key and ".dl." in key.lower() and (hevc and is_hevc(key)):
            hevc_found = True

    i = 0
    for result in search_results:
        i += 1

        key = result["title"].replace(" ", ".")

        if feedsearch_title in key:
            link = result["link"]
            password = result["password"]
            site = result["site"]
            size = result["size"]
            source = result["source"]
            imdb_id = result["imdb_id"]

            if site == "BY":
                get_download_links_method = content_all_by.by_page_download_link
                download_method = myjd_download
            elif site == "FX":
                link = get_url(link)
                get_download_links_method = content_all_fx.fx_get_download_links
                download_method = add_decrypt_instead_of_download
            elif site == "HW":
                link = get_url(link)
                get_download_links_method = content_all_hw.hw_get_download_links
                download_method = add_decrypt_instead_of_download
            elif site == "NK":
                get_download_links_method = content_all_nk.nk_page_download_link
                download_method = myjd_download
            else:
                continue

            if original_imdb_id and imdb_id and imdb_id != original_imdb_id:
                shared_state.logger.debug("%s - Abweichende IMDb-IDs identifiziert! Breche ab." % key)
                continue
            if ".dl." not in key.lower():
                shared_state.logger.debug("%s - Release ignoriert (nicht zweisprachig)" % key)
                continue
            if hevc and hevc_found and not is_hevc(key):
                shared_state.logger.debug("%s - zweisprachiges Release ignoriert (nicht HEVC)" % key)
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
                    shared_state.logger.debug("%s - zweisprachiges Release ignoriert (bereits gefunden)" % key)
                    return True
                elif self.filename == 'List_ContentAll_Movies' or self.filename == 'IMDb':
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
                            '/Retail' if retail else "") + '/Zweisprachig] - ' + key + ' - [' + site + '] - ' + size + ' - ' + source
                        shared_state.logger.info(log_entry)
                        notify([{"text": log_entry, "imdb_id": imdb_id}])
                        return True
                elif self.filename == 'List_ContentAll_Movies_Regex':
                    if download_method(key, "FeedCrawler" + path_suffix, download_links, password):
                        self.db.store(
                            key,
                            'added'
                        )
                        log_entry = '[Film/Serie/RegEx/Zweisprachig] - ' + key + ' - [' + site + '] - ' + size + ' - ' + source
                        shared_state.logger.info(log_entry)
                        notify([{"text": log_entry, "imdb_id": imdb_id}])
                        return True
                else:
                    if download_method(key, "FeedCrawler" + path_suffix, download_links, password):
                        self.db.store(
                            key,
                            'added'
                        )
                        log_entry = '[Staffel/Zweisprachig] - ' + key + ' - [' + site + '] - ' + size + ' - ' + source
                        shared_state.logger.info(log_entry)
                        notify([{"text": log_entry, "imdb_id": imdb_id}])
                        return True
            else:
                storage = self.db.retrieve_all(key)
                if 'added' not in storage and 'notdl' not in storage:
                    wrong_hoster = '[' + site + 'DL-Suche/Hoster fehlt] - ' + key
                    if 'wrong_hoster' not in storage:
                        print(wrong_hoster)
                        self.db.store(key, 'wrong_hoster')
                        notify([{"text": wrong_hoster}])
                    else:
                        shared_state.logger.debug(wrong_hoster)
    return False


def download_imdb(self, key, download_links, source, imdb_id, size, hevc_retail, score, download_method):
    site = self._SITE
    key = key.replace(" ", ".")

    added_items = []
    if not hevc_retail:
        if self.hevc_retail:
            if not is_hevc(key) and is_retail(key, False):
                if download_hevc(self, key, imdb_id):
                    shared_state.logger.debug("%s - Release ignoriert (stattdessen 1080p-HEVC-Retail gefunden)" % key)
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
                shared_state.logger.debug("%s - Englische Releases deaktiviert" % key)
                return
        if self.config.get('enforcedl') and '.dl.' not in key.lower():
            if original_language_not_german(imdb_id):
                dual_found = download_dual_language(self, key, imdb_id)
                if dual_found:
                    added_items.append(dual_found)
                    if ".1080p." in key:
                        return added_items
                elif not dual_found and not englisch:
                    shared_state.logger.debug("%s - Kein zweisprachiges Release gefunden!" % key)
                    return

        if '.3d.' in key.lower():
            shared_state.logger.debug("%s - Release ignoriert (3D-Film)" % key.title)
            return
        else:
            retail = False
            if (self.config.get('enforcedl') and '.dl.' in key.lower()) or not self.config.get(
                    'enforcedl'):
                if self.config.get('cutoff'):
                    if self.config.get('enforcedl'):
                        if is_retail(key, True):
                            retail = True
            if download_method(key, "FeedCrawler", download_links, self.password):
                self.db.store(
                    key,
                    'notdl' if self.config.get(
                        'enforcedl') and '.dl.' not in key.lower() else 'added'
                )
                try:
                    score = str(float(score))
                except:
                    pass
                log_entry = '[IMDb ' + score + '/Film' + (
                    '/Englisch - ' if englisch and not retail else "") + (
                                '/Englisch/Retail' if englisch and retail else "") + (
                                '/Retail' if not englisch and retail else "") + (
                                '/HEVC' if hevc_retail else '') + '] - ' + key + ' - [' + site + '] - ' + size + ' - ' + source
                shared_state.logger.info(log_entry)
                notify([{"text": log_entry, "imdb_id": imdb_id}])
                added_items.append(log_entry)
    else:
        storage = self.db.retrieve_all(key)
        if 'added' not in storage and 'notdl' not in storage:
            wrong_hoster = '[' + self._SITE + '/Hoster fehlt] - ' + key
            if 'wrong_hoster' not in storage:
                print(wrong_hoster)
                self.db.store(key, 'wrong_hoster')
                notify([{"text": wrong_hoster}])
            else:
                shared_state.logger.debug(wrong_hoster)
    return added_items


def download_feed(self, key, content, source, imdb_id, size, hevc_retail):
    site = self._SITE
    key = key.replace(" ", ".")

    added_items = []
    if not hevc_retail:
        if self.hevc_retail:
            if not is_hevc(key) and is_retail(key, False):
                if download_hevc(self, key, imdb_id):
                    shared_state.logger.debug("%s - Release ignoriert (stattdessen 1080p-HEVC-Retail gefunden)" % key)
                    return

    download_method = self.download_method
    download_links = self.get_download_links_method(self, content, key)
    if check_fallback_required(download_links):
        download_method = add_decrypt_instead_of_download
    if download_links:
        storage = self.db.retrieve_all(key)
        storage_replaced = self.db.retrieve_all(key.replace(".COMPLETE", "").replace(".Complete", ""))
        if 'added' in storage or 'notdl' in storage or 'added' in storage_replaced or 'notdl' in storage_replaced:
            shared_state.logger.debug("%s - Release ignoriert (bereits gefunden)" % key)
            return
        elif not check_valid_release(key, self.retail_only, self.hevc_retail):
            shared_state.logger.debug("%s - Release ignoriert (Gleiche oder bessere Quelle bereits vorhanden)" % key)
            return
        englisch = False
        if "*englisch*" in key.lower() or "*english*" in key.lower():
            key = key.replace(
                '*ENGLISCH*', '').replace("*Englisch*", "").replace("*ENGLISH*", "").replace("*English*", "")
            englisch = True
            if not self.feedcrawler.get('english'):
                shared_state.logger.debug("%s - Englische Releases deaktiviert" % key)
                return
        if self.config.get('enforcedl') and '.dl.' not in key.lower():
            if not imdb_id:
                dual_found = download_dual_language(self, key, imdb_id)
                if dual_found:
                    added_items.append(dual_found)
                    if ".1080p." in key:
                        return added_items
                else:
                    shared_state.logger.debug("%s - Kein zweisprachiges Release gefunden." % key)
                    self.dl_unsatisfied = True
            else:
                if original_language_not_german(imdb_id):
                    dual_found = download_dual_language(self, key, imdb_id)
                    if dual_found:
                        added_items.append(dual_found)
                        if ".1080p." in key:
                            return added_items
                    elif not dual_found and not englisch:
                        shared_state.logger.debug("%s - Kein zweisprachiges Release gefunden! Breche ab." % key)
                        self.dl_unsatisfied = True
                        return
        if self.filename == 'List_ContentAll_Movies':
            retail = False
            if (self.config.get('enforcedl') and '.dl.' in key.lower()) or not self.config.get(
                    'enforcedl'):
                if self.config.get('cutoff'):
                    if is_retail(key, True):
                        retail = True
            else:
                if self.config.get('cutoff'):
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
                                '/HEVC' if hevc_retail else '') + '] - ' + key + ' - [' + site + '] - ' + size + ' - ' + source
                shared_state.logger.info(log_entry)
                notify([{"text": log_entry, "imdb_id": imdb_id}])
                added_items.append(log_entry)
        elif self.filename == 'List_ContentAll_Seasons':
            if download_method(key, "FeedCrawler", download_links, self.password):
                self.db.store(
                    key.replace(".COMPLETE", "").replace(".Complete", ""),
                    'notdl' if self.config.get(
                        'enforcedl') and '.dl.' not in key.lower() else 'added'
                )
                log_entry = '[Staffel] - ' + key.replace(".COMPLETE", "").replace(".Complete",
                                                                                  "") + ' - [' + site + '] - ' + size + ' - ' + source
                shared_state.logger.info(log_entry)
                notify([{"text": log_entry, "imdb_id": imdb_id}])
                added_items.append(log_entry)
        else:
            if download_method(key, "FeedCrawler", download_links, self.password):
                self.db.store(
                    key,
                    'notdl' if self.config.get(
                        'enforcedl') and '.dl.' not in key.lower() else 'added'
                )
                log_entry = '[Film/Serie/RegEx] - ' + key + ' - [' + site + '] - ' + size + ' - ' + source
                shared_state.logger.info(log_entry)
                notify([{"text": log_entry, "imdb_id": imdb_id}])
                added_items.append(log_entry)
    else:
        storage = self.db.retrieve_all(key)
        if 'added' not in storage and 'notdl' not in storage:
            wrong_hoster = '[' + self._SITE + '/Hoster fehlt] - ' + key
            if 'wrong_hoster' not in storage:
                print(wrong_hoster)
                self.db.store(key, 'wrong_hoster')
                notify([{"text": wrong_hoster}])
            else:
                shared_state.logger.debug(wrong_hoster)
    return added_items


def periodical_task(self):
    urls = []
    if self.url:
        for URL in self.FEED_URLS:
            urls.append(URL)
    else:
        shared_state.logger.debug("Kein Hostname gesetzt. Stoppe Suche für Filme! (" + self.filename + ")")
        return

    if self.filename == 'List_ContentAll_Seasons':
        if not self.config.get('crawlseasons'):
            return
        liste = get_movies_list(self.filename)
        if liste:
            self.pattern = r'(' + "|".join(liste).lower() + ').*'
    elif self.filename == 'List_ContentAll_Movies_Regex':
        if not self.config.get('regex'):
            shared_state.logger.debug("Regex deaktiviert. Stoppe Suche für Filme! (" + self.filename + ")")
            return
        liste = get_movies_list(self.filename)
        if liste:
            self.pattern = r'(' + "|".join(liste).lower() + ').*'
    elif self.filename == "IMDb":
        self.pattern = self.filename
    else:
        liste = get_movies_list(self.filename)
        if liste:
            self.pattern = r'(' + "|".join(liste).lower() + ').*'

    if not self.pattern:
        shared_state.logger.debug("Liste ist leer. Stoppe Suche für Filme! (" + self.filename + ")")
        return

    desired_rating = self.imdb
    if self.filename == 'IMDb' and desired_rating == 0:
        shared_state.logger.debug("IMDb-Suchwert ist 0. Stoppe Suche für Filme! (" + self.filename + ")")
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
        shared_state.logger.debug("Fehler beim Abruf von " + self._SITE + " - breche " + self._SITE + "-Suche ab!")

    set_all = settings_hash(self, False)

    if self.last_set_all == set_all:
        if loading_304:
            urls = []
            shared_state.logger.debug(
                self._SITE + "-Feed seit letztem Aufruf nicht aktualisiert - breche " + self._SITE + "-Suche ab!")

    sha = None

    if self.filename != 'IMDb':
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
    if self.filename == "IMDb":
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
            shared_state.logger.debug(
                "Für ein oder mehrere Release(s) wurde kein zweisprachiges gefunden. Setze kein neues " + self._SITE + "-CDC!")
    if not loading_304:
        try:
            header = first_page_raw['headers']['Last-Modified']
        except:
            header = False
            shared_state.logger.debug(
                "Keine Header für das Abkürzen des nächsten Suchlaufs verfügbar auf " + self._SITE + ".")
        if header:
            self.cdc.delete(self._SITE + "Headers-" + self.filename)
            self.cdc.store(self._SITE + "Headers-" + self.filename, header)

    return
