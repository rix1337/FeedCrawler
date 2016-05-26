# -*- coding: utf-8 -*-
import ConfigParser
import logging
import os


class RssConfig(object):
    _CONFIG_FILES = [os.path.join(os.path.dirname(__file__), 'Einstellungen/RSScrawler.ini')]
    _DEFAULT_CONFIG = {
        'RSScrawler': [
            ("jdownloader", "str", "Dieser Pfad muss das exakte Verzeichnis des JDownloaders sein, sonst funktioniert das Script nicht!", "/jd2"),
            ("interval", "int", "Execution interval of the script in minutes", "10"),
            ("pushbulletapi","str","Add your Pushbullet-API key if you want to be notified",""),
            ("hoster", """Uploaded,Share-Online""", "Hier den gewünschten Hoster eintragen (Uploaded oder Share-Online)", "Uploaded")
        ],
        'MB': [
            ("quality", """480p;720p;1080p""", "Quality to look for in Release titles - 480p, 720p or 1080p", "720p"),
            ("ignore","str","Ignore pattern - Comma seperated list of Release tags to ignore","ts,cam,subbed,xvid,dvdr,untouched,remux,pal,md,ac3md,mic,xxx,hou"),
            ("historical","bool","Use search function - Disable if you only want current Releases to be added","True"),
            ("crawl3d","bool","Crawl for 3D versions of Movies - in 1080p, regardles of quality set above","False"),
            ("enforcedl", "bool", "If release without DL tag is added, look for DL release - ignoring quality setting", "False"),
            ("crawlseasons", "bool", "Crawl complete Seasons on MB", "False"),
            ("seasonsquality", "str", "Quality of complete seasons to crawl for - 480p, 720p or 1080p", "720p"),
            ("seasonssource", "str", "Source tag to look for in complete seasons - e.g. bluray, web-dl or hdtv", "bluray")
        ],
        'SJ': [
            ("quality", """480p;720p;1080p""", "Quality to look for in Release titles - 480p, 720p or 1080p", "720p"),
            ("rejectlist", "str", "Reject list - Semicolon seperated list of Release tags to ignore", "XviD;Subbed;HDTV"),
            ("regex","bool","Treat entries of the List as regular expressions - for advanced use cases", "True")
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
            logging.error('Config file has duplicate section.')
            raise
        except ConfigParser.Error:
            logging.error('An unknown error occurred while reading the configuration file.')
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
