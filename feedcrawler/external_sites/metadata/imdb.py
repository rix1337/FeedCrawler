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
from feedcrawler.common import simplified_search_term_in_title
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


def get_imdb_id_from_content(key, content, current_list="NoList"):
    try:
        imdb_id = re.findall(
            r'.*?(?:href=.?http(?:|s):\/\/(?:|www\.)imdb\.com\/title\/(tt[0-9]{7,9}).*?).*?(\d(?:\.|\,)\d)(?:.|.*?)<\/a>.*?',
            content)
    except:
        imdb_id = False

    if imdb_id:
        imdb_id = imdb_id[0][0]
    else:
        imdb_id = get_imdb_id_from_title(key, current_list)

    return imdb_id


def get_imdb_id_from_link(key, link, current_list="NoList"):
    try:
        imdb_id = re.findall(r'.*?http(?:|s):\/\/(?:|www\.)imdb\.com\/title\/(tt[0-9]{7,9}).*?.*?', link)
    except:
        imdb_id = False

    if imdb_id:
        imdb_id = imdb_id[0]
    else:
        imdb_id = get_imdb_id_from_title(key, current_list)

    return imdb_id


def get_clean_title(release_title):
    try:
        clean_title = re.findall(r"(.*?)(?:.\|(?:19|20)\d{2}|\.German|\.\d{3,4}p|\.S(?:\d{1,3})\.)", release_title)[
            0].replace(".", "+")
    except:
        clean_title = release_title
    return clean_title


def get_imdb_id_from_title(title, current_list="NoList"):
    title = get_clean_title(title)

    query = quote(title)

    if current_list == 'List_ContentAll_Seasons':
        query = query + "&s=tt&ttype=tv&ref_=fn_tv"
    else:
        query = query + "&s=tt&ttype=ft&ref_=fn_ft"

    request = get_url_headers("https://www.imdb.com/find?q=" + query, headers={'Accept-Language': 'de'})
    search_results = re.findall(r'<td class="result_text"> <a href="\/title\/(tt[0-9]{7,9}).*?" >(.*?)<\/a>(.*?)<\/td>',
                                request["text"])

    imdb_id = False
    if len(search_results) > 0:
        for result in search_results:
            if simplified_search_term_in_title(title, result[1] + "." + result[2]):
                imdb_id = result[0]
                break
    else:
        internal.logger.debug("[IMDb] - %s - Keine ID gefunden" % title)
    return imdb_id


@imdb_id_not_none
def get_poster_link(imdb_id):
    request = get_url("https://www.imdb.com/title/%s/" % imdb_id)
    soup = BeautifulSoup(request, "html5lib")
    try:
        poster_set = soup.find('div', class_='ipc-poster').div.img[
            "srcset"]  # contains links to posters in ascending resolution
        poster_links = [x for x in poster_set.split(" ") if
                        len(x) > 10]  # extract all poster links ignoring resolution info
        poster_link = poster_links[-1]  # get the highest resolution poster
    except:
        poster_link = False
    return poster_link


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
