# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt die Konfiguration für den FeedCrawler bereit.

import base64
import configparser
import string

from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from Cryptodome.Util.Padding import pad

from feedcrawler.providers import shared_state
from feedcrawler.providers.sqlite_database import FeedDb


class CrawlerConfig(object):
    _DEFAULT_CONFIG = {
        'FeedCrawler': [
            ("auth_user", "secret", ""),
            ("auth_hash", "secret", ""),
            ("myjd_user", "secret", ""),
            ("myjd_pass", "secret", ""),
            ("myjd_device", "str", ""),
            ("myjd_auto_update", "bool", "False"),
            ("port", "int", "9090"),
            ("prefix", "str", ""),
            ("interval", "int", "60"),
            ("sponsors_helper", "str", ""),
            ("flaresolverr", "str", ""),
            ("english", "bool", "False"),
            ("surround", "bool", ""),
            ("one_mirror_policy", "bool", "False"),
            ("packages_per_myjd_page", "int", "3"),
            ("force_ignore_in_web_search", "bool", "False"),
        ],
        'Hostnames': [
            ("fx", "secret", ""),
            ("sf", "secret", ""),
            ("dw", "secret", ""),
            ("hw", "secret", ""),
            ("ff", "secret", ""),
            ("by", "secret", ""),
            ("nk", "secret", ""),
            ("nx", "secret", ""),
            ("ww", "secret", ""),
            ("sj", "secret", ""),
            ("dj", "secret", ""),
            ("dd", "secret", "")
        ],
        "Cloudflare": [
            ("wait_time", "int", "12"),
        ],
        'SponsorsHelper': [
            ("max_attempts", "int", "3"),
            ("hide_donation_banner", "bool", "False"),
        ],
        'Crawljobs': [
            ("autostart", "bool", "True"),
            ("subdir", "bool", "True"),
            ("subdir_by_type", "bool", "False"),
        ],
        'Notifications': [
            ("discord", "secret", ""),
            ("telegram", "secret", ""),
            ("pushbullet", "secret", ""),
            ("pushover", "secret", ""),
            ("homeassistant", "secret", ""),
        ],
        'Hosters': [
            ("ddl", "bool", "True"),
            ("rapidgator", "bool", "True"),
            ("1fichier", "bool", "True"),
            ("filer", "bool", "False"),
            ("turbobit", "bool", "False"),
            ("filefactory", "bool", "False"),
            ("uptobox", "bool", "False"),
            ("nitroflare", "bool", "False"),
            ("k2s", "bool", "False"),
            ("katfile", "bool", "False"),
            ("ironfiles", "bool", "False"),
        ],
        'Plex': [
            ("url", "str", ""),
            ("api", "secret", ""),
            ("client_id", "secret", ""),
            ("pin_code", "secret", ""),
            ("pin_id", "secret", ""),
        ],
        'Overseerr': [
            ("url", "str", ""),
            ("api", "secret", ""),
        ],
        'Ombi': [
            ("url", "str", ""),
            ("api", "secret", ""),
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
            ("imdbyear", "str", "2020"),
            ("imdb", "str", "6.5"),
            ("hevc_retail", "bool", "False"),
            ("retail_only", "bool", "False"),
            ("hoster_fallback", "bool", "False"),
        ],
        'ContentShows': [
            ("quality", "str", "1080p"),
            ("rejectlist", "str", "XviD,Subbed,HDTV"),
            ("regex", "bool", "False"),
            ("hevc_retail", "bool", "False"),
            ("retail_only", "bool", "False"),
            ("hoster_fallback", "bool", "False"),
        ],
        'CustomDJ': [
            ("quality", "str", "1080p"),
            ("rejectlist", "str", "XviD,Subbed,HDTV"),
            ("regex", "bool", "False"),
            ("hoster_fallback", "bool", "False"),
        ],
        'CustomDD': [
            ("hoster_fallback", "bool", "False"),
        ],
        'CustomF': [
            ("search", "int", "3"),
        ]
    }
    __config__ = []

    def __init__(self, section):
        self._configfile = shared_state.values["configfile"]
        self._section = section
        self._config = configparser.RawConfigParser()
        try:
            self._config.read(self._configfile)
            self._config.has_section(
                self._section) or self._set_default_config(self._section)
            self.__config__ = self._read_config(self._section)
        except configparser.DuplicateSectionError:
            print('Doppelte Sektion in der Konfigurationsdatei.')
            raise
        except:
            print('Ein unbekannter Fehler in der Konfigurationsdatei ist aufgetreten.')
            raise

    def _set_default_config(self, section):
        self._config.add_section(section)
        for (key, key_type, value) in self._DEFAULT_CONFIG[section]:
            self._config.set(section, key, value)
        with open(self._configfile, 'w') as configfile:
            self._config.write(configfile)

    def _get_encryption_params(self):
        crypt_key = FeedDb('secrets').retrieve("key")
        crypt_iv = FeedDb('secrets').retrieve("iv")
        if crypt_iv and crypt_key:
            return base64.b64decode(crypt_key), base64.b64decode(crypt_iv)
        else:
            crypt_key = get_random_bytes(32)
            crypt_iv = get_random_bytes(16)
            FeedDb('secrets').update_store("key", base64.b64encode(crypt_key).decode())
            FeedDb('secrets').update_store("iv", base64.b64encode(crypt_iv).decode())
            return crypt_key, crypt_iv

    def _set_to_config(self, section, key, value):
        default_value_type = [param[1] for param in self._DEFAULT_CONFIG[section] if param[0] == key]
        if default_value_type and default_value_type[0] == 'secret' and len(value):
            crypt_key, crypt_iv = self._get_encryption_params()
            cipher = AES.new(crypt_key, AES.MODE_CBC, crypt_iv)
            value = base64.b64encode(cipher.encrypt(pad(value.encode(), AES.block_size)))
            value = 'secret|' + value.decode()
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
        if [param for param in self._DEFAULT_CONFIG[self._section] if param[0] == key and param[1] == 'secret']:
            value = res[0].strip('\'"')
            if value.startswith("secret|"):
                crypt_key, crypt_iv = self._get_encryption_params()
                cipher = AES.new(crypt_key, AES.MODE_CBC, crypt_iv)
                decrypted_payload = cipher.decrypt(base64.b64decode(value[7:])).decode("utf-8").strip()
                final_payload = "".join(filter(lambda c: c in string.printable, decrypted_payload))
                return final_payload
            else:  ## Loaded value is not encrypted, return as is
                if len(value) > 0:
                    self.save(key, value)
                return value
        elif [param for param in self._DEFAULT_CONFIG[self._section] if param[0] == key and param[1] == 'bool']:
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

    def remove_redundant_entries(self):
        for section in self._config.sections():
            if section not in self._DEFAULT_CONFIG:
                self._config.remove_section(section)
                print(f"Entferne überflüssige Sektion '{section}' aus der Konfigurationsdatei.")
            else:
                for option in self._config.options(section):
                    if option not in [param[0] for param in self._DEFAULT_CONFIG[section]]:
                        self._config.remove_option(section, option)
                        print(
                            f"Entferne überflüssige Option '{option}' der Sektion '{section}' aus der Konfigurationsdatei.")
        with open(self._configfile, 'w') as configfile:
            self._config.write(configfile)
