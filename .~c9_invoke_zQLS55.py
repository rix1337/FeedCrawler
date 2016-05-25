# -*- coding: utf-8 -*-
import ConfigParser
import logging
import os


class RssConfig(object):
    _CONFIG_FILES = [os.path.join(os.path.dirname(__file__), 'Settings/Settings.ini')]
    _DEFAULT_CONFIG = {
        'MB': [
            ("patternfile", "str", "List of Movies - Each line should contain one Movie title", os.path.join(os.path.dirname(__file__), "Settings/Lists/Movies.txt")),
            ("db_file","str","Database used to ignore already downloaded Releases in the future",os.path.join(os.path.dirname(__file__), "Settings/Databases/Downloads_MB.db")),
            ("crawljob_directory","str","JDownloaders folderwatch directory for automatic link adding - Enable folderwatch!","/jd2/folderwatch"),
            ("ignore","str","Ignore pattern - Comma seperated list of Release tags to ignore","ts,cam,subbed,xvid,dvdr,untouched,remux,pal,md,ac3md,mic,xxx,hou"),
            ("interval", "int", "Execution interval of the script in minutes", "15"),
            ("quality", """480p;720p;1080p""", "Quality to look for in Release titles - 480p, 720p or 1080p", "720p"),
            ("pushbulletapi","str","Add your Pushbullet-API key if you want to be notified",""),
            ("hoster", """OBOOM;Uploaded;Share-Online;Zippyshare""", "Hoster to load from on MB - OBOOM, Uploaded, Share-Online or Zippyshare", "Uploaded"),
            ("historical","bool","Use search function - Disable if you only want current Releases to be added","True"),
            ("crawl3d","bool","Crawl for 3D versions of Movies - in 1080p, regardles of quality set above","False"),
            ("enforcedl", "bool", "If release without DL tag is added, look for DL release - ignoring quality setting", "False"),
            ("crawlseasons", "bool", "Crawl complete Seasons on MB", "False"),
            ("seasonslist", "str", "List of shows, to crawl for complete seasons - May be equal to SJ file", os.path.join(os.path.dirname(__file__), "Settings/Lists/Shows.txt")),
            ("seasonsquality", "str", "Quality of complete seasons to crawl for - 480p, 720p or 1080p", "720p"),
            ("seasonssource", "str", "Source tag to look for in complete seasons - e.g. bluray, web-dl or hdtv", "bluray")
        ],
        'SJ': [
            ("file", "str", "List of Shows - Each line should contain one Show title", os.path.join(os.path.dirname(__file__), "Settings/Lists/Shows.txt")),
            ("db_file","str","Database used to ignore already downloaded Releases in the future",os.path.join(os.path.dirname(__file__), "Settings/Databases/Downloads_SJ.db")),
            ("crawljob_directory","str","JDownloaders folderwatch directory for automatic link adding - Enable folderwatch!","/jd2/folderwatch"),
            ("rejectlist", "str", "Reject list - Semicolon seperated list of Release tags to ignore", "XviD;Subbed;HDTV"),
            ("interval", "int", "Execution interval of the script in minutes", "15"),
            ("pushbulletapi","str","Add your Pushbullet-API key if you want to be notified",""),
            ("language", """DEUTSCH;ENGLISCH""", "Language to load Shows in - DEUTSCH or ENGLISCH", "DEUTSCH"),
            ("quality", """480p;720p;1080p""", "Quality to look for in Release titles - 480p, 720p or 1080p", "720p"),
            ("hoster", """ul;so;fm;cz;alle""", "Hoster to load from on SJ - ul, so, fm, cz, alle", "ul"),
            ("regex","bool","Treat entries of the List as regular expressions - for advanced use cases", "Fals"),
            ("regex_file", "str", "List of Shows in RegEx scheme. Use this to crawl more precicely for Groups/Tags", os.path.join(os.path.dirname(__file__), "Settings/Lists/Shows_Regex.txt"))
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
