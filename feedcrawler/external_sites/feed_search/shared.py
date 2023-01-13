# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt Hilfsfunktionen für die Feed-Suche bereit.

import re

from feedcrawler.providers.common_functions import check_hoster
from feedcrawler.providers.common_functions import readable_size
from feedcrawler.providers.myjd_connection import add_decrypt
from feedcrawler.providers.url_functions import get_redirected_url


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


def check_release_not_sd(title):
    if "720p" in title.lower() or "1080p" in title.lower() or "1080i" in title.lower() \
            or "2160p" in title.lower() or "complete.bluray" in title.lower() or "complete.mbluray" in title.lower() \
            or "complete.uhd.bluray" in title.lower():
        return True
    else:
        return False


def standardize_size_value(size):
    size_value = round(float(re.sub('[^0-9,.]', '', size)), 2)
    if str(size_value).endswith('.0'):
        size_value = int(size_value)
    size_unit = re.sub('[0-9,.]', '', size).strip().upper()

    if size_unit == 'B':
        readable_size(size_value)
    elif size_unit == 'KB':
        readable_size(size_value * 1024)
    elif size_unit == 'MB':
        size = readable_size(size_value * 1024 * 1024)
    elif size_unit == 'GB':
        size = readable_size(size_value * 1024 * 1024 * 1024)
    elif size_unit == 'TB':
        size = readable_size(size_value * 1024 * 1024 * 1024 * 1024)
    else:
        size = str(size_value) + " " + str(size_unit)

    return size


def add_decrypt_instead_of_download(key, path, download_links, password, replace=False):
    unused_get_feed_parameter(path)

    if add_decrypt(key.strip(), download_links[0], password, replace):
        return True
    else:
        return False
