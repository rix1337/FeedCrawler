# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import datetime
import json
import re
from bs4 import BeautifulSoup

from rsscrawler.common import add_decrypt
from rsscrawler.common import check_hoster
from rsscrawler.common import check_is_site
from rsscrawler.common import check_valid_release
from rsscrawler.common import rreplace
from rsscrawler.config import RssConfig
from rsscrawler.notifiers import notify
from rsscrawler.url import get_redirected_url
from rsscrawler.url import get_url
from rsscrawler.url import get_urls_async
from rsscrawler.url import post_url
from rsscrawler.url import post_url_headers


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
        if check_hoster(hoster, self.configfile):
            link = url_hoster[0]
            if self.url in link:
                demasked_link = get_redirected_url(link, self.configfile, self.dbfile, self.scraper)
                if demasked_link:
                    link = demasked_link
            links[hoster] = link
    if self.hoster_fallback and not links:
        for url_hoster in reversed(url_hosters):
            hoster = url_hoster[1].lower().replace('target="_blank">', '').replace(" ", "-").replace("ddownload", "ddl")
            link = url_hoster[0]
            if self.url in link:
                demasked_link = get_redirected_url(link, self.configfile, self.dbfile, self.scraper)
                if demasked_link:
                    link = demasked_link
            links[hoster] = link
    return list(links.values())


def get_search_results(self, bl_query):
    hostnames = RssConfig('Hostnames', self.configfile)
    by = hostnames.get('by')
    dw = hostnames.get('dw')
    fx = hostnames.get('fx')
    nk = hostnames.get('nk')

    search_results = []

    config = RssConfig('MB', self.configfile)
    quality = config.get('quality')

    if "480p" not in quality:
        search_quality = "+" + quality
    else:
        search_quality = ""

    if by:
        by_search = 'https://' + by + '/?q=' + bl_query + search_quality
    else:
        by_search = None
    if dw:
        dw_search = 'https://' + dw + '/?kategorie=Movies&search=' + bl_query + search_quality
    else:
        dw_search = None
    if fx:
        fx_search = 'https://' + fx + '/?s=' + bl_query
    else:
        fx_search = None

    async_results = get_urls_async([by_search, dw_search, fx_search], self.configfile, self.dbfile, self.scraper)
    scraper = async_results[1]
    async_results = async_results[0]

    by_results = []
    dw_results = []
    fx_results = []

    for res in async_results:
        if check_is_site(res, self.configfile) == 'BY':
            by_results = by_search_results(res, by)
        elif check_is_site(res, self.configfile) == 'DW':
            dw_results = dw_search_results(res, dw)
        elif check_is_site(res, self.configfile) == 'FX':
            fx_results = fx_search_results(fx_content_to_soup(res), self.configfile, self.dbfile, scraper)

    if nk:
        nk_search = post_url('https://' + nk + "/search", self.configfile, self.dbfile,
                             data={'search': bl_query.replace("+", " ") + " " + quality})
        nk_results = nk_search_results(nk_search, 'https://' + nk + '/')
    else:
        nk_results = []

    password = by
    for result in by_results:
        if "480p" in quality:
            if "720p" in result[0].lower() or "1080p" in result[0].lower() or "1080i" in result[
                0].lower() or "2160p" in \
                    result[0].lower() or "complete.bluray" in result[0].lower() or "complete.mbluray" in result[
                0].lower() or "complete.uhd.bluray" in result[0].lower():
                continue
        if "xxx" not in result[0].lower():
            search_results.append([result[0], result[1] + "|" + password])

    password = dw
    for result in dw_results:
        if "480p" in quality:
            if "720p" in result[0].lower() or "1080p" in result[0].lower() or "1080i" in result[
                0].lower() or "2160p" in \
                    result[0].lower() or "complete.bluray" in result[0].lower() or "complete.mbluray" in result[
                0].lower() or "complete.uhd.bluray" in result[0].lower():
                continue
        search_results.append([result[0], result[1] + "|" + password])

    for result in fx_results:
        if "480p" in quality:
            if "720p" in result[0].lower() or "1080p" in result[0].lower() or "1080i" in result[
                0].lower() or "2160p" in \
                    result[0].lower() or "complete.bluray" in result[0].lower() or "complete.mbluray" in result[
                0].lower() or "complete.uhd.bluray" in result[0].lower():
                continue
        if "-low" not in result[0].lower():
            search_results.append([result[0], result[1]])

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


def add_decrypt_instead_of_download(configfile, dbfile, device, key, path, download_links, password):
    unused_get_feed_parameter(configfile)
    unused_get_feed_parameter(path)

    if add_decrypt(key, download_links[0], password, dbfile):
        return device
    else:
        return False


