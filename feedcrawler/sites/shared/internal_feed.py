# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul abstrahiert die Feeds aller integrierten Seiten mit Helfer-Funktionen zu einer standardisierten Struktur.
#
#
# Für die self.get_feed_method von "content_all"-Modulen muss der resultierende FakeFeed wie folgt aufgebaut sein:
#
# feed = {
#     'entries': [
#         {
#             'title': 'Release.1.Title-Group',
#             'published': '15.02.2022 / 15:31 Uhr',
#             'content': [
#                 {
#                     'value': """HTML-Inhalt der entweder direkt Download-Links (inklusive Hoster-Bezeichnung)
#                                 enthält, oder Links zu der eigentlichen Seite enthält, auf der die Links zu finden
#                                 sind.
#                                 Der folgende IMDb-Link ist notwendig, um das Release eindeutig einer IMDb-Seite
#                                 zuzuordnen. Der zeichengenaue Aufbau ist wichtig, damit die Feed-Suche den Link
#                                 erkennt: <a href="http://www.imdb.com/title/tt0012345/" 9.9</a>
#                                 Das Dateiformat "mkv" muss ebenfalls zwingend im Text vorhanden sein: mkv"""
#                 }
#             ]
#         },
#         {
#             'title': 'Release.2.Title-Group',
#             'published': '01.01.2000 / 00:10 Uhr',
#             'content': [
#                 {
#                     'value': """HTML-Inhalt der entweder direkt Download-Links (inklusive Hoster-Bezeichnung)
#                                     enthält, oder Links zu der eigentlichen Seite enthält, auf der die Links zu finden
#                                     sind.
#                                     Der folgende IMDb-Link ist notwendig, um das Release eindeutig einer IMDb-Seite
#                                     zuzuordnen. Der zeichengenaue Aufbau ist wichtig, damit die Feed-Suche den Link
#                                     erkennt: <a href="http://www.imdb.com/title/tt0012345/" 9.9</a>
#                                     Das Dateiformat "mkv" muss ebenfalls zwingend im Text vorhanden sein: mkv"""
#                 }
#             ]
#         }
#     ]
# }
#
# Die self.get_download_links_method von "content_all"-Modulen muss folgende Parameter zurückgeben:
# download_links = Liste von Strings, Download-Links zum Release
#
# Hauptaufgabe der self.get_download_links_method ist demnach, die "download_links" aus dem "value" des Feed-"entries"
# eines Releases (nach Hoster-Auswahl in den Einstellungen) zu finden.
#
#
# Für die self.get_feed_method von "content_shows"-Modulen muss der resultierende FakeFeed wie folgt aufgebaut sein:
#
# feed = {
#     'entries': [
#         {
#             'title': 'Release.1.Title-Group',
#             'series_url': 'https://link.zu/website_mit_download_links_des_ersten_releases',
#             'published': '2000-01-30T00:00:00.999Z'},
#         {
#             'title': 'Release.2.Title-Group',
#             'series_url': 'https://link.zu/website_mit_download_links_des_zweiten_releases',
#             'published': '2000-01-30T00:10:00.999Z'}
#     ]
# }
#
# Die self.parse_download_method von "content_shows"-Modulen muss folgende Parameter als Liste zurückgeben:
# title, download_link, language_id, season, episode
# title = String, Der Titel des Releases
# download_link = String, Ein Download-Link zum Release
# language_id = Integer, Die Sprach-ID des Releases (1=Deutsch, 2=Englisch, 0=Sonstige) - Im Zweifel 1
# season = Integer, Die Staffel des Releases - False, wenn unbekannt
# episode = Integer, Die Episode des Releases - False, wenn unbekannt
#
# Hauptaufgabe der self.parse_download_method ist demnach, die "series_url" aus dem Feed zu durchsuchen und den
# ersten passenden Download-Link (nach Hoster-Auswahl in den Einstellungen) zu finden.

import datetime
import json
import re

from bs4 import BeautifulSoup

