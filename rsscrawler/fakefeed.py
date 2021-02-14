# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import json
import re

import feedparser
from bs4 import BeautifulSoup

from rsscrawler.common import rreplace
from rsscrawler.config import RssConfig
from rsscrawler.url import get_url
from rsscrawler.url import get_urls_async


class FakeFeedParserDict(dict):
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: " + name)


def fx_content_to_soup(content):
    content = BeautifulSoup(content, 'lxml')
    return content


def fx_get_download_links(content, title, configfile):
    hostnames = RssConfig('Hostnames', configfile)
    fc = hostnames.get('fc').replace('www.', '').split('.')[0]
    try:
        try:
            content = BeautifulSoup(content, 'lxml')
        except:
            content = BeautifulSoup(str(content), 'lxml')
        try:
            download_links = [content.find("a", text=re.compile(r".*" + title + r".*"))['href']]
        except:
            if not fc:
                fc = '^unmatchable$'
                print(u"FC Hostname nicht gesetzt. FX kann keine Links finden!")
            download_links = re.findall(r'"(https://.+?' + fc + '.+?)"', str(content))
    except:
        return False
    return download_links


def fx_feed_enricher(feed, configfile):
    hostnames = RssConfig('Hostnames', configfile)
    fc = hostnames.get('fc').replace('www.', '').split('.')[0]
    if not fc:
        fc = '^unmatchable$'
        print(u"FC Hostname nicht gesetzt. FX kann keine Links finden!")

    feed = BeautifulSoup(feed, 'lxml')
    articles = feed.findAll("article")
    entries = []

    for article in articles:
        try:
            article = BeautifulSoup(str(article), 'lxml')
            titles = article.findAll("a", href=re.compile(fc))
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
    hostnames = RssConfig('Hostnames', configfile)
    fc = hostnames.get('fc').replace('www.', '').split('.')[0]
    if not fc:
        fc = '^unmatchable$'
        print(u"FC Hostname nicht gesetzt. FX kann keine Links finden!")

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
            titles = article.find_all("a", href=re.compile(fc))
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


def hs_feed_enricher(feed, configfile, dbfile, scraper):
    feed = feedparser.parse(feed)

    async_results = []
    for post in feed.entries:
        try:
            async_results.append(post.links[0].href)
        except:
            pass
    async_results = get_urls_async(async_results, configfile, dbfile, scraper)[0]

    entries = []
    if async_results:
        for result in async_results:
            try:
                content = []
                details = result
                title = BeautifulSoup(details, 'lxml').find("h2", {"class": "entry-title"}).text
                published = BeautifulSoup(details, 'lxml').find("p", {"class": "blog-post-meta"}).contents[0]
                data = BeautifulSoup(details, 'lxml').find("div", {"class": "entry-content"}).contents[2]
                content.append(str(data).replace("\n", ""))
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


def hs_search_results(url):
    content = []
    search = BeautifulSoup(url, 'lxml')
    if search:
        results = search.find_all("item")
        if results:
            for r in results:
                try:
                    title = r.title.next
                    link = r.find("comments").text
                    content.append((title, link))
                except:
                    break
    return content


def hs_search_to_feedparser_dict(beautifulsoup_object_list):
    entries = []
    for beautifulsoup_object in beautifulsoup_object_list:
        title = beautifulsoup_object["key"]
        # TODO: this is entirely broken
        item_head = beautifulsoup_object["value"].find_all("p", {"class": "blog-post-meta"})
        item_download = beautifulsoup_object["value"].find_all("div", {"class": "entry-content"})

        i = 0
        for item in item_head:
            contents = item_download[i].contents
            published = item.contents[0]
            content = []
            data = contents[2]
            content.append(str(data).replace("\n", ""))
            content = "".join(content)

            entries.append(FakeFeedParserDict({
                "title": title,
                "published": published,
                "content": [FakeFeedParserDict({
                    "value": content})]
            }))

            i += 1

    feed = {"entries": entries}
    feed = FakeFeedParserDict(feed)
    return feed


def hs_search_to_soup(url, configfile, dbfile, scraper):
    content = []
    search = BeautifulSoup(get_url(url, configfile, dbfile, scraper), 'lxml')
    if search:
        results = search.find_all("item")
        if results:
            async_results = []
            for r in results:
                try:
                    async_results.append(r.link.next)
                except:
                    pass
            async_results = get_urls_async(async_results, configfile, dbfile, scraper)[0]
            # TODO: This is a bug, if async results is ordered differently than results
            i = 0
            for r in results:
                try:
                    title = r.title.next
                    details = BeautifulSoup(async_results[i], 'lxml')
                    content.append({
                        "key": title,
                        "value": details
                    })
                except:
                    pass
                i += 1
    return hs_search_to_feedparser_dict(content)


def nk_feed_enricher(content, base_url, configfile, dbfile, scraper):
    content = BeautifulSoup(content, 'lxml')
    posts = content.findAll("a", {"class": "btn"}, href=re.compile("/release/"))
    async_results = []
    for post in posts:
        try:
            async_results.append(base_url + post['href'])
        except:
            pass
    async_results = get_urls_async(async_results, configfile, dbfile, scraper)[0]

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
                    content.append('href="' + base_url + link["href"] + '"' + link.text + '<')
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
