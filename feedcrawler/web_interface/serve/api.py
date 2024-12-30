# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt die API des FeedCrawlers bereit.

import ast
import json
import os
import re
import site
import sys
import time
from functools import wraps
from urllib import parse
from xml.etree import ElementTree

from feedcrawler.providers.http_requests.request_handler import request as internal_request

if sys.stdout is None or sys.stderr is None:  # required to allow pyinstaller --noconsole to work with bottle
    from io import StringIO

    sys.stdout = StringIO()
    sys.stderr = StringIO()

from Cryptodome.Protocol.KDF import scrypt
from Cryptodome.Random import get_random_bytes
from bottle import Bottle, request, response, HTTPError, static_file, redirect, abort
from bs4 import BeautifulSoup

import feedcrawler.external_sites
from feedcrawler.external_sites.feed_search.shared import add_decrypt_instead_of_download
from feedcrawler.external_sites.web_search.shared import search_web
from feedcrawler.external_tools.myjd_api import TokenExpiredException, RequestTimeoutException, MYJDException
from feedcrawler.external_tools.plex_api import get_plex_headers, get_client_id
from feedcrawler.providers import shared_state, version
from feedcrawler.providers.common_functions import decode_base64, check_is_site, get_to_decrypt, remove_decrypt, \
    enable_decrypt, keep_alphanumeric_with_special_characters, keep_alphanumeric_with_regex_characters, keep_numbers, \
    disable_decrypt, rreplace
from feedcrawler.providers.config import CrawlerConfig
from feedcrawler.providers.myjd_connection import set_device, get_info, set_device_from_config, get_state, \
    set_enabled, move_to_downloads, remove_from_linkgrabber, reset_in_downloads, retry_decrypt, jdownloader_start, \
    jdownloader_pause, jdownloader_stop, jdownloader_update, get_packages_in_linkgrabber, download
from feedcrawler.providers.notifications import notify
from feedcrawler.providers.sqlite_database import FeedDb, ListDb
from feedcrawler.providers.url_functions import get_url_headers, post_url_headers, get_url
from feedcrawler.web_interface.serve.server import Server
from feedcrawler.external_sites.captcha.filecrypt import get_filecrypt_links

helper_active = False
already_added = []
auth_user = False
auth_hash = False
known_hashes = {}


