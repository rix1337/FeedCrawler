# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt allen anderen Modulen den Abruf von IMDb-Daten bereit.

import re
import traceback
from json import loads
from urllib.parse import quote

from bs4 import BeautifulSoup

from feedcrawler.providers import shared_state
from feedcrawler.providers.common_functions import simplified_search_term_in_title
from feedcrawler.providers.url_functions import get_url, get_url_headers


def imdb_id_not_none(f):
    """Decorator that checks if IMDb-Id was passed correctly."""

    def check_imdb_id_not_none(imdb_id=None):
        if not type(imdb_id) == str or not imdb_id.startswith('tt'):
            caller = traceback.extract_stack(f=None, limit=None)[-2]
            detailed_trace = f"In {caller.name}:{caller.lineno}, Aufruf: {caller.line}"
            print(f"Ein Aufruf ohne IMDb-ID ist nicht möglich! - {detailed_trace}")
            shared_state.logger.debug(f"Ein Aufruf ohne IMDb-ID ist nicht möglich! - {detailed_trace}")
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


def get_clean_title(title):
    try:
        extracted_title = re.findall(r"(.*?)(?:.(?!19|20)\d{2}|\.German|.GERMAN|\.\d{3,4}p|\.S(?:\d{1,3}))", title)[0]
        leftover_tags_removed = re.sub(
            r'(|.UNRATED.*|.Unrated.*|.Uncut.*|.UNCUT.*)(|.Directors.Cut.*|.Final.Cut.*|.DC.*|.REMASTERED.*|.EXTENDED.*|.Extended.*|.Theatrical.*|.THEATRICAL.*)',
            "", extracted_title)
        clean_title = leftover_tags_removed.replace(".", " ").strip().replace(" ", "+")

    except:
        clean_title = title
    return clean_title


def get_imdb_id_from_title(title, current_list="NoList", language="de", year_in_title=False):
    title = get_clean_title(title)

    query = quote(title)

    ttype = 'tv' if current_list == 'List_ContentAll_Seasons' else 'ft'
    query += f"&s=tt&ttype={ttype}&ref_=fn_{ttype}"

    imdb_id = False

    request = get_url_headers(f"https://www.imdb.com/find/?q={query}", headers={'Accept-Language': language})

    if request["status_code"] == 200:
        soup = BeautifulSoup(request["text"], "html.parser")
        props = soup.find("script", text=re.compile("props"))
        details = loads(props.string)
        search_results = details['props']['pageProps']['titleResults']['results']

        if len(search_results) > 0:
            for result in search_results:
                year = ""
                if year_in_title:
                    try:
                        year = f" {result['titleReleaseText']}"
                    except KeyError:
                        year = " 9999"
                if simplified_search_term_in_title(title, f"{result['titleNameText']}{year}"):
                    imdb_id = result['id']
                    break
    else:
        print(f"IMDb-Abfrage fehlgeschlagen: {request['status_code']}")
        shared_state.logger.debug(f"IMDb-Abfrage fehlgeschlagen: {request['status_code']}")

    if not imdb_id:
        shared_state.logger.debug(f"[IMDb] - {title.replace('+', ' ')} - Keine ID gefunden")
    return imdb_id


@imdb_id_not_none
def get_poster_link(imdb_id):
    request = get_url(f"https://www.imdb.com/title/{imdb_id}/")
    soup = BeautifulSoup(request, "html.parser")
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
        request = get_url(f"https://www.imdb.com/title/{imdb_id}/")
        soup = BeautifulSoup(request, "html.parser")
        props = soup.find("script", text=re.compile("props"))
        details = loads(props.string)
        languages = details['props']['pageProps']['mainColumnData']['spokenLanguages']['spokenLanguages']
        original_language = languages[0]['id']
    except:
        pass

    if original_language and original_language == "de":
        shared_state.logger.debug(
            f"[IMDb] - {imdb_id} - Original-Sprache ist Deutsch. Breche Suche nach zweisprachigem Release ab!")
        return False

    if not original_language:
        print(f"[IMDb] - {imdb_id} - Original-Sprache nicht ermittelbar")
        shared_state.logger.debug(f"[IMDb] - {imdb_id} - Original-Sprache nicht ermittelbar")

    return original_language


