# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import re

from rsscrawler.url import get_url


def get_imdb_id(key, content, filename, configfile, dbfile, scraper, log_debug):
    imdb_id = re.findall(
        r'.*?(?:href=.?http(?:|s):\/\/(?:|www\.)imdb\.com\/title\/(tt[0-9]{7,9}).*?).*?(\d(?:\.|\,)\d)(?:.|.*?)<\/a>.*?',
        content)

    if imdb_id:
        imdb_id = imdb_id[0][0]
    else:
        search_title = re.findall(
            r"(.*?)(?:\.(?:(?:19|20)\d{2})|\.German|\.\d{3,4}p|\.S(?:\d{1,3})\.)", key)[0].replace(".", "+")
        search_url = "http://www.imdb.com/find?q=" + search_title
        search_page = get_url(search_url, configfile, dbfile, scraper)
        search_results = re.findall(
            r'<td class="result_text"> <a href="\/title\/(tt[0-9]{7,9})\/\?ref_=fn_al_tt_\d" >(.*?)<\/a>.*? \((\d{4})\)..(.{9})',
            search_page)
        total_results = len(search_results)
        if filename == 'MB_Staffeln':
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
                log_debug(
                    "%s - Keine passende Film-IMDB-Seite gefunden" % key)
        if not imdb_id:
            return False

    return imdb_id


def get_original_language(key, imdb_details, imdb_url, configfile, dbfile, scraper, log_debug):
    original_language = ""
    if imdb_details and len(imdb_details) > 0:
        original_language = re.findall(
            r"Language:<\/h4>\n.*?\n.*?url'>(.*?)<\/a>", imdb_details)
        if original_language:
            original_language = original_language[0]
        else:
            log_debug(
                "%s - Originalsprache nicht ermittelbar" % key)
    elif imdb_url and len(imdb_url) > 0:
        details = get_url(imdb_url, configfile, dbfile, scraper)
        if not details:
            log_debug(
                "%s - Originalsprache nicht ermittelbar" % key)
        original_language = re.findall(
            r"Language:<\/h4>\n.*?\n.*?url'>(.*?)<\/a>", details)
        if original_language:
            original_language = original_language[0]
            return original_language
        else:
            log_debug(
                "%s - Originalsprache nicht ermittelbar" % key)
            return False

    if original_language == "German":
        log_debug(
            "%s - Originalsprache ist Deutsch. Breche Suche nach zweisprachigem Release ab!" % key)
        return False
