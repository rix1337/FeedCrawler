# -*- coding: utf-8 -*-
import ConfigParser
import logging
import os


class RssConfig(object):
    _CONFIG_FILES = [os.path.join(os.path.dirname(__file__), 'Einstellungen/RSScrawler.ini')]
    _DEFAULT_CONFIG = {
        'RSScrawler': [
            ("jdownloader", "str", "", "/jd2"),
            ("interval", "int", "", "10"),
            ("pushbulletapi","str","",""),
            ("hoster", """Uploaded,Share-Online""", "", "Uploaded")
        ],
        'MB': [
            ("quality", """480p;720p;1080p""", "", "720p"),
            ("ignore","str","","ts,cam,subbed,xvid,dvdr,untouched,remux,pal,md,ac3md,mic,xxx,hou"),
            ("historical","bool","","True"),
            ("crawl3d","bool","","False"),
            ("enforcedl", "bool", "", "False"),
            ("crawlseasons", "bool", "", "False"),
            ("seasonsquality", "str", "", "720p"),
            ("seasonssource", "str", "", "bluray")
        ],
        'SJ': [
            ("quality", """480p;720p;1080p""", "", "720p"),
            ("rejectlist", "str", "", "XviD;Subbed;HDTV"),
            ("regex","bool","", "True")
        ]
    }
    __config__ = []

    def __init__(self, section):
        self._section = section
        self._config =  ConfigParser.RawConfigParser()
        try:
            self._config.read(self._CONFIG_FILES)
            self._config.has_section(self._section) or self._set_default_config(self._section)
            self.__config__ = self._read_config(self._section)
        except ConfigParser.DuplicateSectionError:
            logging.error('Doppelte Sektion in der Konfigurationsdatei.')
            raise
        except ConfigParser.Error:
            logging.error('Ein unbekannter Fehler in der Konfigurationsdatei ist aufgetreten.')
            raise

    def _set_default_config(self, section):
        self._config.add_section(section)
        for (key,key_type,comment,value) in self._DEFAULT_CONFIG[section]:
            self._config.set(section,key,value)
        with open(self._CONFIG_FILES.pop(), 'wb') as configfile:
            self._config.write(configfile)

    def _read_config(self, section):
        return [(key, '', '', self._config.get(section,key)) for key in self._config.options(section)]

    def _get_from_config(self, scope, key):
        res = [param[3] for param in scope if param[0] == key]
        if [param for param in self._DEFAULT_CONFIG[self._section] if param[0] == key and param[1] == 'bool']:
            return True if len(res) and res[0].strip('\'"').lower() == 'true' else False
        else:
            return res[0].strip('\'"') if len(res) > 0 else False

    def get(self, key):
        return self._get_from_config(self.__config__, key) or self._get_from_config(self._DEFAULT_CONFIG[self._section], key)