def by_get_download_links(self, content, title):
    async_link_results = re.findall(r'href="([^"\'>]*)"', content)
    async_link_results = get_urls_async(async_link_results, self.configfile, self.dbfile, self.scraper)

    content = []
    links = async_link_results[0]
    for link in links:
        link = BeautifulSoup(link, 'lxml').find("a", href=re.compile("/go\.php\?"))
        try:
            content.append('href="' + link["href"] + '">' + link.text.replace(" ", "") + '<')
        except:
            pass

    content = "".join(content)
    download_links = get_download_links(self, content, title)
    return download_links


def by_feed_enricher(self, content):
    base_url = "https://" + RssConfig('Hostnames', self.configfile).get('by')
    content = BeautifulSoup(content, 'lxml')
    posts = content.findAll("a", href=re.compile("/category/"), text=re.compile("Download"))
    async_results = []
    for post in posts:
        try:
            async_results.append(base_url + post['href'])
        except:
            pass
    async_results = get_urls_async(async_results, self.configfile, self.dbfile, self.scraper)
    results = async_results[0]

    entries = []
    if results:
        for result in results:
            try:
                content = []
                details = BeautifulSoup(result, 'lxml').findAll("td", {"valign": "TOP", "align": "CENTER"})[1]
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
    content = BeautifulSoup(content, 'lxml')
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
    download_link = get_url(download_link, self.configfile, self.dbfile)
    soup = BeautifulSoup(download_link, 'lxml')
    links = soup.find_all("iframe")
    async_link_results = []
    for link in links:
        link = link["src"]
        if 'https://' + by in link:
            async_link_results.append(link)
    async_link_results = get_urls_async(async_link_results, self.configfile, self.dbfile)
    links = async_link_results[0]
    url_hosters = []
    for link in links:
        if link:
            link = BeautifulSoup(link, 'lxml').find("a", href=re.compile("/go\.php\?"))
            if link:
                url_hosters.append([link["href"], link.text.replace(" ", "")])
    return check_download_links(self, url_hosters)


def dw_get_download_links(self, content, title):
    unused_get_feed_parameter(title)
    try:
        download_link = False
        hosters = re.findall(r'HOSTERS="(.*)"', content)[0].split("|")
        for hoster in hosters:
            hoster = hoster.lower().replace("ddownload", "ddl")
            if check_hoster(hoster, self.configfile):
                download_link = re.findall(r'DOWNLOADLINK="(.*)"HOSTERS="', content)[0]
        if self.hoster_fallback and not download_link:
            download_link = re.findall(r'DOWNLOADLINK="(.*)"HOSTERS="', content)[0]
    except:
        return False
    return [download_link]


def dw_feed_enricher(self, content):
    base_url = "https://" + RssConfig('Hostnames', self.configfile).get('dw')
    content = BeautifulSoup(content, 'lxml')
    posts = content.findAll("a", href=re.compile("download/"))
    href_by_id = {}
    async_results = []
    for post in posts:
        try:
            post_id = post['href'].replace("download/", "").split("/")[0]
            post_link = base_url + "/" + post['href']
            post_hosters = post.parent.findAll("img", src=re.compile(r"images/icon_hoster"))
            hosters = []
            for hoster in post_hosters:
                hosters.append(hoster["title"].replace("Download bei ", ""))
            hosters = "|".join(hosters)
            href_by_id[post_id] = {
                "hosters": hosters,
                "link": post_link
            }
            async_results.append(post_link)
        except:
            pass
    async_results = get_urls_async(async_results, self.configfile, self.dbfile, self.scraper)
    results = async_results[0]

    entries = []
    if results:
        for result in results:
            try:
                content = []
                details = BeautifulSoup(result, 'lxml')
                title = details.title.text.split(' //')[0].replace("*mirror*", "").strip()
                post_id = details.find("a", {"data-warezkorb": re.compile(r"\d*")})["data-warezkorb"]
                details = details.findAll("div", {"class": "row"})[3]
                published = details.findAll("td")[1].text.replace("Datum", "")
                try:
                    imdb = details.findAll("td")[6].find("a")
                    imdb_link = imdb["href"]
                    imdb_score = imdb.find("b").text.replace(" ", "").replace("/10", "")
                    if "0.0" in imdb_score:
                        imdb_score = "9.9"
                    content.append('<a href="' + imdb_link + '"' + imdb_score + '</a>')
                except:
                    pass

                content.append('DOWNLOADLINK="' + href_by_id[post_id]["link"] + '"')
                content.append('HOSTERS="' + href_by_id[post_id]["hosters"] + '"')

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


