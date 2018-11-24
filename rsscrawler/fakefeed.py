# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337


class FakeFeedParserDict(dict):
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: " + name)


def ha_to_feedparser_obj(content):
    items_head = content.find_all("div", {"class": "topbox"})
    items_download = content.find_all("div", {"class": "download"})

    entries = []

    i = 0
    for item in items_head:
        contents = item.contents
        title = contents[1].a["title"]
        published = contents[1].text.replace(title, "").replace("\n", "").replace("...", "")
        content = []
        imdb = contents[3]
        content.append(str(imdb).replace("\n", ""))
        download = items_download[i].find_all("span", {"style": "display:inline;"}, text=True)
        for link in download:
            link = link.a
            text = link.text.strip()
            if text:
                content.append(str(link))
        content = "".join(content)

        entries.append({
            "title": title,
            "published": published,
            "content": [{
                "value": content}]
        })

        i += 1

    feed = {"entries": entries}
    feed = FakeFeedParserDict(feed)
    return feed