from feedcrawler import internal
from feedcrawler.common import check_hoster
from feedcrawler.common import check_is_site
from feedcrawler.common import check_valid_release
from feedcrawler.common import rreplace
from feedcrawler.common import simplified_search_term_in_title
from feedcrawler.config import CrawlerConfig
from feedcrawler.myjd import add_decrypt
from feedcrawler.notifiers import notify
from feedcrawler.url import get_redirected_url
from feedcrawler.url import get_url
from feedcrawler.url import get_urls_async
from feedcrawler.url import post_url
from feedcrawler.url import post_url_headers


class FakeFeedParserDict(dict):
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: " + name)


def unused_get_feed_parameter(param):
    return param


def get_download_links(self, content, title):
    unused_get_feed_parameter(title)
    url_hosters = re.findall(r'href="([^"\'>]*)".+?(.+?)<', content)
    return check_download_links(self, url_hosters)


def check_download_links(self, url_hosters):
    links = {}
    for url_hoster in reversed(url_hosters):
        hoster = url_hoster[1].lower().replace('target="_blank">', '').replace(" ", "-").replace("ddownload", "ddl")
        if check_hoster(hoster):
            link = url_hoster[0]
            if self.url in link:
                demasked_link = get_redirected_url(link)
                if demasked_link:
                    link = demasked_link
            links[hoster] = link
    if self.hoster_fallback and not links:
        for url_hoster in reversed(url_hosters):
            hoster = url_hoster[1].lower().replace('target="_blank">', '').replace(" ", "-").replace("ddownload", "ddl")
            link = url_hoster[0]
            if self.url in link:
                demasked_link = get_redirected_url(link)
                if demasked_link:
                    link = demasked_link
            links[hoster] = link
    return list(links.values())


def get_search_results(self, bl_query):
    unused_get_feed_parameter(self)
    hostnames = CrawlerConfig('Hostnames')
    by = hostnames.get('by')
    fx = hostnames.get('fx')
    hw = hostnames.get('hw')
    nk = hostnames.get('nk')

    search_results = []

    config = CrawlerConfig('ContentAll')
    quality = config.get('quality')

    if "480p" not in quality:
        search_quality = "+" + quality
    else:
        search_quality = ""

    if by:
        by_search = 'https://' + by + '/?q=' + bl_query + search_quality
    else:
        by_search = None
    if fx:
        fx_search = 'https://' + fx + '/?s=' + bl_query
    else:
        fx_search = None
    if hw:
        hw_search = 'https://' + hw + '/?s=' + bl_query
    else:
        hw_search = None

    async_results = get_urls_async([by_search, fx_search, hw_search])
    async_results = async_results[0]

    by_results = []
    fx_results = []
    hw_results = []

    for res in async_results:
        if check_is_site(res) == 'BY':
            by_results = by_search_results(res, by)
        elif check_is_site(res) == 'FX':
            fx_results = fx_search_results(fx_content_to_soup(res), bl_query)
        elif check_is_site(res) == 'HW':
            hw_results = hw_search_results(res)

    if nk:
        nk_search = post_url('https://' + nk + "/search",
                             data={'search': bl_query.replace("+", " ") + " " + quality})
        nk_results = nk_search_results(nk_search, 'https://' + nk + '/')
    else:
        nk_results = []

    password = by.split('.')[0]
    for result in by_results:
        if "480p" in quality:
            if "720p" in result[0].lower() or "1080p" in result[0].lower() or "1080i" in result[
                0].lower() or "2160p" in \
                    result[0].lower() or "complete.bluray" in result[0].lower() or "complete.mbluray" in result[
                0].lower() or "complete.uhd.bluray" in result[0].lower():
                continue
        if "xxx" not in result[0].lower():
            search_results.append([result[0], result[1] + "|" + password])

    password = fx.split('.')[0]
    for result in fx_results:
        if "480p" in quality:
            if "720p" in result[0].lower() or "1080p" in result[0].lower() or "1080i" in result[
                0].lower() or "2160p" in \
                    result[0].lower() or "complete.bluray" in result[0].lower() or "complete.mbluray" in result[
                0].lower() or "complete.uhd.bluray" in result[0].lower():
                continue
        search_results.append([result[0], result[1] + "|" + password])

    password = hw.split('.')[0]
    for result in hw_results:
        if "480p" in quality:
            if "720p" in result[0].lower() or "1080p" in result[0].lower() or "1080i" in result[
                0].lower() or "2160p" in \
                    result[0].lower() or "complete.bluray" in result[0].lower() or "complete.mbluray" in result[
                0].lower() or "complete.uhd.bluray" in result[0].lower():
                continue
        if "xxx" not in result[0].lower():
            search_results.append([result[0], result[1] + "|" + password])

    password = nk.split('.')[0].capitalize()
    for result in nk_results:
        if "480p" in quality:
            if "720p" in result[0].lower() or "1080p" in result[0].lower() or "1080i" in result[
                0].lower() or "2160p" in \
                    result[0].lower() or "complete.bluray" in result[0].lower() or "complete.mbluray" in result[
                0].lower() or "complete.uhd.bluray" in result[0].lower():
                continue
        search_results.append([result[0], result[1] + "|" + password])

    return search_results