def dw_search_results(content, base_url):
    content = BeautifulSoup(content, 'lxml')
    posts = content.findAll("a", href=re.compile("download/"))
    results = []
    for post in posts:
        try:
            title = post.text.strip()
            link = "https://" + base_url + '/' + post['href']
            results.append([title, link + "|" + title])
        except:
            pass
    return results


def dw_mirror(self, title):
    hostnames = RssConfig('Hostnames', self.configfile)
    dw = hostnames.get('dw')

    if dw:
        dw_search = 'https://' + dw + '/?search=' + title

        dw_results = get_url(dw_search, self.configfile, self.dbfile, self.scraper)
        dw_results = dw_search_results(dw_results, dw)

        for result in dw_results:
            return [result[1].split("|")[0]]

    return False


def dw_page_download_link(self, download_link, key):
    unused_get_feed_parameter(self)
    unused_get_feed_parameter(key)
    return [download_link]


def fx_content_to_soup(content):
    content = BeautifulSoup(content, 'lxml')
    return content


def fx_get_download_links(self, content, title):
    hostnames = RssConfig('Hostnames', self.configfile)
    try:
        try:
            content = BeautifulSoup(content, 'lxml')
        except:
            content = BeautifulSoup(str(content), 'lxml')
        try:
            download_links = [content.find("a", text=re.compile(r".*" + title + r".*"))['href']]
        except:
            download_links = re.findall(r'"(https://.+?filecrypt.cc.+?)"', str(content))
    except:
        return False
    return download_links


def fx_feed_enricher(self, feed):
    feed = BeautifulSoup(feed, 'lxml')
    articles = feed.findAll("article")
    entries = []

    for article in articles:
        try:
            article = BeautifulSoup(str(article), 'lxml')
            titles = article.findAll("a", href=re.compile("filecrypt"))
            for title in titles:
                title = title.text.encode("ascii", errors="ignore").decode().replace("/", "")
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


def fx_search_results(content, configfile, dbfile, scraper):
    articles = content.find("main").find_all("article")
    result_urls = []
    for article in articles:
        url = article.find("a")["href"]
        if url:
            result_urls.append(url)

    items = []

    if result_urls:
        results = []
        for url in result_urls:
            results.append(get_url(url, configfile, dbfile, scraper))

        for result in results:
            article = BeautifulSoup(str(result), 'lxml')
            titles = article.find_all("a", href=re.compile("filecrypt"))
            for title in titles:
                link = article.find("link", rel="canonical")["href"]
                title = title.text.encode("ascii", errors="ignore").decode().replace("/", "")
                if title:
                    if "download" in title.lower():
                        try:
                            title = str(content.find("strong", text=re.compile(r".*Release.*")).nextSibling)
                        except:
                            continue
                    items.append([title, link + "|" + title])
    return items


def nk_feed_enricher(self, content):
    base_url = "https://" + RssConfig('Hostnames', self.configfile).get('nk')
    content = BeautifulSoup(content, 'lxml')
    posts = content.findAll("a", {"class": "btn"}, href=re.compile("/release/"))
    async_results = []
    for post in posts:
        try:
            async_results.append(base_url + post['href'])
        except:
            pass
    async_results = get_urls_async(async_results, self.configfile, self.dbfile, self.scraper)[0]

    entries = []
    if async_results:
        for result in async_results:
            try:
                content = []
                details = BeautifulSoup(result, 'lxml').find("div", {"class": "article"})
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
    content = BeautifulSoup(content, 'lxml')
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
    download_link = get_url(download_link, self.configfile, self.dbfile)
    soup = BeautifulSoup(download_link, 'lxml')
    url_hosters = []
    hosters = soup.find_all("a", href=re.compile("/go/"))
    for hoster in hosters:
        url_hosters.append(['https://' + nk + hoster["href"], hoster.text])
    return check_download_links(self, url_hosters)


def ww_post_url_headers(url, configfile, dbfile, headers=False, scraper=False):
    try:
        if not headers:
            headers = {}
        payload = url.split("|")
        url = payload[0]
        referer = payload[0].replace("/ajax", payload[1])
        data = payload[2]
        headers["Referer"] = referer
        response = post_url_headers(url, configfile, dbfile, headers, data, scraper)
        if not response[0].text or response[0].status_code is not (200 or 304) or not '<span class="main-rls">' in \
                                                                                      response[0].text:
            print(u"WW hat den Feed-Anruf blockiert. Eine spätere Anfrage hat möglicherweise Erfolg!")
            return ""
        return response
    except:
        return ""


def ww_get_download_links(self, content, title):
    base_url = "https://" + RssConfig('Hostnames', self.configfile).get('ww')
    content = content.replace("mkv|", "")
    download_links = []
    try:
        response = get_url(content, self.configfile, self.dbfile, self.scraper)
        if not response or "NinjaFirewall 429" in response:
            print(u"WW hat den Link-Abruf für " + title + " blockiert. Eine spätere Anfrage hat möglicherweise Erfolg!")
            return False
        links = BeautifulSoup(response, 'lxml').findAll("div", {"id": "download-links"})
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


