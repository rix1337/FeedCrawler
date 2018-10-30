# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

from six.moves import configparser


class RssConfig(object):
    _DEFAULT_CONFIG = {
        'RSScrawler': [
            ("myjd_user", "str", ""),
            ("myjd_pass", "str", ""),
            ("myjd_device", "str", ""),
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
            ("hoster", "str", ".*?share-online.*?"),
            ("quality", "str", "720p"),
            ("search", "int", "10"),
            ("ignore", "str", "cam,subbed,xvid,dvdr,untouched,remux,avc,pal,md,ac3md,mic,xxx"),
            ("regex", "bool", "False"),
            ("cutoff", "bool", "False"),
            ("crawl3d", "bool", "False"),
            ("crawl3dtype", "str", "hsbs"),
            ("enforcedl", "bool", "False"),
            ("crawlseasons", "bool", "True"),
            ("seasonsquality", "str", "720p"),
            ("seasonpacks", "bool", "False"),
            ("seasonssource", "str",
             "web-dl.*-(tvs|4sj)|webrip.*-(tvs|4sj)|webhd.*-(tvs|4sj)|netflix.*-(tvs|4sj)|amazon.*-(tvs|4sj)|itunes.*-(tvs|4sj)|bluray|bd|bdrip"),
            ("imdbyear", "str", "2010"),
            ("imdb", "str", "0.0")
        ],
        'SJ': [
            ("hoster", "str", ".*?share-online.*?"),
            ("quality", "str", "720p"),
            ("rejectlist", "str", "XviD,Subbed,HDTV"),
            ("regex", "bool", "False")
        ],
        'DD': [
            ("hoster", "str", ".*"),
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
        'Ombi': [
            ("url", "str", ""),
            ("api", "str", ""),
            ("mdb_api", "str", ""),
            ("tvd_api", "str", ""),
            ("tvd_user", "str", ""),
            ("tvd_userkey", "str", "")
        ],
        'Crawljobs': [
            ("autostart", "bool", "True"),
            ("subdir", "bool", "True")
        ]
    }
    __config__ = []

    def __init__(self, section, configfile):
        self._configfile = configfile
        self._section = section
        self._config = configparser.RawConfigParser()
        try:
            self._config.read(self._configfile)
            self._config.has_section(
                self._section) or self._set_default_config(self._section)
            self.__config__ = self._read_config(self._section)
        except configparser.DuplicateSectionError:
            print(u'Doppelte Sektion in der Konfigurationsdatei.')
            raise
        except:
            print(u'Ein unbekannter Fehler in der Konfigurationsdatei ist aufgetreten.')
            raise

    def _set_default_config(self, section):
        self._config.add_section(section)
        for (key, key_type, value) in self._DEFAULT_CONFIG[section]:
            self._config.set(section, key, value)
        with open(self._configfile, 'w') as configfile:
            self._config.write(configfile)

    def _set_to_config(self, section, key, value):
        self._config.set(section, key, value)
        with open(self._configfile, 'w') as configfile:
            self._config.write(configfile)

    def _read_config(self, section):
        return [(key, '', self._config.get(section, key)) for key in self._config.options(section)]

    def _get_from_config(self, scope, key):
        res = [param[2] for param in scope if param[0] == key]
        if not res:
            res = [param[2]
                   for param in self._DEFAULT_CONFIG[self._section] if param[0] == key]
        if [param for param in self._DEFAULT_CONFIG[self._section] if param[0] == key and param[1] == 'bool']:
            return True if len(res) and res[0].strip('\'"').lower() == 'true' else False
        else:
            return res[0].strip('\'"') if len(res) > 0 else False

    def save(self, key, value):
        self._set_to_config(self._section, key, value)
        return

    def get(self, key):
        return self._get_from_config(self.__config__, key)