def add_decrypt_instead_of_download(key, path, download_links, password):
    unused_get_feed_parameter(path)

    if add_decrypt(key.strip(), download_links[0], password):
        return True
    else:
        return False


def by_get_download_links(self, content, title):
    async_link_results = re.findall(r'href="([^"\'>]*)"', content)
    async_link_results = get_urls_async(async_link_results)

    content = []
    links = async_link_results[0]
    for link in links:
        link = BeautifulSoup(link, 'html5lib').find("a", href=re.compile("/go\.php\?"))
        try:
            content.append('href="' + link["href"] + '">' + link.text.replace(" ", "") + '<')
        except:
            pass

    content = "".join(content)
    download_links = get_download_links(self, content, title)
    return download_links


def by_feed_enricher(content):
    base_url = "https://" + CrawlerConfig('Hostnames').get('by')
    content = BeautifulSoup(content, 'html5lib')
    posts = content.findAll("a", href=re.compile("/category/"), text=re.compile("Download"))
    async_results = []
    for post in posts:
        try:
            async_results.append(base_url + post['href'])
        except:
            pass
    async_results = get_urls_async(async_results)
    results = async_results[0]

    entries = []
    if results:
        for result in results:
            try:
                content = []
                details = BeautifulSoup(result, 'html5lib').findAll("td", {"valign": "TOP", "align": "CENTER"})[1]
                title = details.find("small").text
                published = details.find("th", {"align": "RIGHT"}).text
                try:
                    imdb = details.find("a", href=re.compile("imdb.com"))
                    imdb_link = imdb["href"].replace("https://anonym.to/?", "")
                    imdb_score = imdb.text.replace(" ", "").replace("/10", "")
                    if "0.0" in imdb_score:
                        imdb_score = "9.9"
                    content.append('<a href="' + imdb_link + '"' + imdb_score + '</a>')
                except:
                    pass
                links = details.find_all("iframe")
                for link in links:
                    content.append('href="' + link["src"] + '"')

                content = "".join(content)

                entries.append(FakeFeedParserDict({
                    "title": title,
                    "published": published,
                    "content": [FakeFeedParserDict({
                        "value": content + " mkv"})]
                }))
            except:
                pass

    feed = {"entries": entries}
    feed = FakeFeedParserDict(feed)
    return feed


def by_search_results(content, base_url):
    content = BeautifulSoup(content, 'html5lib')
    posts = content.findAll("a", href=re.compile("/category/"))
    results = []
    for post in posts:
        try:
            title = post.text.replace(" ", ".")
            link = "https://" + base_url + post['href']
            results.append([title, link])
        except:
            pass
    return results