@imdb_id_not_none
def get_episodes(imdb_id):
    episodes = False

    try:
        request = get_url(f"https://www.imdb.com/title/{imdb_id}/episodes?ref_=tt_eps_sm")
        soup = BeautifulSoup(request, "html.parser")
        seasons = soup.find("select", {"id": "bySeason"}).findAll("option")
        if len(seasons) > 0:
            episodes = {}
            for sn in seasons:
                i = 1
                sn = sn["value"]
                eps = []
                request = get_url(f"https://www.imdb.com/title/{imdb_id}/episodes?season={sn}")
                soup = BeautifulSoup(request, "html.parser")
                details = soup.findAll("div", {"itemprop": "episodes"})
                for _ in details:
                    eps.append(i)
                    i += 1
                episodes[int(sn)] = eps
    except:
        pass

    if not episodes:
        print(f"[IMDb] - {imdb_id} - Keine Folgen gefunden")
        shared_state.logger.debug(f"[IMDb] - {imdb_id} - Keine Folgen gefunden")

    return episodes


@imdb_id_not_none
def get_localized_title(imdb_id):
    localized_title = False

    try:
        request = get_url_headers(f"https://www.imdb.com/title/{imdb_id}/", headers={'Accept-Language': 'de'})
        match = re.findall(r'<title>(.*?) \(.*?</title>', request["text"])
        localized_title = match[0]
    except:
        try:
            match = re.findall(r'<title>(.*?) - IMDb</title>', request["text"])
            localized_title = match[0]
        except:
            pass

    if not localized_title:
        print(f"[IMDb] - {imdb_id} - Deutscher Titel nicht ermittelbar")
        shared_state.logger.debug(f"[IMDb] - {imdb_id} - Deutscher Titel nicht ermittelbar")

    return localized_title


@imdb_id_not_none
def get_rating(imdb_id):
    rating = False

    try:
        request = get_url(f"https://www.imdb.com/title/{imdb_id}/")
        soup = BeautifulSoup(request, "html.parser")
        props = soup.find("script", text=re.compile("props"))
        details = loads(props.string)
        rating = details['props']['pageProps']['aboveTheFoldData']['ratingsSummary']['aggregateRating']
    except:
        pass

    if not rating:
        print(f"[IMDb] - {imdb_id} - Bewertungen nicht ermittelbar")
        shared_state.logger.debug(f"[IMDb] - {imdb_id} - Bewertungen nicht ermittelbar")

    return rating


@imdb_id_not_none
def get_votes(imdb_id):
    votes = False

    try:
        request = get_url(f"https://www.imdb.com/title/{imdb_id}/")
        soup = BeautifulSoup(request, "html.parser")
        props = soup.find("script", text=re.compile("props"))
        details = loads(props.string)
        votes = details['props']['pageProps']['aboveTheFoldData']['ratingsSummary']['voteCount']
    except:
        pass

    if not votes:
        print(f"[IMDb] - {imdb_id} - Anzahl der Bewertungen nicht ermittelbar")
        shared_state.logger.debug(f"[IMDb] - {imdb_id} - Anzahl der Bewertungen nicht ermittelbar")

    return votes


@imdb_id_not_none
def get_year(imdb_id):
    year = False

    try:
        request = get_url(f"https://www.imdb.com/title/{imdb_id}/")
        match = re.findall(r'<title>(?:.*?) \(.*?(\d{4}).*</title>', request)
        year = int("".join(re.findall(r'\d+', str(match[0]))))
    except:
        pass

    if not year:
        print(f"[IMDb] - {imdb_id} - Erscheinungsjahr nicht ermittelbar")
        shared_state.logger.debug(f"[IMDb] - {imdb_id} - Erscheinungsjahr nicht ermittelbar")

    return year
