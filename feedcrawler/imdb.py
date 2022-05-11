# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt allen anderen Modulen den Abruf von IMDb-Daten bereit.

import re
import traceback
from json import loads
from urllib.parse import quote

from bs4 import BeautifulSoup

from feedcrawler import internal
from feedcrawler.url import get_url, get_url_headers


def imdb_id_not_none(f):
    """Decorator that checks if IMDb-Id was passed correctly."""

    def check_imdb_id_not_none(imdb_id=None):
        if not type(imdb_id) == str or not imdb_id.startswith('tt'):
            caller = traceback.extract_stack(f=None, limit=None)[-2]
            detailed_trace = "In " + str(caller.name) + ":" + str(caller.lineno) + ", Aufruf: " + str(caller.line)
            print("Ein Aufruf ohne IMDb-ID ist nicht möglich! - " + detailed_trace)
            internal.logger.debug("Ein Aufruf ohne IMDb-ID ist nicht möglich! - " + detailed_trace)
            return False
        return f(imdb_id)

    return check_imdb_id_not_none


def get_imdb_id_from_content(key, content, current_list):
    try:
        imdb_id = re.findall(
            r'.*?(?:href=.?http(?:|s):\/\/(?:|www\.)imdb\.com\/title\/(tt[0-9]{7,9}).*?).*?(\d(?:\.|\,)\d)(?:.|.*?)<\/a>.*?',
            content)
    except:
        imdb_id = False

    if imdb_id:
        imdb_id = imdb_id[0][0]
    else:
        search_title = re.findall(r"(.*?)(?:\.(?:(?:19|20)\d{2})|\.German|\.\d{3,4}p|\.S(?:\d{1,3})\.)", key)[
            0].replace(".", "+")
        imdb_id = get_imdb_id_from_title(search_title, current_list)

    return imdb_id


def get_imdb_id_from_title(title, current_list):
    if current_list == 'List_ContentAll_Seasons':
        query = "s=tt&ttype=ft&ref_=fn_ft&q=%s" % quote(title)
    else:
        query = quote(title)
    request = get_url_headers("https://www.imdb.com/find?" + query, headers={'Accept-Language': 'de'})
    search_results = re.findall(r'<td class="result_text"> <a href="\/title\/(tt[0-9]{7,9}).*?" >(.*?)<\/a>(.*?)<\/td>',
                                request["text"])
    if len(search_results) > 0:
        imdb_id = search_results[0][0]
    else:
        internal.logger.debug("[IMDb] - %s - Keine ID gefunden" % title)
        imdb_id = False
    return imdb_id


@imdb_id_not_none
def original_language_not_german(imdb_id):
    original_language = False

    try:
        request = get_url("https://www.imdb.com/title/%s/" % imdb_id)
        soup = BeautifulSoup(request, "html5lib")
        props = soup.find("script", text=re.compile("props"))
        details = loads(props.string)
        languages = details['props']['pageProps']['mainColumnData']['spokenLanguages']['spokenLanguages']
        original_language = languages[0]['id']
    except:
        pass

    if original_language and original_language == "de":
        internal.logger.debug(
            "[IMDb] - %s - Original-Sprache ist Deutsch. Breche Suche nach zweisprachigem Release ab!" % imdb_id)
        return False

    if not original_language:
        print(u"[IMDb] - %s - Original-Sprache nicht ermittelbar" % imdb_id)
        internal.logger.debug("[IMDb] - %s - Original-Sprache nicht ermittelbar" % imdb_id)

    return original_language


@imdb_id_not_none
def get_episodes(imdb_id):
    episodes = False

    try:
        request = get_url("https://www.imdb.com/title/%s/episodes?ref_=tt_eps_sm" % imdb_id)
        soup = BeautifulSoup(request, "html5lib")
        seasons = soup.find("select", {"id": "bySeason"}).findAll("option")
        if len(seasons) > 0:
            episodes = {}
            for sn in seasons:
                i = 1
                sn = sn["value"]
                eps = []
                request = get_url("https://www.imdb.com/title/" + imdb_id + "/episodes?season=" + sn)
                soup = BeautifulSoup(request, "html5lib")
                details = soup.findAll("div", {"itemprop": "episodes"})
                for _ in details:
                    eps.append(i)
                    i += 1
                episodes[int(sn)] = eps
    except:
        pass

    if not episodes:
        print(u"[IMDb] - %s - Keine Episoden gefunden" % imdb_id)
        internal.logger.debug("[IMDb] - %s - Keine Episoden gefunden" % imdb_id)

    return episodes


@imdb_id_not_none
def get_localized_title(imdb_id):
    localized_title = False

    try:
        request = get_url_headers("https://www.imdb.com/title/%s/" % imdb_id, headers={'Accept-Language': 'de'})
        match = re.findall(r'<title>(.*?) \(.*?</title>', request["text"])
        localized_title = match[0]
    except:
        try:
            match = re.findall(r'<title>(.*?) - IMDb</title>', request["text"])
            localized_title = match[0]
        except:
            pass

    if not localized_title:
        print(u"[IMDb] - %s - Deutscher Titel nicht ermittelbar" % imdb_id)
        internal.logger.debug("[IMDb] - %s - Deutscher Titel nicht ermittelbar" % imdb_id)

    return localized_title


@imdb_id_not_none
def get_rating(imdb_id):
    rating = False

    try:
        request = get_url("https://www.imdb.com/title/%s/" % imdb_id)
        soup = BeautifulSoup(request, "html5lib")
        props = soup.find("script", text=re.compile("props"))
        details = loads(props.string)
        rating = details['props']['pageProps']['aboveTheFoldData']['ratingsSummary']['aggregateRating']
    except:
        pass

    if not rating:
        print(u"[IMDb] - %s - Bewertungen nicht ermittelbar" % imdb_id)
        internal.logger.debug("[IMDb] - %s - Bewertungen nicht ermittelbar" % imdb_id)

    return rating


@imdb_id_not_none
def get_votes(imdb_id):
    votes = False

    try:
        request = get_url("https://www.imdb.com/title/%s/" % imdb_id)
        soup = BeautifulSoup(request, "html5lib")
        props = soup.find("script", text=re.compile("props"))
        details = loads(props.string)
        votes = details['props']['pageProps']['aboveTheFoldData']['ratingsSummary']['voteCount']
    except:
        pass

    if not votes:
        print(u"[IMDb] - %s - Anzahl der Bewertungen nicht ermittelbar" % imdb_id)
        internal.logger.debug("[IMDb] - %s - Anzahl der Bewertungen nicht ermittelbar" % imdb_id)

    return votes


@imdb_id_not_none
def get_year(imdb_id):
    year = False

    try:
        request = get_url("https://www.imdb.com/title/%s/" % imdb_id)
        match = re.findall(r'<title>(?:.*?) \(.*?(\d{4}).*</title>', request)
        year = int("".join(re.findall(r'\d+', str(match[0]))))
    except:
        pass

    if not year:
        print(u"[IMDb] - %s - Erscheinungsjahr nicht ermittelbar" % imdb_id)
        internal.logger.debug("[IMDb] - %s - Erscheinungsjahr nicht ermittelbar" % imdb_id)

    return year