def by_page_download_link(self, download_link, key):
    unused_get_feed_parameter(key)
    by = self.hostnames.get('by')
    download_link = get_url(download_link)
    soup = BeautifulSoup(download_link, 'html5lib')
    links = soup.find_all("iframe")
    async_link_results = []
    for link in links:
        link = link["src"]
        if 'https://' + by in link:
            async_link_results.append(link)
    async_link_results = get_urls_async(async_link_results)
    links = async_link_results[0]
    url_hosters = []
    for link in links:
        if link:
            link = BeautifulSoup(link, 'html5lib').find("a", href=re.compile("/go\.php\?"))
            if link:
                url_hosters.append([link["href"], link.text.replace(" ", "")])
    return check_download_links(self, url_hosters)


def fx_content_to_soup(content):
    content = BeautifulSoup(content, 'html5lib')
    return content


def fx_get_download_links(self, content, title):
    unused_get_feed_parameter(self)
    try:
        try:
            content = BeautifulSoup(content, 'html5lib')
        except:
            content = BeautifulSoup(str(content), 'html5lib')
        try:
            download_links = [content.find("a", text=re.compile(r".*" + title + r".*"))['href']]
        except:
            fx = CrawlerConfig('Hostnames').get('fx')
            download_links = re.findall(re.compile('"(.+?(?:filecrypt|safe.' + fx + ').+?)"'), str(content))
    except:
        return False
    return download_links


def fx_feed_enricher(feed):
    feed = BeautifulSoup(feed, 'html5lib')
    fx = CrawlerConfig('Hostnames').get('fx')
    articles = feed.findAll("article")
    entries = []

    for article in articles:
        try:
            article = BeautifulSoup(str(article), 'html5lib')
            titles = article.findAll("a", href=re.compile("(filecrypt|safe." + fx + ")"))
            for title in titles:
                title = title.text.encode("ascii", errors="ignore").decode().replace("/", "").replace(" ", ".")
                if title:
                    if "download" in title.lower():
                        try:
                            title = str(article.find("strong", text=re.compile(r".*Release.*")).nextSibling)
                        except:
                            continue
                    published = ""
                    dates = article.findAll("time")
                    for date in dates:
                        published = date["datetime"]
                    entries.append(FakeFeedParserDict({
                        "title": title,
                        "published": published,
                        "content": [
                            FakeFeedParserDict({
                                "value": str(article) + " mkv"
                            })]
                    }))
        except:
            print(u"FX hat den Feed angepasst. Parsen teilweise nicht möglich!")
            continue

    feed = {"entries": entries}
    feed = FakeFeedParserDict(feed)
    return feed


def fx_search_results(content, search_term):
    fx = CrawlerConfig('Hostnames').get('fx')
    articles = content.find("main").find_all("article")
    result_urls = []
    for article in articles:
        if simplified_search_term_in_title(search_term, article.find("h2").text):
            url = article.find("a")["href"]
            if url:
                result_urls.append(url)

    items = []

    if result_urls:
        results = []
        for url in result_urls:
            results.append(get_url(url))

        for result in results:
            article = BeautifulSoup(str(result), 'html5lib')
            titles = article.find_all("a", href=re.compile("(filecrypt|safe." + fx + ")"))
            for title in titles:
                try:
                    link = article.find("link", rel="canonical")["href"]
                    title = title.text.encode("ascii", errors="ignore").decode().replace("/", "").replace(" ", ".")
                    if title and "-fun" in title.lower():
                        if "download" in title.lower():
                            try:
                                title = str(content.find("strong", text=re.compile(r".*Release.*")).nextSibling)
                            except:
                                continue
                        items.append([title, link])
                except:
                    pass
    return items


def hw_get_download_links(self, content, title):
    try:
        try:
            content = BeautifulSoup(content, 'html5lib')
        except:
            content = BeautifulSoup(str(content), 'html5lib')
        download_links = content.findAll("a", href=re.compile('filecrypt'))
    except:
        return False

    links_string = ""
    for link in download_links:
        links_string += str(link)

    return get_download_links(self, links_string, title)


