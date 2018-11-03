# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import re

from six.moves.urllib.error import HTTPError

from rsscrawler.myjd import myjd_download
from rsscrawler.notifiers import notify
from rsscrawler.rssconfig import RssConfig
from rsscrawler.rssdb import ListDb
from rsscrawler.rssdb import RssDb
from rsscrawler.url import get_url


class YT:
    _INTERNAL_NAME = 'YT'

    def __init__(self, configfile, dbfile, device, logging):
        self.configfile = configfile
        self.dbfile = dbfile
        self.device = device
        self.config = RssConfig(self._INTERNAL_NAME, self.configfile)
        self.log_info = logging.info
        self.log_error = logging.error
        self.log_debug = logging.debug
        self.db = RssDb(self.dbfile, 'rsscrawler')
        self.youtube = 'YT_Channels'
        self.dictWithNamesAndLinks = {}

    def read_input(self, liste):
        cont = ListDb(self.dbfile, liste).retrieve()
        return cont if cont else ""

    def periodical_task(self):
        if not self.config.get('youtube'):
            self.log_debug("Suche für YouTube deaktiviert!")
            return self.device
        added_items = []
        channels = []
        videos = []
        self.allInfos = self.read_input(self.youtube)

        for item in self.allInfos:
            if len(item) > 0:
                if self.config.get("youtube") is False:
                    self.log_debug(
                        "Liste ist leer. Stoppe Suche für YouTube!")
                    return self.device
                channels.append(item)

        for channel in channels:
            if 'list=' in channel:
                id_cutter = channel.rfind('list=') + 5
                channel = channel[id_cutter:]
                url = 'https://www.youtube.com/playlist?list=' + channel
                response = get_url(url, self.configfile, self.dbfile)
            else:
                url = 'https://www.youtube.com/user/' + channel + '/videos'
                urlc = 'https://www.youtube.com/channel/' + channel + '/videos'
                cnotfound = False
                try:
                    response = get_url(url, self.configfile, self.dbfile)
                except HTTPError:
                    try:
                        response = get_url(urlc, self.configfile, self.dbfile)
                    except HTTPError:
                        cnotfound = True
                    if cnotfound:
                        self.log_debug("YouTube-Kanal: " +
                                       channel + " nicht gefunden!")
                        break

            links = re.findall(
                r'VideoRenderer":{"videoId":"(.*?)",".*?[Tt]ext":"(.*?)"}', response)

            maxvideos = int(self.config.get("maxvideos"))
            if maxvideos < 1:
                self.log_debug("Anzahl zu suchender YouTube-Videos (" +
                               str(maxvideos) + ") zu gering. Suche stattdessen 1 Video!")
                maxvideos = 1
            elif maxvideos > 50:
                self.log_debug("Anzahl zu suchender YouTube-Videos (" +
                               str(maxvideos) + ") zu hoch. Suche stattdessen maximal 50 Videos!")
                maxvideos = 50

            for link in links[:maxvideos]:
                if len(link[0]) > 10:
                    videos.append(
                        [link[0], link[1], channel])

        for video in videos:
            channel = video[2]
            title = video[1]
            if "[private" in title.lower() and "video]" in title.lower():
                self.log_debug(
                    "[%s] - YouTube-Video ignoriert (Privates Video)" % video)
                continue
            video_title = title.replace("&amp;", "&").replace("&gt;", ">").replace(
                "&lt;", "<").replace('&quot;', '"').replace("&#39;", "'").replace("\u0026", "&")
            video = video[0]
            download_link = 'https://www.youtube.com/watch?v=' + video
            if download_link:
                if self.db.retrieve(video) == 'added':
                    self.log_debug(
                        "[%s] - YouTube-Video ignoriert (bereits gefunden)" % video)
                else:
                    ignore = "|".join(["%s" % p for p in self.config.get("ignore").lower().split(
                        ',')]) if self.config.get("ignore") else r"^unmatchable$"
                    ignorevideo = re.search(ignore, video_title.lower())
                    if ignorevideo:
                        self.log_debug(video_title + " (" + channel + ") " +
                                       "[" + video + "] - YouTube-Video ignoriert (basierend auf ignore-Einstellung)")
                        continue
                    self.device = myjd_download(self.configfile, self.device, "YouTube/" + channel, "RSScrawler",
                                                download_link, "")
                    if self.device:
                        self.db.store(
                            video,
                            'added'
                        )
                        log_entry = '[YouTube] - ' + video_title + ' (' + channel + ')'
                        self.log_info(log_entry)
                        notify([log_entry], self.configfile)
                        added_items.append(log_entry)
        return self.device
