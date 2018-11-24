# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337


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