def hw_feed_enricher(feed):
    feed = BeautifulSoup(feed, 'html5lib')
    articles = feed.findAll("article")
    entries = []

    for article in articles:
        try:
            title = article.find("h2", {"class": "entry-title"}).text.strip()
            media_post = article.find("strong", text="Format: ")
            if title and media_post:
                published = article.find("p", {"class": "blog-post-meta"}).text.split("|")[0].strip()
                entries.append(FakeFeedParserDict({
                    "title": title,
                    "published": published,
                    "content": [
                        FakeFeedParserDict({
                            "value": str(article)
                        })]
                }))
        except:
            print(u"HW hat den Feed angepasst. Parsen teilweise nicht möglich!")
            continue

    feed = {"entries": entries}
    feed = FakeFeedParserDict(feed)
    return feed


def hw_search_results(content):
    content = BeautifulSoup(content, 'html5lib')
    posts = content.findAll("a", href=re.compile(r"^(?!.*\/category).*\/(filme|serien).*(?!.*#comments.*)$"))
    results = []
    for post in posts:
        try:
            title = post.text.strip()
            link = post['href']
            if "#comments-title" not in link:
                results.append([title, link])
        except:
            pass
    return results


def ff_get_download_links(self, content, title):
    unused_get_feed_parameter(title)
    try:
        try:
            content = BeautifulSoup(content, 'html5lib')
        except:
            content = BeautifulSoup(str(content), 'html5lib')
        links = content.findAll("div", {'class': 'row'})[1].findAll('a')
        download_link = False
        for link in links:
            if check_hoster(link.text.replace('\n', '')):
                download_link = "https://" + self.url + link['href']
                break
    except:
        return False

    return [download_link]


def ff_feed_enricher(releases):
    entries = []
    if releases:
        try:
            base_url = CrawlerConfig('Hostnames').get('ff')
            page = BeautifulSoup(releases, 'html5lib')
            day = page.find("li", {"class": "active"}).find("a")["href"].replace("/updates/", "").replace("#list", "")
            movies = page.findAll("div", {"class": "sra"}, style=re.compile("order"))

            for movie in movies:
                movie_url = "https://" + base_url + movie.find("a")["href"]
                details = BeautifulSoup(get_url(movie_url), 'html5lib')
                api_secret = re.sub(r"[\n\t\s]*", "",
                                    str(details.find("script", text=re.compile(".*initMovie.*"))).strip()).replace(
                    "<script>initMovie(\'", "").replace("\',\'\',\'ALL\');</script>", "")
                epoch = str(datetime.datetime.now().timestamp()).replace('.', '')[:-3]
                api_url = "https://" + base_url + '/api/v1/' + api_secret + '?lang=ALL&_=' + epoch
                response = get_url(api_url)
                info = BeautifulSoup(json.loads(response)["html"], 'html5lib')

                releases = movie.findAll("a", href=re.compile("^(?!.*(genre))"), text=re.compile("\S"))
                for release in releases:
                    title = release.text.strip()
                    time = movie.find("span", {"class": "lsf-icon timed"}).text
                    published = day + "|" + time

                    imdb_infos = details.find("ul", {"class": "info"})

                    try:
                        imdb_link = str(imdb_infos.find("a")["href"])
                        imdb_rating = str(float(imdb_infos.find("i").text.strip()))
                        imdb_info = 'href="' + imdb_link + ' ' + imdb_rating + '/10</a>'
                    except:
                        imdb_info = ""
                        pass
                    release_infos = info.findAll("div", {"class": "entry"})
                    release_info = False
                    for check_info in release_infos:
                        if check_info.find("span", text=title):
                            release_info = str(check_info)

                    if release_info:
                        content = imdb_info + " " + release_info

                        entries.append(FakeFeedParserDict({
                            "title": title,
                            "content": [FakeFeedParserDict({
                                "value": content + " mkv"})],
                            "published": published
                        }))
        except Exception as e:
            internal.logger.debug("FF-Feed konnte nicht gelesen werden: " + str(e))
            pass

    feed = {"entries": entries}
    feed = FakeFeedParserDict(feed)
    return feed


