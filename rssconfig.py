# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import ConfigParser
import logging
import os
import sys


class RssConfig(object):
    _CONFIG_FILES = [os.path.join(os.path.dirname(
        sys.argv[0]), 'Einstellungen/RSScrawler.ini')]
    _DEFAULT_CONFIG = {
        'RSScrawler': [
            ("jdownloader", "str", ""),
            ("port", "int", "9090"),
            ("prefix", "str", ""),
            ("interval", "int", "10"),
            ("english", "bool", "False"),
            ("surround", "bool", ""),
            ("proxy", "str", ""),
            ("fallback", "bool", "False")
        ],
        'MB': [
            ("hoster", "str", "Share-Online"),
            ("quality", "str", "720p"),
            ("ignore", "str", "cam,subbed,xvid,dvdr,untouched,remux,avc,pal,md,ac3md,mic,xxx"),
            ("historical", "bool", "False"),
            ("regex", "bool", "False"),
            ("cutoff", "bool", "False"),
            ("crawl3d", "bool", "False"),
            ("crawl3dtype", "str", "hsbs"),
            ("enforcedl", "bool", "False"),
            ("crawlseasons", "bool", "True"),
            ("seasonsquality", "str", "720p"),
            ("seasonpacks", "bool", "False"),
            ("seasonssource", "str", "web-dl.*-(tvs|4sj)|webrip.*-(tvs|4sj)|webhd.*-(tvs|4sj)|netflix.*-(tvs|4sj)|amazon.*-(tvs|4sj)|itunes.*-(tvs|4sj)|bluray|bd|bdrip"),
            ("imdbyear", "str", "2010"),
            ("imdb", "str", "0.0")
        ],
        'SJ': [
            ("hoster", "str", "Share-Online"),
            ("quality", "str", "720p"),
            ("rejectlist", "str", "XviD,Subbed,HDTV"),
            ("regex", "bool", "False")
        ],
        'DD': [
            ("hoster", "str", ""),
            ("feeds", "str", "")
        ],
        'YT': [
            ("youtube", "bool", "False"),
            ("maxvideos", "int", "10"),
            ("ignore", "str", "")
        ],
        'Notifications': [
            ("homeassistant", "str", ""),
            ("pushbullet", "str", ""),
            ("pushover", "str", "")
        ],
        'Crawljobs': [
            ("autostart", "bool", "True"),
            ("subdir", "bool", "True")
        ]
    }
    __config__ = []

    def __init__(self, section, jdownloader=None, port=None):
        self._section = section
        self._config = ConfigParser.RawConfigParser()
        try:
            self._config.read(self._CONFIG_FILES)
            self._config.has_section(
                self._section) or self._set_default_config(self._section)
            if jdownloader and port:
                self._set_parameters(jdownloader, port)
            self.__config__ = self._read_config(self._section)
        except ConfigParser.DuplicateSectionError:
            logging.error('Doppelte Sektion in der Konfigurationsdatei.')
            raise
        except ConfigParser.Error:
            logging.error(
                'Ein unbekannter Fehler in der Konfigurationsdatei ist aufgetreten.')
            raise

    def _set_default_config(self, section):
        self._config.add_section(section)
        for (key, key_type, value) in self._DEFAULT_CONFIG[section]:
            self._config.set(section, key, value)
        with open(self._CONFIG_FILES[::-1].pop(), 'wb') as configfile:
            self._config.write(configfile)

    def _set_parameters(self, jdownloader, port):
        self._config.set("RSScrawler", "jdownloader", jdownloader)
        self._config.set("RSScrawler", "port", port)
        with open(self._CONFIG_FILES[::-1].pop(), 'wb') as configfile:
            self._config.write(configfile)

    def _read_config(self, section):
        return [(key, '', '', self._config.get(section, key)) for key in self._config.options(section)]

    def _get_from_config(self, scope, key):
        res = [param[2] for param in scope if param[0] == key]
        if [param for param in self._DEFAULT_CONFIG[self._section] if param[0] == key and param[1] == 'bool']:
            return True if len(res) and res[0].strip('\'"').lower() == 'true' else False
        else:
            return res[0].strip('\'"') if len(res) > 0 else False

    def get(self, key):
        return self._get_from_config(self.__config__, key) or self._get_from_config(self._DEFAULT_CONFIG[self._section], key)
