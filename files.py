# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

from rssconfig import RssConfig


def startup(jdownloader=None, port=None):
    if jdownloader or port:
        sections = ['RSScrawler', 'MB', 'SJ', 'DD',
                    'YT', 'Notifications', 'Crawljobs']
        for section in sections:
            RssConfig(section)
        if jdownloader:
            RssConfig('RSScrawler').save("jdownloader", jdownloader)
        if port:
            RssConfig('RSScrawler').save("port", port)