def nk_feed_enricher(content):
    base_url = "https://" + CrawlerConfig('Hostnames').get('nk')
    content = BeautifulSoup(content, 'html5lib')
    posts = content.findAll("a", {"class": "btn"}, href=re.compile("/release/"))
    async_results = []
    for post in posts:
        try:
            async_results.append(base_url + post['href'])
        except:
            pass
    async_results = get_urls_async(async_results)[0]

    entries = []
    if async_results:
        for result in async_results:
            try:
                content = []
                details = BeautifulSoup(result, 'html5lib').find("div", {"class": "article"})
                title = details.find("span", {"class": "subtitle"}).text
                published = details.find("p", {"class": "meta"}).text
                content.append("mkv ")
                try:
                    imdb = details.find("a", href=re.compile("imdb.com"))["href"]
                    content.append('<a href="' + imdb + '" 9,9</a>')
                except:
                    pass
                links = details.find_all("a", href=re.compile("/go/"))
                for link in links:
                    content.append('href="' + base_url + link["href"] + '">' + link.text + '<')
                content = "".join(content)

                entries.append(FakeFeedParserDict({
                    "title": title,
                    "published": published,
                    "content": [FakeFeedParserDict({
                        "value": content})]
                }))
            except:
                pass

    feed = {"entries": entries}
    feed = FakeFeedParserDict(feed)
    return feed


def nk_search_results(content, base_url):
    content = BeautifulSoup(content, 'html5lib')
    posts = content.findAll("a", {"class": "btn"}, href=re.compile("/release/"))
    results = []
    for post in posts:
        try:
            title = post.parent.parent.parent.find("span", {"class": "subtitle"}).text
            link = base_url + post['href']
            results.append([title, link])
        except:
            pass
    return results


def nk_page_download_link(self, download_link, key):
    unused_get_feed_parameter(key)
    nk = self.hostnames.get('nk')
    download_link = get_url(download_link)
    soup = BeautifulSoup(download_link, 'html5lib')
    url_hosters = []
    hosters = soup.find_all("a", href=re.compile("/go/"))
    for hoster in hosters:
        url_hosters.append(['https://' + nk + hoster["href"], hoster.text])
    return check_download_links(self, url_hosters)


def ww_post_url_headers(url, headers=False):
    try:
        if not headers:
            headers = {}
        payload = url.split("|")
        url = payload[0]
        referer = payload[0].replace("/ajax", payload[1])
        data = payload[2]
        headers["Referer"] = referer
        response = post_url_headers(url, headers, data)
        if not response["text"] or response["status_code"] is not (200 or 304) or not '<span class="main-rls">' in \
                                                                                      response["text"]:
            if not internal.ww_blocked:
                print(u"WW hat den Feed-Anruf blockiert. Eine spätere Anfrage hat möglicherweise Erfolg!")
                internal.ww_blocked = True
            return ""
        return response
    except:
        return ""


def ww_get_download_links(self, content, title):
    base_url = "https://" + CrawlerConfig('Hostnames').get('ww')
    content = content.replace("mkv|", "")
    download_links = []
    try:
        response = get_url(content)
        if not response or "NinjaFirewall 429" in response:
            if not internal.ww_blocked:
                print(
                    u"WW hat den Link-Abruf für " + title + " blockiert. Eine spätere Anfrage hat möglicherweise Erfolg!")
                internal.ww_blocked = True
            return False
        links = BeautifulSoup(response, 'html5lib').findAll("div", {"id": "download-links"})
        for link in links:
            hoster = link.text
            if 'Direct Download 100 MBit/s' not in hoster:
                url = base_url + link.find("a")["href"]
                download_links.append('href="' + url + '" ' + hoster + '<')
        download_links = "".join(download_links)

        download_links = get_download_links(self, download_links, title)
        return download_links
    except:
        return False