def ww_feed_enricher(self, content):
    base_url = "https://" + RssConfig('Hostnames', self.configfile).get('ww')
    content = BeautifulSoup(content, 'lxml')
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
    if not check_valid_release(title, self.retail_only, self.hevc_retail, self.dbfile):
        self.log_debug(title + u" - Release ignoriert (Gleiche oder bessere Quelle bereits vorhanden)")
        return False
    if self.filename == 'MB_Staffeln':
        if not self.config.get("seasonpacks"):
            staffelpack = re.search(r"s\d.*(-|\.).*s\d", title.lower())
            if staffelpack:
                self.log_debug(
                    "%s - Release ignoriert (Staffelpaket)" % title)
                return False
        if not re.search(self.seasonssource, title.lower()):
            self.log_debug(title + " - Release hat falsche Quelle")
            return False
    try:
        series_info = get_url(series_url, self.configfile, self.dbfile)
        series_id = re.findall(r'data-mediaid="(.*?)"', series_info)[0]
        api_url = 'https://' + self.url + '/api/media/' + series_id + '/releases'

        response = get_url(api_url, self.configfile, self.dbfile, self.scraper)
        seasons = json.loads(response)
        for season in seasons:
            season = seasons[season]
            for item in season['items']:
                if item['name'] == title:
                    valid = False
                    for hoster in item['hoster']:
                        if hoster:
                            if check_hoster(hoster, self.configfile):
                                valid = True
                    if not valid and not self.hoster_fallback:
                        storage = self.db.retrieve_all(title)
                        if 'added' not in storage and 'notdl' not in storage:
                            wrong_hoster = '[SJ/Hoster fehlt] - ' + title
                            if 'wrong_hoster' not in storage:
                                print(wrong_hoster)
                                self.db.store(title, 'wrong_hoster')
                                notify([wrong_hoster], self.configfile)
                            else:
                                self.log_debug(wrong_hoster)
                            return False
                    else:
                        return [title, series_url, language_id, False, False]
    except:
        print(self._INTERNAL_NAME + u" hat die Serien-API angepasst. Breche Download-Prüfung ab!")
        return False


def sf_releases_to_feedparser_dict(releases, list_type, base_url, check_seasons_or_episodes):
    content = BeautifulSoup(releases, 'lxml')
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

        series_url = rreplace(base_url + '/api/v1' + a['href'], '/', '/season/', 1)
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
    if not check_valid_release(title, self.retail_only, self.hevc_retail, self.dbfile):
        self.log_debug(title + u" - Release ignoriert (Gleiche oder bessere Quelle bereits vorhanden)")
        return False
    if self.filename == 'MB_Staffeln':
        if not self.config.get("seasonpacks"):
            staffelpack = re.search(r"s\d.*(-|\.).*s\d", title.lower())
            if staffelpack:
                self.log_debug(
                    "%s - Release ignoriert (Staffelpaket)" % title)
                return False
        if not re.search(self.seasonssource, title.lower()):
            self.log_debug(title + " - Release hat falsche Quelle")
            return False
    try:
        if language_id == 2:
            lang = 'EN'
        else:
            lang = 'DE'
        epoch = str(datetime.datetime.now().timestamp()).replace('.', '')[:-3]
        api_url = series_url + '?lang=' + lang + '&_=' + epoch
        response = get_url(api_url, self.configfile, self.dbfile, self.scraper)
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

        content = BeautifulSoup(info['html'], 'lxml')
        releases = content.find("small", text=re.compile(season_title, re.IGNORECASE)).parent.parent.parent
        links = releases.findAll("div", {'class': 'row'})[1].findAll('a')
        download_link = False
        for link in links:
            if check_hoster(link.text.replace('\n', ''), self.configfile):
                download_link = get_redirected_url("https://" + self.url + link['href'], self.configfile,
                                                   self.dbfile, self.scraper)
                break
        if not download_link and not self.hoster_fallback:
            storage = self.db.retrieve_all(title)
            if 'added' not in storage and 'notdl' not in storage:
                wrong_hoster = '[SF/Hoster fehlt] - ' + title
                if 'wrong_hoster' not in storage:
                    print(wrong_hoster)
                    self.db.store(title, 'wrong_hoster')
                    notify([wrong_hoster], self.configfile)
                else:
                    self.log_debug(wrong_hoster)
                return False
        else:
            return [title, download_link, language_id, season, episode]
    except:
        print(u"SF hat die Serien-API angepasst. Breche Download-Prüfung ab!")
        return False
