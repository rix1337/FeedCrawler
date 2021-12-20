# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337

import configparser

from feedcrawler import internal


class CrawlerConfig(object):
    _DEFAULT_CONFIG = {
        'FeedCrawler': [
            ("auth_user", "str", ""),
            ("auth_hash", "str", ""),
            ("myjd_user", "str", ""),
            ("myjd_pass", "str", ""),
            ("myjd_device", "str", ""),
            ("port", "int", "9090"),
            ("prefix", "str", ""),
            ("interval", "int", "10"),
            ("flaresolverr", "str", ""),
            ("flaresolverr_proxy", "str", ""),
            ("english", "bool", "False"),
            ("surround", "bool", ""),
            ("closed_myjd_tab", "bool", "False"),
            ("one_mirror_policy", "bool", "False"),
            ("packages_per_myjd_page", "int", "3")
        ],
        'Hostnames': [
            ("sj", "str", ""),
            ("dj", "str", ""),
            ("sf", "str", ""),
            ("by", "str", ""),
            ("fx", "str", ""),
            ("nk", "str", ""),
            ("ww", "str", "")
        ],
        'Crawljobs': [
            ("autostart", "bool", "True"),
            ("subdir", "bool", "True")
        ],
        'Notifications': [
            ("homeassistant", "str", ""),
            ("pushbullet", "str", ""),
            ("telegram", "str", ""),
            ("pushover", "str", "")
        ],
        'Hosters': [
            ("rapidgator", "bool", "True"),
            ("turbobit", "bool", "False"),
            ("uploaded", "bool", "False"),
            ("zippyshare", "bool", "False"),
            ("oboom", "bool", "False"),
            ("ddl", "bool", "False"),
            ("filefactory", "bool", "False"),
            ("uptobox", "bool", "False"),
            ("1fichier", "bool", "False"),
            ("filer", "bool", "False"),
            ("nitroflare", "bool", "False"),
            ("ironfiles", "bool", "False"),
            ("k2s", "bool", "False")
        ],
        'Ombi': [
            ("url", "str", ""),
            ("api", "str", "")
        ],
        'ContentAll': [
            ("quality", "str", "1080p"),
            ("search", "int", "10"),
            ("ignore", "str", "cam,subbed,xvid,dvdr,untouched,remux,mpeg2,avc,pal,md,ac3md,mic,xxx"),
            ("regex", "bool", "False"),
            ("cutoff", "bool", "True"),
            ("enforcedl", "bool", "False"),
            ("crawlseasons", "bool", "True"),
            ("seasonsquality", "str", "1080p"),
            ("seasonpacks", "bool", "False"),
            ("seasonssource", "str",
             "web-dl.*-(tvs|4sj|tvr)|webrip.*-(tvs|4sj|tvr)|webhd.*-(tvs|4sj|tvr)|netflix.*-(tvs|4sj|tvr)|amazon.*-(tvs|4sj|tvr)|itunes.*-(tvs|4sj|tvr)|bluray|bd|bdrip"),
            ("imdbyear", "str", "2010"),
            ("imdb", "str", "0.0"),
            ("hevc_retail", "bool", "False"),
            ("retail_only", "bool", "False"),
            ("hoster_fallback", "bool", "False")
        ],
        'ContentShows': [
            ("quality", "str", "1080p"),
            ("rejectlist", "str", "XviD,Subbed,HDTV"),
            ("regex", "bool", "False"),
            ("hevc_retail", "bool", "False"),
            ("retail_only", "bool", "False"),
            ("hoster_fallback", "bool", "False")
        ],
        'CustomDJ': [
            ("quality", "str", "1080p"),
            ("rejectlist", "str", "XviD,Subbed"),
            ("regex", "bool", "False"),
            ("hoster_fallback", "bool", "False")
        ]
    }
    __config__ = []

    def __init__(self, section):
        self._configfile = internal.configfile
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

    def get_section(self):
        return self._config._sections[self._section]
