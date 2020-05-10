# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337


import re

import feedparser
from bs4 import BeautifulSoup

from rsscrawler.rsscommon import decode_base64
from rsscrawler.url import get_url
from rsscrawler.url import get_urls_async


class FakeFeedParserDict(dict):
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: " + name)


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


def sj_to_feedparser_dict(beautifulsoup_object, type):
    content_areas = beautifulsoup_object.findAll("h3", text=type)
    entries = []

    for area in content_areas:
        lists = area.previous.findAll("div")
        for list in lists:
            try:
                published = str(list.previous)
            except:
                published = "ERROR"

            items = list.findAll("a")
            for item in items:
                title = item.text
                link = decode_base64('aHR0cHM6Ly9zZXJpZW5qdW5raWVzLm9yZw==') + item.attrs["href"]

                entries.append(FakeFeedParserDict({
                    "title": title,
                    "link": link,
                    "published": published
                }))

    feed = {"entries": entries}
    feed = FakeFeedParserDict(feed)
    return feed


def sj_content_to_soup(content, type):
    content = BeautifulSoup(content, 'lxml')
    content = sj_to_feedparser_dict(content, type)
    return content


def dj_to_feedparser_dict(beautifulsoup_object):
    content_areas = beautifulsoup_object.findAll("fieldset")
    entries = []

    for area in content_areas:
        try:
            published = re.findall(r"Updates.{3}(.*Uhr)", area.text)[0]
        except:
            published = "ERROR"

        genres = area.find_all("div", {"class": "grey-box"})

        for genre in genres:
            items = genre.select("a")
            dj_type = str(genre.previous.previous)

            for item in items:
                titles = item.text.split('\n')
                link = item.attrs["href"]

                for title in titles:
                    entries.append(FakeFeedParserDict({
                        "title": title,
                        "published": published,
                        "genre": dj_type,
                        "link": link
                    }))

    feed = {"entries": entries}
    feed = FakeFeedParserDict(feed)
    return feed


def dj_content_to_soup(content):
    content = BeautifulSoup(content, 'lxml')
    content = dj_to_feedparser_dict(content)
    return content


def fx_content_to_soup(content):
    content = BeautifulSoup(content, 'lxml')
    return content


def fx_search_results(content):
    content = content.find_all("item")
    items = []
    for item in content:
        title = fx_post_title(item)
        link = item.find("comments").text
        items.append([title, link])
    return items


def fx_post_title(content):
    # TODO: this only gets the first release if there are multiple options
    if not content:
        return ""
    try:
        content = BeautifulSoup(content, 'lxml')
    except:
        content = BeautifulSoup(str(content), 'lxml')
    try:
        title = content.find("mark").text.encode("ascii", errors="ignore").decode()
    except:
        try:
            title = content.find("title").text
        except:
            title = ""
    return title


def fx_download_links(content, title):
    try:
        try:
            content = BeautifulSoup(content, 'lxml')
        except:
            content = BeautifulSoup(str(content), 'lxml')
        try:
            download_links = [content.find("a", text=re.compile(r".*" + title + r".*"))['href']]
        except:
            download_links = re.findall(r'"(https://.+?filecrypt.+?)"', str(content))
    except:
        return False
    return download_links


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
