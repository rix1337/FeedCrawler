# -*- coding: utf-8 -*-
import ConfigParser
import logging
import os


class RssConfig(object):
    _CONFIG_FILES = [os.path.join(os.path.dirname(__file__), 'Settings/Settings.conf')]
    _DEFAULT_CONFIG = {
        'MB': [
            ("interval", "int", "Execution interval in minutes", "10"),
            ("patternfile", "str", "List of Movies (use SJ for shows)", os.path.join(os.path.dirname(__file__), "Settings/Lists/Movies.txt")),
            ("destination", "queue;collector", "Deprecated Option", "collector"),
            ("ignore","str","Ignore pattern (comma seperated)","ts,cam,subbed,xvid,dvdr,untouched,pal,md,ac3md,mic,3d"),
            ("historical","bool","Use the search function in order to match older entries","False"),
            ("pushbulletapi","str","Your Pushbullet-API key",""),
            ("quiethours","str","Quiet hours (comma seperated)",""),
            ("crawljob_directory","str","JDownloaders folderwatch directory","/jd2/folderwatch"),
            ("db_file","str","db_file",os.path.join(os.path.dirname(__file__), "Settings/Database/Downloads.db"))
        ],
        'SJ': {
            ("regex","bool","Treat entries of the List as regular expressions", "False"),
            ("quality", """480p;720p;1080p""", "480p, 720p or 1080p", "720p"),
            ("file", "str", "List of shows", os.path.join(os.path.dirname(__file__), "Settings/Lists/Shows.txt")),
            ("rejectlist", "str", "Ignore pattern (semicolon-separated)", "XviD;Subbed;NCIS.New.Orleans;NCIS.Los.Angeles;LEGO"),
            ("language", """DEUTSCH;ENGLISCH""", "Language", "DEUTSCH"),
            ("interval", "int", "Execution interval in minutes", "10"),
            ("hoster", """ul;so;fm;cz;alle""", "Hoster to load from", "ul"),
            ("pushbulletapi","str","Your Pushbullet-API key",""),
            ("crawljob_directory","str","JDownloaders folderwatch directory","/jd2/folderwatch"),
            ("db_file","str","db_file",os.path.join(os.path.dirname(__file__), "Settings/Database/Downloads.db"))
        }
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
        return res[0] if len(res) > 0 else False

    def get(self, key):
        return (
            self._get_from_config(self.__config__, key)
            or
            self._get_from_config(self._DEFAULT_CONFIG[self._section], key)
        ).strip('\'"')