def ww_feed_enricher(content):
    base_url = "https://" + CrawlerConfig('Hostnames').get('ww')
    try:
        content = BeautifulSoup(content, 'html5lib')
    except:
        content = BeautifulSoup(content["text"], 'html5lib')
    posts = content.findAll("li")
    entries = []
    if posts:
        for post in posts:
            try:
                link = post.findAll("a", href=re.compile("/download"))[1]
                title = link.nextSibling.nextSibling.strip()
                published = post.find("span", {"class": "main-date"}).text.replace("\n", "")
                content = "mkv|" + base_url + link["href"]

                entries.append(FakeFeedParserDict({
                    "title": title,
                    "published": published,
                    "content": [FakeFeedParserDict({
                        "value": content})]
                }))
            except:
                pass

    feed = {"entries": entries}
    feed = FakeFeedParserDict(feed)
    return feed


def j_releases_to_feedparser_dict(releases, list_type, base_url, check_seasons_or_episodes):
    releases = json.loads(releases)
    entries = []

    for release in releases:
        if check_seasons_or_episodes:
            try:
                if list_type == 'seasons' and release['episode']:
                    continue
                elif list_type == 'episodes' and not release['episode']:
                    continue
            except:
                continue
        title = release['name']
        series_url = base_url + '/serie/' + release["_media"]['slug']
        published = release['createdAt']

        entries.append(FakeFeedParserDict({
            "title": title,
            "series_url": series_url,
            "published": published
        }))

    feed = {"entries": entries}
    feed = FakeFeedParserDict(feed)
    return feed


def j_parse_download(self, series_url, title, language_id):
    if not check_valid_release(title, self.retail_only, self.hevc_retail):
        internal.logger.debug(title + u" - Release ignoriert (Gleiche oder bessere Quelle bereits vorhanden)")
        return False
    if self.filename == 'List_ContentAll_Seasons':
        if not self.config.get("seasonpacks"):
            staffelpack = re.search(r"s\d.*(-|\.).*s\d", title.lower())
            if staffelpack:
                internal.logger.debug(
                    "%s - Release ignoriert (Staffelpaket)" % title)
                return False
        if not re.search(self.seasonssource, title.lower()):
            internal.logger.debug(title + " - Release hat falsche Quelle")
            return False
    try:
        series_info = get_url(series_url)
        series_id = re.findall(r'data-mediaid="(.*?)"', series_info)[0]
        api_url = 'https://' + self.url + '/api/media/' + series_id + '/releases'

        response = get_url(api_url)
        seasons = json.loads(response)
        for season in seasons:
            season = seasons[season]
            for item in season['items']:
                if item['name'] == title:
                    valid = False
                    for hoster in item['hoster']:
                        if hoster:
                            if check_hoster(hoster):
                                valid = True
                    if not valid and not self.hoster_fallback:
                        storage = self.db.retrieve_all(title)
                        if 'added' not in storage and 'notdl' not in storage:
                            wrong_hoster = '[' + self._INTERNAL_NAME + ' / Hoster fehlt] - ' + title
                            if 'wrong_hoster' not in storage:
                                print(wrong_hoster)
                                self.db.store(title, 'wrong_hoster')
                                notify([wrong_hoster])
                            else:
                                internal.logger.debug(wrong_hoster)
                            return False
                    else:
                        return [title, series_url, language_id, False, False]
    except:
        print(self._INTERNAL_NAME + u" hat die Serien-API angepasst. Breche Download-Prüfung ab!")
        return False


def sf_releases_to_feedparser_dict(releases, list_type, base_url, check_seasons_or_episodes):
    content = BeautifulSoup(releases, 'html5lib')
    releases = content.findAll("div", {"class": "row"}, style=re.compile("order"))
    entries = []

    for release in releases:
        a = release.find("a", href=re.compile("/"))
        title = a.text
        is_episode = re.match(r'.*(S\d{1,3}E\d{1,3}).*', title)
        if check_seasons_or_episodes:
            try:
                if list_type == 'seasons' and is_episode:
                    continue
                elif list_type == 'episodes' and not is_episode:
                    continue
            except:
                continue

        series_url = base_url + a['href']
        published = release.find("div", {"class": "datime"}).text

        entries.append(FakeFeedParserDict({
            "title": title,
            "series_url": series_url,
            "published": published
        }))

    feed = {"entries": entries}
    feed = FakeFeedParserDict(feed)
    return feed


