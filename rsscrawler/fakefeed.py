# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337


from bs4 import BeautifulSoup

from rsscrawler.url import get_url


class FakeFeedParserDict(dict):
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: " + name)


def ha_to_feedparser_dict(beautifulsoup_object):
    items_head = beautifulsoup_object.find_all("div", {"class": "topbox"})
    items_download = beautifulsoup_object.find_all("div", {"class": "download"})

    entries = []

    i = 0
    for item in items_head:
        contents = item.contents
        title = contents[1].a["title"]
        published = contents[1].text.replace(title, "").replace("\n", "").replace("...", "")
        content = []
        imdb = contents[3]
        content.append(str(imdb).replace("http://dontknow.me/at/?", "").replace("\n", ""))
        download = items_download[i].find_all("span", {"style": "display:inline;"}, text=True)
        for link in download:
            link = link.a
            text = link.text.strip()
            if text:
                content.append(str(link))
        content.append("<span>mkv</span>")
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


def ha_search_to_feedparser_dict(beautifulsoup_object_list):
    entries = []
    for beautifulsoup_object in beautifulsoup_object_list:
        title = beautifulsoup_object["key"]
        item_head = beautifulsoup_object["value"].find_all("div", {"class": "topbox"})
        item_download = beautifulsoup_object["value"].find_all("div", {"class": "download"})

        i = 0
        for item in item_head:
            contents = item.contents
            published = contents[1].text.replace(title, "").replace("\n", "").replace("...", "")
            content = []
            imdb = contents[3]
            content.append(str(imdb).replace("http://dontknow.me/at/?", "").replace("\n", ""))
            download = item_download[i].find_all("span", {"style": "display:inline;"}, text=True)
            for link in download:
                link = link.a
                text = link.text.strip()
                if text:
                    content.append(str(link))
            content.append("<span>mkv</span>")
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


def ha_url_to_soup(url, configfile, dbfile):
    content = BeautifulSoup(get_url(url, configfile, dbfile), 'lxml')
    return ha_to_feedparser_dict(content)


def ha_search_to_soup(url, configfile, dbfile):
    content = []
    search = BeautifulSoup(get_url(url, configfile, dbfile), 'lxml')
    results = search.find("div", {"id": "content"}).find_all("a")
    pagination = False
    for r in results:
        try:
            title = r["title"]
            details = BeautifulSoup(get_url(r["href"], configfile, dbfile), 'lxml')
            content.append({
                "key": title,
                "value": details
            })
        except:
            pagination = r["href"]
    if pagination:
        i = 3
        while i > 0:
            search = BeautifulSoup(get_url(pagination, configfile, dbfile), 'lxml')
            results = search.find("div", {"id": "content"}).find_all("a")
            more_pages = False
            for r in results:
                try:
                    title = r["title"]
                    details = BeautifulSoup(get_url(r["href"], configfile, dbfile), 'lxml')
                    content.append({
                        "key": title,
                        "value": details
                    })
                except:
                    more_pages = r["href"]
            if not more_pages:
                break
            i -= 1

    return ha_search_to_feedparser_dict(content)


def ha_search_results(url, configfile, dbfile):
    content = []
    search = BeautifulSoup(get_url(url, configfile, dbfile), 'lxml')
    results = search.find("div", {"id": "content"}).find_all("a")
    for r in results:
        try:
            content.append((r["title"], r["href"]))
        except:
            break
    return content