def app_container():
    global helper_active
    global already_added
    global auth_user
    global auth_hash
    global known_hashes

    base_dir = './feedcrawler'
    if getattr(sys, 'frozen', False):
        base_dir = os.path.join(sys._MEIPASS).replace("\\", "/")
    elif os.environ.get('DOCKER'):
        static_location = site.getsitepackages()[0]
        base_dir = static_location + "/feedcrawler"

    general = CrawlerConfig('FeedCrawler')
    if general.get("prefix"):
        prefix = '/' + general.get("prefix")
    else:
        prefix = ''

    app = Bottle()

    config = CrawlerConfig('FeedCrawler')
    auth_user = config.get('auth_user')
    auth_hash = config.get('auth_hash')

    def auth_basic(check_func, realm="private", text="Access denied"):
        def decorator(func):
            @wraps(func)
            def wrapper(*a, **ka):
                global auth_user
                global auth_hash
                _config = CrawlerConfig('FeedCrawler')
                auth_user = _config.get('auth_user')
                auth_hash = _config.get('auth_hash')
                user, password = request.auth or (None, None)
                if auth_user and auth_hash:
                    if user is None or not check_func(user, password):
                        err = HTTPError(401, text)
                        err.add_header('WWW-Authenticate', f'Basic realm="{realm}"')
                        return err
                return func(*a, **ka)

            return wrapper

        return decorator

    def is_authenticated_user(user, password):
        global auth_user
        global auth_hash
        _config = CrawlerConfig('FeedCrawler')
        auth_user = _config.get('auth_user')
        auth_hash = _config.get('auth_hash')
        if auth_user and auth_hash:
            if auth_hash and "scrypt|" not in auth_hash:
                salt = get_random_bytes(16).hex()
                key = scrypt(auth_hash, salt, 16, N=2 ** 14, r=8, p=1).hex()
                auth_hash = "scrypt|" + salt + "|" + key
                _config.save("auth_hash", to_str(auth_hash))
            secrets = auth_hash.split("|")
            salt = secrets[1]
            config_hash = secrets[2]
            if password not in known_hashes:
                # Remember the hash for up to three passwords
                if len(known_hashes) > 2:
                    known_hashes.clear()
                sent_hash = scrypt(password, salt, 16, N=2 ** 14, r=8, p=1).hex()
                known_hashes[password] = sent_hash
            else:
                sent_hash = known_hashes[password]
            return user == _config.get("auth_user") and config_hash == sent_hash
        else:
            return True

    @app.get(prefix + '/')
    @auth_basic(is_authenticated_user)
    def catch_all():
        return static_file('index.html', root=base_dir + "/web_interface/vuejs_frontend/dist")

    @app.get('//<url:re:.*>')
    @auth_basic(is_authenticated_user)
    def redirect_double_slash(url):
        redirect_url = '/' + url
        if prefix and prefix not in redirect_url:
            redirect_url = prefix + redirect_url
        return redirect(redirect_url)

    @app.hook('before_request')
    def redirect_without_trailing_slash():
        no_trailing_slash = [
            "/assets/",
            "/favicon.ico",
            ".user.js",
            "/api/log_entry/",
            "/api/search/",
            "/api/download_movie/",
            "/api/download_show/",
            "/api/download_bl/",
            "/api/download_s/",
            "/api/myjd_enable/",
            "/api/myjd_disable/",
            "/api/myjd_move/",
            "/api/myjd_remove/",
            "/api/myjd_reset/",
            "/api/myjd_retry/",
            "/api/myjd_pause/",
            "/sponsors_helper/api/to_decrypt/",
            "/sponsors_helper/api/to_decrypt_disable/",
            "/sponsors_helper/replace_decrypt/",
            "/sponsors_helper/to_download/",
            "/captcha/"
        ]
        if not request.path.endswith('/') and not any(s in request.path for s in no_trailing_slash):
            raise redirect(request.url + '/')

    if prefix:
        @app.get('/')
        @auth_basic(is_authenticated_user)
        def index_prefix():
            return redirect(prefix)

    @app.get(prefix + '/assets/<filename>')
    def static_files(filename):
        return static_file(filename, root=base_dir + "/web_interface/vuejs_frontend/dist/assets")

    @app.get(prefix + '/favicon.ico')
    def static_favicon():
        return static_file('favicon.ico', root=base_dir + "/web_interface/vuejs_frontend/dist/")

    def to_int(i):
        if isinstance(i, bytes):
            i = i.decode()
        i = str(i).strip().replace("None", "")
        return int(i) if i else ""

    def to_float(i):
        i = str(i).strip().replace("None", "")
        return float(i) if i else ""

    def to_str(i):
        return '' if i is None else str(i)

    def to_bool(i):
        return True if i == "True" else False

    def check(site, db):
        return to_bool(str(db.retrieve(site)).replace("Blocked", "True"))

    @app.get(prefix + "/api/log/")
    @auth_basic(is_authenticated_user)
    def get_log():
        try:
            log = []
            if os.path.isfile(shared_state.values["log_file"]):
                logfile = open(shared_state.values["log_file"])
                i = 0
                for line in reversed(logfile.readlines()):
                    if line and line != "\n":
                        payload = [i]
                        line = line.replace("]", "")
                        line = line.replace("[", "")
                        line = re.sub(r",\d{3}", "", line)
                        line = line.split(" - ")
                        for line_part in line:
                            payload.append(line_part)
                        log.append(payload)
                    i += 1
            return {
                "log": log,
            }

        except:
            return abort(400, "Failed")

    @app.delete(prefix + "/api/log/")
    @auth_basic(is_authenticated_user)
    def delete_log():
        try:
            open(shared_state.values["log_file"], 'w').close()
            return "Success"
        except:
            return abort(400, "Failed")

    @app.delete(prefix + "/api/log_entry/<b64_entry>")
    @auth_basic(is_authenticated_user)
    def delete_log_entry(b64_entry):
        try:
            entry = decode_base64(b64_entry)
            log = []
            if os.path.isfile(shared_state.values["log_file"]):
                logfile = open(shared_state.values["log_file"])
                for line in reversed(logfile.readlines()):
                    if line and line != "\n":
                        if entry not in line:
                            log.append(line)
                log = "".join(reversed(log))
                with open(shared_state.values["log_file"], 'w') as file:
                    file.write(log)
            return "Success"
        except:
            return abort(400, "Failed")

    @app.get(prefix + "/redirect_sponsors/")
    def redirect_sponsors():
        redirect("https://github.com/sponsors/rix1337")

    @app.get(prefix + "/redirect_captcha/")
    def redirect_captcha():
        redirect("https://deathbycaptcha.com/register?refid=6184288242b")

    @app.get(prefix + "/redirect_hoster/")
    def redirect_captcha():
        redirect("https://linksnappy.com/?ref=397097")

    @app.get(prefix + "/api/settings/")
    @auth_basic(is_authenticated_user)
    def get_settings():
        try:
            general_conf = CrawlerConfig('FeedCrawler')
            hosters = CrawlerConfig('Hosters')
            alerts = CrawlerConfig('Notifications')
            plex = CrawlerConfig('Plex')
            ombi = CrawlerConfig('Ombi')
            overseerr = CrawlerConfig('Overseerr')
            crawljobs = CrawlerConfig('Crawljobs')
            mb_conf = CrawlerConfig('ContentAll')
            sj_conf = CrawlerConfig('ContentShows')
            dj_conf = CrawlerConfig('CustomDJ')
            dd_conf = CrawlerConfig('CustomDD')
            f_conf = CrawlerConfig('CustomF')
            cloudflare_conf = CrawlerConfig('Cloudflare')
            helper_conf = CrawlerConfig('SponsorsHelper')
            if os.environ.get('DOCKER'):
                port = 9090
            else:
                port = to_int(general_conf.get("port"))
            return {
                "settings": {
                    "general": {
                        "auth_user": general_conf.get("auth_user"),
                        "auth_hash": "",  # This is always empty to not leak password hashes
                        "myjd_user": general_conf.get("myjd_user"),
                        "myjd_pass": general_conf.get("myjd_pass"),
                        "myjd_device": general_conf.get("myjd_device"),
                        "myjd_auto_update": general_conf.get("myjd_auto_update"),
                        "port": port,
                        "prefix": general_conf.get("prefix"),
                        "interval": to_int(general_conf.get("interval")),
                        "flaresolverr": general_conf.get("flaresolverr"),
                        "english": general_conf.get("english"),
                        "surround": general_conf.get("surround"),
                        "one_mirror_policy": general_conf.get("one_mirror_policy"),
                        "packages_per_myjd_page": to_int(general_conf.get("packages_per_myjd_page")),
                        "force_ignore_in_web_search": general_conf.get("force_ignore_in_web_search"),
                    },
                    "hosters": {
                        "ddl": hosters.get("ddl"),
                        "rapidgator": hosters.get("rapidgator"),
                        "onefichier": hosters.get("1fichier"),
                        "filer": hosters.get("filer"),
                        "turbobit": hosters.get("turbobit"),
                        "filefactory": hosters.get("filefactory"),
                        "uptobox": hosters.get("uptobox"),
                        "nitroflare": hosters.get("nitroflare"),
                        "k2s": hosters.get("k2s"),
                        "katfile": hosters.get("katfile"),
                        "ironfiles": hosters.get("ironfiles"),
                    },
                    "alerts": {
                        "telegram": alerts.get("telegram"),
                        "discord": alerts.get("discord"),
                        "pushbullet": alerts.get("pushbullet"),
                        "pushover": alerts.get("pushover"),
                        "homeassistant": alerts.get("homeassistant"),
                    },
                    "plex": {
                        "url": plex.get("url"),
                        "api": bool(plex.get("api")),
                    },
                    "ombi": {
                        "url": ombi.get("url"),
                        "api": ombi.get("api"),
                    },
                    "overseerr": {
                        "url": overseerr.get("url"),
                        "api": overseerr.get("api"),
                    },
                    "crawljobs": {
                        "autostart": crawljobs.get("autostart"),
                        "subdir": crawljobs.get("subdir"),
                        "subdir_by_type": crawljobs.get("subdir_by_type"),
                    },
                    "mb": {
                        "quality": mb_conf.get("quality"),
                        "search": mb_conf.get("search"),
                        "ignore": mb_conf.get("ignore"),
                        "regex": mb_conf.get("regex"),
                        "imdb_score": to_float(mb_conf.get("imdb")),
                        "imdb_year": to_int(mb_conf.get("imdbyear")),
                        "force_dl": mb_conf.get("enforcedl"),
                        "cutoff": mb_conf.get("cutoff"),
                        "hevc_retail": mb_conf.get("hevc_retail"),
                        "retail_only": mb_conf.get("retail_only"),
                        "hoster_fallback": mb_conf.get("hoster_fallback"),
                    },
                    "sj": {
                        "quality": sj_conf.get("quality"),
                        "ignore": sj_conf.get("rejectlist"),
                        "regex": sj_conf.get("regex"),
                        "hevc_retail": sj_conf.get("hevc_retail"),
                        "retail_only": sj_conf.get("retail_only"),
                        "hoster_fallback": sj_conf.get("hoster_fallback"),
                    },
                    "mbsj": {
                        "enabled": mb_conf.get("crawlseasons"),
                        "quality": mb_conf.get("seasonsquality"),
                        "packs": mb_conf.get("seasonpacks"),
                        "source": mb_conf.get("seasonssource"),
                    },
                    "dj": {
                        "quality": dj_conf.get("quality"),
                        "ignore": dj_conf.get("rejectlist"),
                        "regex": dj_conf.get("regex"),
                        "hoster_fallback": dj_conf.get("hoster_fallback"),
                    },
                    "dd": {
                        "hoster_fallback": dd_conf.get("hoster_fallback"),
                    },
                    "f": {
                        "search": to_int(f_conf.get("search"))
                    },
                    "cloudflare": {
                        "wait_time": to_int(cloudflare_conf.get("wait_time")),
                    },
                    "sponsors_helper": {
                        "max_attempts": to_int(helper_conf.get("max_attempts")),
                        "hide_donation_banner": helper_conf.get("hide_donation_banner"),
                    }
                }
            }
        except:
            return abort(400, "Failed")

    @app.post(prefix + "/api/settings/")
    @auth_basic(is_authenticated_user)
    def post_settings():
        try:
            data = request.json

            section = CrawlerConfig("FeedCrawler")
            section.save(
                "auth_user", to_str(data['general']['auth_user']))

            password_hash = data['general']['auth_hash']
            if password_hash and "scrypt|" not in password_hash:
                salt = get_random_bytes(16).hex()
                key = scrypt(password_hash, salt, 16, N=2 ** 14, r=8, p=1).hex()
                password_hash = "scrypt|" + salt + "|" + key
                section.save(
                    "auth_hash", to_str(password_hash))

            myjd_user = to_str(data['general']['myjd_user'])
            myjd_pass = to_str(data['general']['myjd_pass'])
            myjd_device = to_str(data['general']['myjd_device'])

            if myjd_user and myjd_pass and myjd_device:
                device_check = set_device(myjd_user, myjd_pass, myjd_device)
                if not device_check:
                    print("Fehlerhafte My-JDownloader-Zugangsdaten. Bitte vor dem Speichern prüfen!")
                    return abort(400, "Failed")

            myjd_auto_update = to_str(data['general']['myjd_auto_update'])

            section.save("myjd_user", myjd_user)
            section.save("myjd_pass", myjd_pass)
            section.save("myjd_device", myjd_device)
            section.save("myjd_auto_update", myjd_auto_update)
            if os.environ.get('DOCKER'):
                port = "9090"
            else:
                port = to_str(data['general']['port'])
            section.save("port", port)
            section.save("prefix", to_str(data['general']['prefix']).lower())
            interval = to_str(data['general']['interval'])
            if to_int(interval) < 5:
                interval = '5'
            section.save("interval", interval)
            section.save("flaresolverr", to_str(data['general']['flaresolverr']))
            section.save("english", to_str(data['general']['english']))
            section.save("surround", to_str(data['general']['surround']))
            section.save("one_mirror_policy", to_str(data['general']['one_mirror_policy']))
            section.save("packages_per_myjd_page", to_str(data['general']['packages_per_myjd_page']))
            section.save("force_ignore_in_web_search", to_str(data['general']['force_ignore_in_web_search']))

            section = CrawlerConfig("Crawljobs")
            section.save("autostart", to_str(data['crawljobs']['autostart']))
            section.save("subdir", to_str(data['crawljobs']['subdir']))
            section.save("subdir_by_type", to_str(data['crawljobs']['subdir_by_type']))

            section = CrawlerConfig("Notifications")
            section.save("telegram", to_str(data['alerts']['telegram']))
            section.save("discord", to_str(data['alerts']['discord']))
            section.save("pushbullet", to_str(data['alerts']['pushbullet']))
            section.save("pushover", to_str(data['alerts']['pushover']))
            section.save("homeassistant", to_str(data['alerts']['homeassistant']))

            section = CrawlerConfig("Hosters")
            section.save("ddl", to_str(data['hosters']['ddl']))
            section.save("rapidgator", to_str(data['hosters']['rapidgator']))
            section.save("1fichier", to_str(data['hosters']['onefichier']))
            section.save("filer", to_str(data['hosters']['filer']))
            section.save("turbobit", to_str(data['hosters']['turbobit']))
            section.save("filefactory", to_str(data['hosters']['filefactory']))
            section.save("uptobox", to_str(data['hosters']['uptobox']))
            section.save("nitroflare", to_str(data['hosters']['nitroflare']))
            section.save("k2s", to_str(data['hosters']['k2s']))
            section.save("katfile", to_str(data['hosters']['katfile']))
            section.save("ironfiles", to_str(data['hosters']['ironfiles']))

            section = CrawlerConfig("Plex")
            section.save("url", to_str(data['plex']['url']))

            section = CrawlerConfig("Ombi")
            ombi_url = to_str(data['ombi']['url'])
            ombi_url = ombi_url[:-1] if ombi_url.endswith('/') else ombi_url
            ombi_api = to_str(data['ombi']['api'])
            if not ombi_url or not ombi_api:
                ombi_url = ""
                ombi_api = ""
            section.save("url", ombi_url)
            section.save("api", ombi_api)

            section = CrawlerConfig("Overseerr")
            overseerr_url = to_str(data['overseerr']['url'])
            overseerr_url = overseerr_url[:-1] if overseerr_url.endswith('/') else overseerr_url
            overseerr_api = to_str(data['overseerr']['api'])
            if not overseerr_url or not overseerr_api:
                overseerr_url = ""
                overseerr_api = ""
            section.save("url", overseerr_url)
            section.save("api", overseerr_api)

            section = CrawlerConfig("ContentAll")
            section.save("quality", to_str(data['mb']['quality']))
            section.save("search", to_str(data['mb']['search']))
            section.save("ignore", to_str(data['mb']['ignore']).lower())
            section.save("regex", to_str(data['mb']['regex']))
            section.save("cutoff", to_str(data['mb']['cutoff']))
            section.save("enforcedl", to_str(data['mb']['force_dl']))
            section.save("crawlseasons", to_str(data['mbsj']['enabled']))
            section.save("seasonsquality", to_str(data['mbsj']['quality']))
            section.save("seasonpacks", to_str(data['mbsj']['packs']))
            section.save("seasonssource", to_str(data['mbsj']['source']).lower())
            section.save("imdbyear", to_str(data['mb']['imdb_year']))
            imdb = to_str(data['mb']['imdb_score'])
            if re.match('[^0-9]', imdb):
                imdb = 0.0
            elif imdb == '':
                imdb = 0.0
            else:
                imdb = round(float(to_str(data['mb']['imdb_score']).replace(",", ".")), 1)
            if imdb > 10:
                imdb = 10.0
            section.save("imdb", to_str(imdb))
            section.save("hevc_retail", to_str(data['mb']['hevc_retail']))
            section.save("retail_only", to_str(data['mb']['retail_only']))
            section.save("hoster_fallback", to_str(data['mb']['hoster_fallback']))

            section = CrawlerConfig("ContentShows")
            section.save("quality", to_str(data['sj']['quality']))
            section.save("rejectlist", to_str(data['sj']['ignore']).lower())
            section.save("regex", to_str(data['sj']['regex']))
            section.save("hevc_retail", to_str(data['sj']['hevc_retail']))
            section.save("retail_only", to_str(data['sj']['retail_only']))
            section.save("hoster_fallback", to_str(data['sj']['hoster_fallback']))

            section = CrawlerConfig("CustomDJ")
            section.save("quality", to_str(data['dj']['quality']))
            section.save("rejectlist", to_str(data['dj']['ignore']).lower())
            section.save("regex", to_str(data['dj']['regex']))
            section.save("hoster_fallback", to_str(data['dj']['hoster_fallback']))

            section = CrawlerConfig("CustomDD")
            section.save("hoster_fallback", to_str(data['dd']['hoster_fallback']))

            section = CrawlerConfig("CustomF")
            search_depth = to_str(data['f']['search'])
            if to_int(search_depth) > 7:
                search_depth = '7'
            section.save("search", search_depth)

            section = CrawlerConfig("Cloudflare")
            wait_time = to_str(data['cloudflare']['wait_time'])
            if to_int(wait_time) < 6:
                wait_time = '6'
            section.save("wait_time", wait_time)

            section = CrawlerConfig("SponsorsHelper")
            max_attempts = to_str(data['sponsors_helper']['max_attempts'])
            if to_int(max_attempts) > 10:
                max_attempts = '10'
            section.save("max_attempts", max_attempts)
            section.save("hide_donation_banner", to_str(data['sponsors_helper']['hide_donation_banner']))

            return "Success"
        except:
            return abort(400, "Failed")

    @app.get(prefix + "/api/plex_auth/")
    @auth_basic(is_authenticated_user)
    def get_plex_token():
        auth_url = ""
        try:
            plex_config = CrawlerConfig('Plex')

            plex_config.save('pin_id', '')
            plex_config.save('pin_code', '')

            token = plex_config.get('api')
            if token:
                headers = get_plex_headers(token)
                token_valid = get_url_headers('https://plex.tv/api/v2/user', headers=headers)
                if token_valid["status_code"] == 200:
                    return "Plex-Token ist bereits konfiguriert und gültig!"
                if token_valid["status_code"] == 401:
                    token = ''
                    plex_config.save('api', token)
                else:
                    return abort(400, "Plex-API reagiert nicht. Token konnte nicht geprüft werden.")

            origin = parse.urlparse(request.url)
            origin_url = origin.scheme + "://" + origin.netloc
            generate_pin = post_url_headers('https://plex.tv/api/v2/pins?strong=true', headers={
                'accept': 'application/json',
                'X-Plex-Product': 'FeedCrawler',
                'X-Plex-Client-Identifier': get_client_id(),
                'Origin': origin_url
            })

            if generate_pin["status_code"] == 201:
                response = json.loads(generate_pin["text"])
                pin_id = response['id']
                pin_code = response['code']
                plex_config.save('pin_id', str(pin_id))
                plex_config.save('pin_code', str(pin_code))
            else:
                return abort(400, "Plex-API reagiert nicht. PIN konnte nicht erzeugt werden.")

            return_url = request.url.replace("/api/plex_auth/", "/api/plex_pin/")
            client_id = get_client_id()
            auth_url = "https://app.plex.tv/auth#" \
                       "?clientID=" + client_id + \
                       "&code=" + pin_code + \
                       "&context%5Bdevice%5D%5Bproduct%5D=FeedCrawler" + \
                       "&forwardUrl=" + parse.quote(return_url, safe='')

        except:
            time.sleep(3)
            pass

        if auth_url:
            redirect(auth_url)
        else:
            return abort(400, "Failed")

    @app.get(prefix + "/api/plex_pin/")
    @auth_basic(is_authenticated_user)
    def get_plex_pin():
        token = ""
        plex_config = CrawlerConfig('Plex')

        try:
            pin_id = plex_config.get('pin_id')
            pin_code = plex_config.get('pin_code')

            check_pin = get_url_headers('https://plex.tv/api/v2/pins/' + pin_id, headers={
                'code': pin_code,
                'X-Plex-Client-Identifier': get_client_id()
            })

            if check_pin["status_code"] == 200:
                response = ElementTree.fromstring(check_pin["text"])
                token = response.attrib['authToken']
                if token and str(token) != 'null':
                    plex_config.save('api', token)
        except:
            time.sleep(3)
            pass

        plex_config.save('pin_id', '')
        plex_config.save('pin_code', '')

        if token:
            return ("Plex-Token wurde erfolgreich gespeichert! <a href='../..'>Zurück</a>")
        else:
            return abort(400, "Die Authentifizierung war nicht erfolgreich. Bitte erneut versuchen.")

    @app.get(prefix + "/api/plex_server_urls/")
    @auth_basic(is_authenticated_user)
    def get_plex_server_urls():
        plex_servers = []
        try:
            plex_config = CrawlerConfig('Plex')
            token = plex_config.get('api')
            plex_headers = get_plex_headers(token)

            servers = get_url_headers('https://plex.tv/api/v2/resources?includeHttps=1', headers=plex_headers)
            root = ElementTree.fromstring(servers["text"])

            for resource in root.findall('resource'):
                if resource.get('product') == 'Plex Media Server':
                    for connection in resource.findall('connections/connection'):
                        is_local = connection.get('local') == '1'
                        plex_servers.append({
                            'url': connection.get('uri'),
                            'is_local': is_local
                        })
        except:
            shared_state.logger.debug("Fehler beim Abruf der Plex-Server.")
            pass

        if plex_servers:
            return json.dumps(plex_servers)
        else:
            return abort(400, "Abruf der Plex-Server-IPs fehlgeschlagen.")

    @app.get(prefix + "/api/version/")
    @auth_basic(is_authenticated_user)
    def get_version():
        try:
            is_update_ready = False
            update_check = version.update_check()
            if update_check[0]:
                is_update_ready = True
                print(f'Update steht bereit ({update_check[1]})! '
                      f'Weitere Informationen unter https://github.com/rix1337/FeedCrawler/releases/latest')
            return {
                "version": {
                    "ver": "v." + version.get_version(),
                    "update_ready": is_update_ready,
                    "docker": bool(os.environ.get('DOCKER')),
                    "helper_active": helper_active
                }
            }
        except:
            return abort(400, "Failed")

    @app.get(prefix + "/api/crawltimes/")
    @auth_basic(is_authenticated_user)
    def get_crawltimes():
        try:
            crawltimes = FeedDb("crawltimes")
            next_cloudflare_run = False
            try:
                last_cloudflare_run = to_float(FeedDb('crawltimes').retrieve("last_cloudflare_run"))
                cloudflare_wait_time = to_float(CrawlerConfig('Cloudflare').get("wait_time"))
                if last_cloudflare_run:
                    next_cloudflare_run = last_cloudflare_run + 1000 * cloudflare_wait_time * 60 * 60
            except:
                pass
            return {
                "crawltimes": {
                    "active": to_bool(crawltimes.retrieve("active")),
                    "start_time": to_float(crawltimes.retrieve("start_time")),
                    "end_time": to_float(crawltimes.retrieve("end_time")),
                    "total_time": crawltimes.retrieve("total_time"),
                    "next_start": to_float(crawltimes.retrieve("next_start")),
                    "next_cloudflare_run": next_cloudflare_run
                }
            }
        except:
            time.sleep(3)
            return abort(400, "Failed")

    @app.get(prefix + "/api/hostnames/")
    @auth_basic(is_authenticated_user)
    def get_hostnames():
        try:
            hostnames = CrawlerConfig('Hostnames')

            fx = hostnames.get('fx').replace("f", "F", 1).replace("d", "D", 1).replace("x", "X", 1)
            dw = hostnames.get("dw").replace("d", "D", 2).replace("l", "L", 1).replace("w", "W", 1)
            hw = hostnames.get('hw').replace("h", "H", 1).replace("d", "D", 1).replace("w", "W", 1)
            ff = hostnames.get('ff').replace("f", "F", 2)
            by = hostnames.get('by').replace("b", "B", 1)
            nk = hostnames.get('nk').replace("n", "N", 1).replace("k", "K", 1)
            nx = hostnames.get('nx').replace("o", "O", 1).replace("x", "X", 1).replace("n", "N", 1)
            ww = hostnames.get('ww').replace("w", "W", 2)
            sf = hostnames.get('sf').replace("s", "S", 1).replace("f", "F", 1)
            sj = hostnames.get('sj').replace("s", "S", 1).replace("j", "J", 1)
            dj = hostnames.get('dj').replace("d", "D", 1).replace("j", "J", 1)
            dd = hostnames.get('dd').replace("d", "D", 2).replace("l", "L", 1)

            bl = ' / '.join(list(filter(None, [fx, dw, hw, ff, by, nk, nx, ww])))
            s = ' / '.join(list(filter(None, [sf, sj])))
            f = ' / '.join(list(filter(None, [sf, ff])))
            sjbl = ' / '.join(list(filter(None, [s, bl])))
            cloudflare = ' / '.join(list(filter(None, [sj, dj, sf, ff, hw, ww])))  # all sites know to use cloudflare
            search = '/'.join(list(filter(None, [fx, sf, hw, by, nk, nx, sj, dj])))

            def check_if_set(value):
                if not value:
                    return "Nicht gesetzt!"
                else:
                    return value

            cloudflare_shorthands = []
            for site_name in cloudflare.split(" / "):
                site_shorthand = check_is_site(site_name)
                if site_shorthand:
                    cloudflare_shorthands.append(site_shorthand)
            cloudflare_shorthands = "/".join(cloudflare_shorthands)

            return {
                "hostnames": {
                    "fx": check_if_set(fx),
                    "sf": check_if_set(sf),
                    "dw": check_if_set(dw),
                    "hw": check_if_set(hw),
                    "ff": check_if_set(ff),
                    "by": check_if_set(by),
                    "nk": check_if_set(nk),
                    "nx": check_if_set(nx),
                    "ww": check_if_set(ww),
                    "sj": check_if_set(sj),
                    "dj": check_if_set(dj),
                    "dd": check_if_set(dd),
                    "bl": check_if_set(bl),
                    "s": check_if_set(s),
                    "f": check_if_set(f),
                    "sjbl": check_if_set(sjbl),
                    "cloudflare": check_if_set(cloudflare),
                    "cloudflare_shorthands": check_if_set(cloudflare_shorthands),
                    "search": check_if_set(search)
                }
            }
        except:
            return abort(400, "Failed")

    @app.get(prefix + "/api/blocked_sites/")
    @auth_basic(is_authenticated_user)
    def get_blocked_sites():
        try:
            db_status = FeedDb('site_status')
            return {
                "blocked_sites": {
                    "normal": {
                        "SJ": check("SJ_normal", db_status),
                        "DJ": check("DJ_normal", db_status),
                        "SF": check("SF_normal", db_status),
                        "BY": check("BY_normal", db_status),
                        "FX": check("FX_normal", db_status),
                        "HW": check("HW_normal", db_status),
                        "FF": check("FF_normal", db_status),
                        "NK": check("NK_normal", db_status),
                        "NX": check("NX_normal", db_status),
                        "WW": check("WW_normal", db_status)
                    },
                    "advanced": {
                        "SJ": check("SJ_advanced", db_status),
                        "DJ": check("DJ_advanced", db_status),
                        "SF": check("SF_advanced", db_status),
                        "BY": check("BY_advanced", db_status),
                        "FX": check("FX_advanced", db_status),
                        "HW": check("HW_advanced", db_status),
                        "FF": check("FF_advanced", db_status),
                        "NK": check("NK_advanced", db_status),
                        "NX": check("NX_advanced", db_status),
                        "WW": check("WW_advanced", db_status)
                    }
                }
            }
        except:
            return abort(400, "Failed")

    @app.post(prefix + "/api/start_now/")
    @auth_basic(is_authenticated_user)
    def start_now():
        try:
            FeedDb('crawltimes').store("startnow", "True")
            i = 15
            started = False
            while i > 0:
                if not FeedDb('crawltimes').retrieve("startnow"):
                    started = True
                    break
                i -= 1
                time.sleep(1)
            if started:
                return "Success"
            else:
                return abort(400, "Failed")
        except:
            return abort(400, "Failed")

    @app.post(prefix + "/api/search/<title>")
    @auth_basic(is_authenticated_user)
    def search_title(title):
        try:
            if len(title) < 3:
                return abort(400, "Search term too short!")
            data = request.json
            movies_only = data.get('movies_only')
            shows_only = data.get('shows_only')
        except:
            movies_only = False
            shows_only = False
        try:
            results = search_web(title, only_content_movies=movies_only, only_content_shows=shows_only)
            return {
                "results": {
                    "bl": results[0],
                    "sj": results[1],
                    "sf": results[2]
                }
            }
        except:
            return abort(400, "Failed")

    @app.post(prefix + "/api/download_movie/<title>")
    @auth_basic(is_authenticated_user)
    def download_movie(title):
        try:
            payload = feedcrawler.external_sites.web_search.content_all.get_best_result(title)
            if payload:
                matches = feedcrawler.external_sites.web_search.content_all.download(payload)
                return "Success: " + str(matches)
        except Exception as e:
            shared_state.logger.debug("An exception was thrown: " + str(e))
            pass
        return abort(400, "Failed")

    @app.post(prefix + "/api/download_show/<title>")
    @auth_basic(is_authenticated_user)
    def download_show(title):
        shared_state.logger.debug(f'Recieved API-Request for: {title}')
        try:
            payload = feedcrawler.external_sites.web_search.content_shows.get_best_result(title)
            shared_state.logger.debug(f'Found payload is: {payload}')
            if payload:
                matches = feedcrawler.external_sites.web_search.content_shows.download(payload)
                if matches:
                    return "Success: " + str(matches)
        except Exception as e:
            shared_state.logger.debug("An exception was thrown: " + str(e))
            pass
        return abort(400, "Failed")

    @app.post(prefix + "/api/download_bl/<payload>")
    @auth_basic(is_authenticated_user)
    def download_bl(payload):
        try:
            if feedcrawler.external_sites.web_search.content_all.download(payload):
                return "Success"
        except:
            pass
        return abort(400, "Failed")

    @app.post(prefix + "/api/download_s/<payload>")
    @auth_basic(is_authenticated_user)
    def download_s(payload):
        try:
            if feedcrawler.external_sites.web_search.content_shows.download(payload):
                return "Success"
        except:
            pass
        return abort(400, "Failed")

    @app.get(prefix + "/api/myjd/")
    @auth_basic(is_authenticated_user)
    def myjd_info():
        try:
            try:
                myjd = get_info()
                packages_to_decrypt = get_to_decrypt()
                packages_to_decrypt_disabled = get_to_decrypt(disabled=True)
                general_conf = CrawlerConfig('FeedCrawler')
                packages_per_myjd_page = to_int(general_conf.get("packages_per_myjd_page"))
            except (TokenExpiredException, RequestTimeoutException, MYJDException):
                set_device_from_config()
                if not shared_state.get_device():
                    return abort(500, "Failed")
                myjd = get_info()
                packages_to_decrypt = get_to_decrypt()
                packages_to_decrypt_disabled = get_to_decrypt(disabled=True)
                packages_per_myjd_page = 3
            if myjd:
                return {
                    "downloader_state": myjd[1],
                    "grabber_collecting": myjd[2],
                    "update_ready": myjd[3],
                    "packages": {
                        "downloader": myjd[4][0],
                        "linkgrabber_decrypted": myjd[4][1],
                        "linkgrabber_offline": myjd[4][2],
                        "linkgrabber_failed": myjd[4][3],
                        "to_decrypt": packages_to_decrypt,
                        "to_decrypt_disabled": packages_to_decrypt_disabled
                    },
                    "packages_per_myjd_page": packages_per_myjd_page
                }
        except:
            pass
        return abort(400, "Failed")

    @app.get(prefix + "/api/myjd_state/")
    @auth_basic(is_authenticated_user)
    def myjd_state():
        try:
            try:
                myjd = get_state()
            except (TokenExpiredException, RequestTimeoutException, MYJDException):
                set_device_from_config()
                if not shared_state.get_device():
                    return abort(500, "Failed")
                myjd = get_state()
            if myjd:
                return {
                    "downloader_state": myjd[1],
                    "grabber_collecting": myjd[2]
                }
        except:
            pass
        return abort(400, "Failed")

    @app.post(prefix + "/api/myjd_enable/<linkids>&<uuids>")
    @auth_basic(is_authenticated_user)
    def myjd_enable(linkids, uuids):
        try:
            linkids_raw = ast.literal_eval(linkids)
            linkids = []
            if isinstance(linkids_raw, (list, tuple)):
                for linkid in linkids_raw:
                    linkids.append(linkid)
            else:
                linkids.append(linkids_raw)
            uuids_raw = ast.literal_eval(uuids)
            uuids = []
            if isinstance(uuids_raw, (list, tuple)):
                for uuid in uuids_raw:
                    uuids.append(uuid)
            else:
                uuids.append(uuids_raw)
            if set_enabled(True, linkids, uuids):
                return "Success"
        except:
            pass
        return abort(400, "Failed")

    @app.post(prefix + "/api/myjd_disable/<linkids>&<uuids>")
    @auth_basic(is_authenticated_user)
    def myjd_disable(linkids, uuids):
        try:
            linkids_raw = ast.literal_eval(linkids)
            linkids = []
            if isinstance(linkids_raw, (list, tuple)):
                for linkid in linkids_raw:
                    linkids.append(linkid)
            else:
                linkids.append(linkids_raw)
            uuids_raw = ast.literal_eval(uuids)
            uuids = []
            if isinstance(uuids_raw, (list, tuple)):
                for uuid in uuids_raw:
                    uuids.append(uuid)
            else:
                uuids.append(uuids_raw)
            if set_enabled(False, linkids, uuids):
                return "Success"
        except:
            pass
        return abort(400, "Failed")

    @app.post(prefix + "/api/myjd_move/<linkids>&<uuids>")
    @auth_basic(is_authenticated_user)
    def myjd_move(linkids, uuids):
        try:
            linkids_raw = ast.literal_eval(linkids)
            linkids = []
            if isinstance(linkids_raw, (list, tuple)):
                for linkid in linkids_raw:
                    linkids.append(linkid)
            else:
                linkids.append(linkids_raw)
            uuids_raw = ast.literal_eval(uuids)
            uuids = []
            if isinstance(uuids_raw, (list, tuple)):
                for uuid in uuids_raw:
                    uuids.append(uuid)
            else:
                uuids.append(uuids_raw)
            if move_to_downloads(linkids, uuids):
                return "Success"
        except:
            pass
        return abort(400, "Failed")

    @app.post(prefix + "/api/myjd_remove/<linkids>&<uuids>")
    @auth_basic(is_authenticated_user)
    def myjd_remove(linkids, uuids):
        try:
            linkids_raw = ast.literal_eval(linkids)
            linkids = []
            if isinstance(linkids_raw, (list, tuple)):
                for linkid in linkids_raw:
                    linkids.append(linkid)
            else:
                linkids.append(linkids_raw)
            uuids_raw = ast.literal_eval(uuids)
            uuids = []
            if isinstance(uuids_raw, (list, tuple)):
                for uuid in uuids_raw:
                    uuids.append(uuid)
            else:
                uuids.append(uuids_raw)
            if remove_from_linkgrabber(linkids, uuids):
                return "Success"
        except:
            pass
        return abort(400, "Failed")

    @app.post(prefix + "/api/myjd_reset/<linkids>&<uuids>")
    @auth_basic(is_authenticated_user)
    def myjd_reset(linkids, uuids):
        try:
            linkids_raw = ast.literal_eval(linkids)
            linkids = []
            if isinstance(linkids_raw, (list, tuple)):
                for linkid in linkids_raw:
                    linkids.append(linkid)
            else:
                linkids.append(linkids_raw)
            uuids_raw = ast.literal_eval(uuids)
            uuids = []
            if isinstance(uuids_raw, (list, tuple)):
                for uuid in uuids_raw:
                    uuids.append(uuid)
            else:
                uuids.append(uuids_raw)
            if reset_in_downloads(linkids, uuids):
                return "Success"
        except:
            pass
        return abort(400, "Failed")

    @app.post(prefix + "/api/internal_remove/")
    @auth_basic(is_authenticated_user)
    def internal_remove():
        try:
            data = request.body.read().decode("utf-8")
            payload = json.loads(data)
            name = payload["name"]
            delete = remove_decrypt(name)
            delete_disabled = remove_decrypt(name, disabled=True)
            if delete or delete_disabled:
                return "Success"
        except:
            pass
        return abort(400, "Failed")

    @app.post(prefix + "/api/internal_retry/")
    @auth_basic(is_authenticated_user)
    def internal_remove():
        try:
            data = request.body.read().decode("utf-8")
            payload = json.loads(data)
            name = payload["name"]
            reactivated_disabled = enable_decrypt(name)
            if reactivated_disabled:
                return "Success"
        except:
            pass
        return abort(400, "Failed")

    @app.post(prefix + "/api/myjd_retry/<linkids>&<uuids>&<b64_links>")
    @auth_basic(is_authenticated_user)
    def myjd_retry(linkids, uuids, b64_links):
        try:
            linkids_raw = ast.literal_eval(linkids)
            linkids = []
            if isinstance(linkids_raw, (list, tuple)):
                for linkid in linkids_raw:
                    linkids.append(linkid)
            else:
                linkids.append(linkids_raw)
            uuids_raw = ast.literal_eval(uuids)
            uuids = []
            if isinstance(uuids_raw, (list, tuple)):
                for uuid in uuids_raw:
                    uuids.append(uuid)
            else:
                uuids.append(uuids_raw)
            links = decode_base64(b64_links)
            links = links.split("\n")
            if retry_decrypt(linkids, uuids, links):
                return "Success"
        except:
            pass
        return abort(400, "Failed")

    @app.post(prefix + "/api/myjd_start/")
    @auth_basic(is_authenticated_user)
    def myjd_start():
        try:
            try:
                started = jdownloader_start()
            except (TokenExpiredException, RequestTimeoutException, MYJDException):
                set_device_from_config()
                if not shared_state.get_device():
                    return abort(500, "Failed")
                started = jdownloader_start()
            if started:
                return "Success"
        except:
            pass
        return abort(400, "Failed")

    @app.post(prefix + "/api/myjd_pause/<bl>/")
    @auth_basic(is_authenticated_user)
    def myjd_pause(bl):
        try:
            bl = json.loads(bl)
            try:
                paused = jdownloader_pause(bl)
            except (TokenExpiredException, RequestTimeoutException, MYJDException):
                set_device_from_config()
                if not shared_state.get_device():
                    return abort(500, "Failed")
                paused = jdownloader_pause(bl)
            if paused:
                return "Success"
        except:
            pass
        return abort(400, "Failed")

    @app.post(prefix + "/api/myjd_stop/")
    @auth_basic(is_authenticated_user)
    def myjd_stop():
        try:
            try:
                stopped = jdownloader_stop()
            except (TokenExpiredException, RequestTimeoutException, MYJDException):
                set_device_from_config()
                if not shared_state.get_device():
                    return abort(500, "Failed")
                stopped = jdownloader_stop()
            if stopped:
                return "Success"
        except:
            pass
        return abort(400, "Failed")

    @app.post(prefix + "/api/myjd_update/")
    @auth_basic(is_authenticated_user)
    def myjd_update():
        try:
            try:
                updated = jdownloader_update()
            except (TokenExpiredException, RequestTimeoutException, MYJDException):
                set_device_from_config()
                if not shared_state.get_device():
                    return abort(500, "Failed")
                updated = jdownloader_update()
            if updated:
                return "Success"
        except:
            pass
        return abort(400, "Failed")

    @app.get(prefix + "/api/lists/")
    @auth_basic(is_authenticated_user)
    def get_lists():
        try:
            def get_list(liste):
                cont = ListDb(liste).retrieve()
                return "\n".join(cont) if cont else ""

            return {
                "lists": {
                    "mb": {
                        "filme": get_list('List_ContentAll_Movies'),
                        "regex": get_list('List_ContentAll_Movies_Regex'),
                    },
                    "sj": {
                        "serien": get_list('List_ContentShows_Shows'),
                        "regex": get_list('List_ContentShows_Shows_Regex'),
                        "staffeln_regex": get_list('List_ContentShows_Seasons_Regex'),
                    },
                    "dj": {
                        "dokus": get_list('List_CustomDJ_Documentaries'),
                        "regex": get_list('List_CustomDJ_Documentaries_Regex'),
                    },
                    "dd": {
                        "feeds": get_list('List_CustomDD_Feeds'),
                    },
                    "mbsj": {
                        "staffeln": get_list('List_ContentAll_Seasons'),
                    }
                },
            }
        except:
            return abort(400, "Failed")

    @app.post(prefix + "/api/lists/")
    @auth_basic(is_authenticated_user)
    def post_lists():
        try:
            data = request.json

            mb_filme = keep_alphanumeric_with_special_characters(data['mb']['filme']).split('\n')
            ListDb("List_ContentAll_Movies").store_list(mb_filme)

            mbsj_staffeln = keep_alphanumeric_with_special_characters(data['mbsj']['staffeln']).split('\n')
            ListDb("List_ContentAll_Seasons").store_list(mbsj_staffeln)

            mb_regex = keep_alphanumeric_with_regex_characters(data['mb']['regex']).split('\n')
            ListDb("List_ContentAll_Movies_Regex").store_list(mb_regex)

            sj_serien = keep_alphanumeric_with_special_characters(data['sj']['serien']).split('\n')
            ListDb("List_ContentShows_Shows").store_list(sj_serien)

            sj_regex = keep_alphanumeric_with_regex_characters(data['sj']['regex']).split('\n')
            ListDb("List_ContentShows_Shows_Regex").store_list(sj_regex)

            sj_staffeln_regex = keep_alphanumeric_with_regex_characters(data['sj']['staffeln_regex']).split('\n')
            ListDb("List_ContentShows_Seasons_Regex").store_list(sj_staffeln_regex)

            dj_dokus = keep_alphanumeric_with_special_characters(data['dj']['dokus']).split('\n')
            ListDb("List_CustomDJ_Documentaries").store_list(dj_dokus)

            dj_regex = keep_alphanumeric_with_regex_characters(data['dj']['regex']).split('\n')
            ListDb("List_CustomDJ_Documentaries_Regex").store_list(dj_regex)

            dd_feeds = keep_numbers(data['dd']['feeds']).split('\n')
            ListDb("List_CustomDD_Feeds").store_list(dd_feeds)

            return "Success"
        except:
            return abort(400, "Failed")

    @app.get(prefix + "/sponsors_helper/api/to_decrypt/")
    def to_decrypt_api():
        global helper_active
        try:
            helper_active = True
            decrypt_name = False
            decrypt_url = False
            decrypt_password = False
            decrypt = get_to_decrypt()
            if decrypt:
                decrypt = decrypt[0]
                decrypt_name = decrypt["name"]
                decrypt_url = decrypt["url"].replace("http://", "https://") + "#" + decrypt_name + "|" + decrypt[
                    "password"]
                decrypt_password = decrypt["password"]

            try:
                max_attempts = CrawlerConfig('SponsorsHelper').get("max_attempts")
            except:
                max_attempts = 3

            return {
                "to_decrypt": {
                    "name": decrypt_name,
                    "url": decrypt_url,
                    "password": decrypt_password,
                    "max_attempts": max_attempts
                }
            }
        except:
            return abort(400, "Failed")

    @app.post(prefix + "/sponsors_helper/api/to_decrypt_disable/<name>")
    def to_decrypt_disable(name):
        try:
            if name:
                name.encode("ascii", errors="ignore").decode().replace("/", "").replace(" ", ".")
                max_attempts = str(CrawlerConfig('SponsorsHelper').get("max_attempts"))
                if disable_decrypt(name):
                    try:
                        notify([{
                            "text": "[CAPTCHA nicht gelöst] - " + name + " (Paket nach " + max_attempts + " Versuchen deaktiviert)"}])
                    except:
                        print("Benachrichtigung konnte nicht versendet werden!")
                    print(
                        "[CAPTCHA nicht gelöst] - " + name + " (Paket nach " + max_attempts + " Versuchen deaktiviert)")
                    return "<script type='text/javascript'>" \
                           "function closeWindow(){window.close()}window.onload=closeWindow;</script>" \
                           "[CAPTCHA nicht gelöst] - " + name + " (Paket nach " + max_attempts + " Versuchen deaktiviert)"
        except:
            pass
        return abort(400, "Failed")

    @app.put(prefix + "/sponsors_helper/api/activate_sponsor_status/")
    def activate_sponsor_status():
        global helper_active
        try:
            data = request.body.read().decode("utf-8")
            payload = json.loads(data)
            if payload["activate"]:
                helper_active = True
                return "Sponsor status activated successfully!"
        except:
            pass
        return abort(400, "Failed")

    def get_filer_folder_links(url):
        try:
            content = get_url(url)
            links = []
            if content:
                soup = BeautifulSoup(content, 'html.parser')
                folder_links = soup.find_all('a', href=re.compile("/get/"))
                for link in folder_links:
                    link = "https://filer.net" + link.get('href')
                    if link not in links:
                        links.append(link)
            if links:
                return links
        except:
            pass
        return url

    def clean_links(links):
        try:
            if len(links) == 1 and "filer.net/folder/" in links[0]:
                links = get_filer_folder_links(links[0])
            elif type(links) is str and "filer.net/folder/" in links:
                if links.startswith("['") and links.endswith("']"):
                    links = links.split("'")[1]
                elif links.startswith('["') and links.endswith('"]'):
                    links = links.split('"')[1]
                links = get_filer_folder_links(links)
        except:
            pass
        return links

    @app.get(prefix + "/sponsors_helper/replace_decrypt/<payload>")
    def replace_decrypt(payload):
        try:
            payload = decode_base64(payload.replace("%3D", "=")).split("|")
        except:
            return abort(400, "Failed")
        if payload:
            links = clean_links(payload[0])

            package_name = payload[1].replace("%20", "") \
                .encode("ascii", errors="ignore").decode().replace("/", "").replace(" ", ".")

            try:
                password = payload[2]
            except:
                password = ""

            result = add_decrypt_instead_of_download(package_name, 'unused', [links], password, replace=True)
            if result:
                return "<script type='text/javascript'>" \
                       "function closeWindow(){window.close()}window.onload=closeWindow;</script>" \
                       "[Link ersetzt] - " + package_name
        return abort(400, "Failed")

    def attempt_download(package_name, links, password, ids):
        global already_added

        FeedDb('crawldog').store(package_name, 'added')
        if shared_state.get_device():
            if ids:
                try:
                    ids = ids.replace("%20", "").split(";")
                    linkids = ids[0]
                    uuids = ids[1]
                except:
                    linkids = False
                    uuids = False
                if ids and uuids:
                    linkids_raw = ast.literal_eval(linkids)
                    linkids = []
                    if isinstance(linkids_raw, (list, tuple)):
                        for linkid in linkids_raw:
                            linkids.append(linkid)
                    else:
                        linkids.append(linkids_raw)
                    uuids_raw = ast.literal_eval(uuids)
                    uuids = []
                    if isinstance(uuids_raw, (list, tuple)):
                        for uuid in uuids_raw:
                            uuids.append(uuid)
                    else:
                        uuids.append(uuids_raw)

                    remove_from_linkgrabber(linkids, uuids)
                    remove_decrypt(package_name)
                    remove_decrypt(package_name, disabled=True)
            else:
                is_episode = re.findall(r'.*\.(S\d{1,3}E\d{1,3})\..*', package_name)
                if not is_episode:
                    re_name = rreplace(package_name.lower(), "-", ".*", 1)
                    re_name = re_name.replace(".untouched", ".*").replace("dd+51", "dd.51")
                    season_string = re.findall(r'.*(s\d{1,3}).*', re_name)
                    if season_string:
                        re_name = re_name.replace(season_string[0], season_string[0] + '.*')
                    codec_tags = [".h264", ".x264", ".x265", ".h265", ".hevc", ".h.264", ".h.265"]
                    for tag in codec_tags:
                        re_name = re_name.replace(tag, ".*264")
                    web_tags = [".web-rip", ".webrip", ".webdl", ".web-dl"]
                    for tag in web_tags:
                        re_name = re_name.replace(tag, ".web.*")
                    multigroup = re.findall(r'.*-((.*)/(.*))', package_name.lower())
                    if multigroup:
                        re_name = re_name.replace(multigroup[0][0],
                                                  '(' + multigroup[0][1] + '|' + multigroup[0][2] + ')')
                else:
                    re_name = package_name
                    season_string = re.findall(r'.*(s\d{1,3}).*', re_name.lower())

                if season_string:
                    season_string = season_string[0].replace("s", "S")
                else:
                    season_string = "^unmatchable$"
                try:
                    packages = get_packages_in_linkgrabber()
                except (TokenExpiredException, RequestTimeoutException, MYJDException):
                    set_device_from_config()
                    if not shared_state.get_device():
                        return abort(500, "Failed")
                    packages = get_packages_in_linkgrabber()

                if packages:
                    failed = packages[0]
                    offline = packages[1]

                    def check_if_broken(check_packages):
                        if check_packages:
                            for check_package in check_packages:
                                if re.match(re.compile(re_name), check_package['name'].lower()):
                                    episode = re.findall(r'.*\.S\d{1,3}E(\d{1,3})\..*',
                                                         check_package['name'])
                                    if episode:
                                        FeedDb('episode_remover').store(package_name,
                                                                        str(int(episode[0])))
                                    linkids = check_package['linkids']
                                    uuids = [check_package['uuid']]
                                    remove_from_linkgrabber(linkids, uuids)
                                    remove_decrypt(package_name)
                                    remove_decrypt(package_name, disabled=True)
                                    return "<script type='text/javascript'>" \
                                           "function closeWindow(){window.close()}window.onload=closeWindow;</script>" \
                                           "[CAPTCHA gelöst] - " + package_name

                    try:
                        check_if_broken(failed)
                        check_if_broken(offline)
                    except:
                        pass

                packages = get_to_decrypt()
                if packages:
                    for package in packages:
                        if package_name == package["name"].strip():
                            package_name = package["name"]
                        elif re.match(re.compile(re_name),
                                      package['name'].lower().strip().replace(".untouched",
                                                                              ".*").replace(
                                          "dd+51",
                                          "dd.51")):
                            episode = re.findall(r'.*\.S\d{1,3}E(\d{1,3})\..*', package['name'])
                            remove_decrypt(package['name'])
                            remove_decrypt(package['name'], disabled=True)
                            if episode:
                                episode_to_keep = str(int(episode[0]))
                                episode = str(episode[0])
                                if len(episode) == 1:
                                    episode = "0" + episode
                                package_name = package_name.replace(season_string + ".",
                                                                    season_string + "E" + episode + ".")
                                episode_in_remover = FeedDb('episode_remover').retrieve(package_name)
                                if episode_in_remover:
                                    episode_to_keep = episode_in_remover + "|" + episode_to_keep
                                    FeedDb('episode_remover').delete(package_name)
                                    time.sleep(1)
                                FeedDb('episode_remover').store(package_name, episode_to_keep)
                                break
                time.sleep(1)
                remove_decrypt(package_name)
                remove_decrypt(package_name, disabled=True)
            try:
                epoch = int(time.time())
                for item in already_added:
                    if item[0] == package_name:
                        if int(item[1]) + 5 > epoch:
                            print(package_name + " wurde in den letzten 5 Sekunden bereits hinzugefügt")
                            return abort(500, package_name + " wurde in den letzten 5 Sekunden bereits hinzugefügt")
                        else:
                            already_added.remove(item)

                download(package_name, "FeedCrawler", links, password)
                db = FeedDb('FeedCrawler')
                if not db.retrieve(package_name):
                    db.store(package_name, 'added')
                try:
                    notify([{"text": "[CAPTCHA gelöst] - " + package_name}])
                except:
                    print("Benachrichtigung konnte nicht versendet werden!")
                print("[CAPTCHA gelöst] - " + package_name)
                already_added.append([package_name, str(epoch)])
                return "<script type='text/javascript'>" \
                       "function closeWindow(){window.close()}window.onload=closeWindow;</script>" \
                       "[CAPTCHA gelöst] - " + package_name
            except:
                print(package_name + " konnte nicht hinzugefügt werden!")
                return abort(500, package_name + " konnte nicht hinzugefügt werden!")

    @app.get(prefix + "/sponsors_helper/to_download/<payload>")
    def to_download(payload):
        try:
            payload = decode_base64(payload.replace("%3D", "=")).split("|")
        except:
            return abort(400, f"Failed to decode payload: {payload}")
        if payload:
            links = clean_links(payload[0])

            package_name = payload[1].replace("%20", "") \
                .encode("ascii", errors="ignore").decode().replace("/", "").replace(" ", ".")

            try:
                password = payload[2]
            except:
                password = ""
            try:
                ids = payload[3]
            except:
                ids = False

            result = attempt_download(package_name, links, password, ids)
            return result
        return abort(400, "Request was missing payload")

    @app.post(prefix + "/sponsors_helper/to_download/")
    def to_download():
        try:
            data = request.body.read().decode("utf-8")
        except:
            abort(400, "Could not get data from request body")
        try:
            payload = json.loads(data)
        except:
            abort(400, "Could not decode payload from request data")

        try:
            package_name = payload["package_name"] \
                .encode("ascii", errors="ignore").decode().replace("/", "").replace(" ", ".")
            links = clean_links(payload["links"])
        except:
            abort(400, f"Request payload missing package_name or links: {payload}")

        try:
            password = payload["password"]
        except:
            password = ""

        try:
            ids = payload["ids"]
        except:
            ids = False

        try:
            result = attempt_download(package_name, links, password, ids)
            return result
        except:
            abort(400, f"Download attempt failed for payload: {payload}")
        return abort(400, "Request failed for unknown reason")

    obfuscated_captcha_url = decode_base64('aHR0cHM6Ly92Mi5jdXRjYXB0Y2hhLm5ldA==')

    @app.post(prefix + "/api/captcha_token/")
    def captcha_token():
        try:
            data = request.body.read().decode("utf-8")
        except:
            abort(400, "Could not get data from request body")
        try:
            payload = json.loads(data)
            token = payload["token"]
            title = payload["title"]
            link = clean_links(payload["link"])
            password = payload["password"]
            decrypted_links = get_filecrypt_links(shared_state, token, title, link, password)
            success = len(decrypted_links) > 0
            if success:
                if attempt_download(title, decrypted_links, password, []):
                    return f"CAPTCHA solved successfully! Decrypted {decrypted_links} links for {title}"
                else:
                    abort(400, f"Starting Download failed for {title} using {decrypted_links} links.")
            abort(400, f"CAPTCHA solving failed for {title} using token {token}.")
        except:
            abort(400, f"CAPTCHA solving failed for payload: {payload}")

    @app.post(prefix + '/captcha/<captcha_id>.html')
    def proxy(captcha_id):
        target_url = f"{obfuscated_captcha_url}/captcha/{captcha_id}.html"

        headers = {key: value for key, value in request.headers.items() if key != 'Host'}
        data = request.body.read()
        resp = internal_request(target_url, method='POST', headers=headers, data=data.decode("utf-8"))

        content = resp.text
        content = re.sub(r'<script src="/(.*?)"></script>',
                         f'<script src="{obfuscated_captcha_url}/\\1"></script>', content)
        response.content_type = 'text/html'
        return content

    @app.post(prefix + '/captcha/<captcha_id>.json')
    def specific_proxy(captcha_id):
        target_url = f"{obfuscated_captcha_url}/captcha/{captcha_id}.json"

        headers = {key: value for key, value in request.headers.items() if key != 'Host'}
        data = request.body.read()
        resp = internal_request(target_url, method='POST', headers=headers, data=data.decode("utf-8"))

        response.content_type = "application/json; charset=utf-8"
        return resp.content

    @app.get(prefix + '/captcha/<captcha_id>/<uuid>/<filename>')
    def captcha_proxy(captcha_id, uuid, filename):
        new_url = f"{obfuscated_captcha_url}/captcha/{captcha_id}/{uuid}/{filename}"

        try:
            external_response = internal_request(new_url, method="GET")

            if external_response.status_code >= 400:
                raise Exception(
                    f"Request failed with status code {external_response.status_code}: {external_response.text}")

            response.content_type = 'image/png'
            response.headers['Content-Disposition'] = f'inline; filename="{filename}"'

            def generate_chunks(chunk_size=8192):
                content = external_response.content
                for i in range(0, len(content), chunk_size):
                    yield content[i:i + chunk_size]

            return generate_chunks()

        except Exception as e:
            response.status = 502
            return f"Error fetching resource: {e}"

    @app.post(prefix + '/captcha/<captcha_id>/check')
    def captcha_check_proxy(captcha_id):
        new_url = f"{obfuscated_captcha_url}/captcha/{captcha_id}/check"
        headers = {key: value for key, value in request.headers.items()}

        data = request.body.read()
        resp = internal_request(new_url, method='POST', headers=headers, data=data.decode("utf-8"))

        response.status = resp.status_code
        for header in resp.headers:
            if header.lower() not in ['content-encoding', 'transfer-encoding', 'content-length', 'connection']:
                response.set_header(header, resp.headers[header])
        return resp.text

    Server(app, listen='0.0.0.0', port=shared_state.values["port"]).serve_forever()