def sf_parse_download(self, series_url, title, language_id):
    if not check_valid_release(title, self.retail_only, self.hevc_retail):
        internal.logger.debug(title + u" - Release ignoriert (Gleiche oder bessere Quelle bereits vorhanden)")
        return False
    if self.filename == 'List_ContentAll_Seasons':
        if not self.config.get("seasonpacks"):
            staffelpack = re.search(r"s\d.*(-|\.).*s\d", title.lower())
            if staffelpack:
                internal.logger.debug(
                    "%s - Release ignoriert (Staffelpaket)" % title)
                return False
        if not re.search(self.seasonssource, title.lower()):
            internal.logger.debug(title + " - Release hat falsche Quelle")
            return False
    try:
        if language_id == 2:
            lang = 'EN'
        else:
            lang = 'DE'
        epoch = str(datetime.datetime.now().timestamp()).replace('.', '')[:-3]
        season_page = get_url(series_url)
        season_details = re.findall(r"initSeason\('(.+?)\',(.+?),", season_page)[-1]
        season_id = season_details[0]
        season_nr = season_details[1]

        sf = CrawlerConfig('Hostnames').get('sf')

        api_url = 'https://' + sf + '/api/v1/' + season_id + '/season/' + season_nr + '?lang=' + lang + '&_=' + epoch

        response = get_url(api_url)
        info = json.loads(response)

        is_episode = re.findall(r'.*\.(s\d{1,3}e\d{1,3})\..*', title, re.IGNORECASE)
        if is_episode:
            episode_string = re.findall(r'.*S\d{1,3}(E\d{1,3}).*', is_episode[0])[0].lower()
            season_string = re.findall(r'.*(S\d{1,3})E\d{1,3}.*', is_episode[0])[0].lower()
            season_title = rreplace(title.lower().replace(episode_string, ''), "-", ".*", 1).lower().replace(
                ".repack", "")
            season_title = season_title.replace(".untouched", ".*").replace(".dd+51", ".dd.51")
            episode = str(int(episode_string.replace("e", "")))
            season = str(int(season_string.replace("s", "")))
            episode_name = re.findall(r'.*\.s\d{1,3}(\..*).german', season_title, re.IGNORECASE)
            if episode_name:
                season_title = season_title.replace(episode_name[0], '')
            codec_tags = [".h264", ".x264"]
            for tag in codec_tags:
                season_title = season_title.replace(tag, ".*264")
            web_tags = [".web-rip", ".webrip", ".webdl", ".web-dl"]
            for tag in web_tags:
                season_title = season_title.replace(tag, ".web.*")
        else:
            season = False
            episode = False
            season_title = title
            multiple_episodes = re.findall(r'(e\d{1,3}-e*\d{1,3}\.)', season_title, re.IGNORECASE)
            if multiple_episodes:
                season_title = season_title.replace(multiple_episodes[0], '.*')

        content = BeautifulSoup(info['html'], 'html5lib')
        releases = content.find("small", text=re.compile(season_title, re.IGNORECASE)).parent.parent.parent
        links = releases.findAll("div", {'class': 'row'})[1].findAll('a')
        download_link = False
        for link in links:
            if check_hoster(link.text.replace('\n', '')):
                download_link = "https://" + self.url + link['href']
                break
        if not download_link and not self.hoster_fallback:
            storage = self.db.retrieve_all(title)
            if 'added' not in storage and 'notdl' not in storage:
                wrong_hoster = '[SF/Hoster fehlt] - ' + title
                if 'wrong_hoster' not in storage:
                    print(wrong_hoster)
                    self.db.store(title, 'wrong_hoster')
                    notify([wrong_hoster])
                else:
                    internal.logger.debug(wrong_hoster)
                return False
        else:
            return [title, download_link, language_id, season, episode]
    except:
        print(u"SF hat die Serien-API angepasst. Breche Download-Prüfung ab!")
        return False
