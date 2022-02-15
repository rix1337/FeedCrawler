# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt allen anderen Modulen den Abruf von IMDb-Daten bereit.

import re

from imdb import Cinemagoer as IMDb

from feedcrawler import internal
from feedcrawler.url import get_url


def clean_imdb_id(string):
    integer = re.findall(r'\d+', string)[0]
    return integer


def get_imdb_id(key, content, filename):
    try:
        imdb_id = re.findall(
            r'.*?(?:href=.?http(?:|s):\/\/(?:|www\.)imdb\.com\/title\/(tt[0-9]{7,9}).*?).*?(\d(?:\.|\,)\d)(?:.|.*?)<\/a>.*?',
            content)
    except:
        imdb_id = False

    if imdb_id:
        imdb_id = imdb_id[0][0]
    else:
        try:
            search_title = re.findall(
                r"(.*?)(?:\.(?:(?:19|20)\d{2})|\.German|\.\d{3,4}p|\.S(?:\d{1,3})\.)", key)[0].replace(".", "+")
            search_url = "http://www.imdb.com/find?q=" + search_title
            search_page = get_url(search_url)
            search_results = re.findall(
                r'<td class="result_text"> <a href="\/title\/(tt[0-9]{7,9})\/\?ref_=fn_al_tt_\d" >(.*?)<\/a>.*? \((\d{4})\)..(.{9})',
                search_page)
        except:
            return False
        total_results = len(search_results)
        if filename == 'List_ContentAll_Seasons':
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
                internal.logger.debug("%s - Keine passende Film-IMDb-Seite gefunden" % key)
        if not imdb_id:
            return False

    return imdb_id


def get_original_language(key, imdb_id):
    original_language = False

    try:
        imdb_id = clean_imdb_id(imdb_id)
        output = IMDb('https', languages='de-DE').get_movie(imdb_id)
        original_language = output.data["languages"][0]
    except:
        pass

    if not original_language:
        internal.logger.debug("%s - Originalsprache nicht ermittelbar" % key)

    if original_language and original_language == "German":
        internal.logger.debug("%s - Originalsprache ist Deutsch. Breche Suche nach zweisprachigem Release ab!" % key)
        return False
    else:
        return original_language
