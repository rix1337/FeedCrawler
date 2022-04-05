# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt den Webserver und sämtliche APIs des FeedCrawlers bereit.

import ast
import json
import os
import re
import sys
import time
from functools import wraps

from flask import Flask, request, redirect, render_template, send_from_directory, jsonify, Response
from passlib.hash import pbkdf2_sha256
from requests.packages.urllib3 import disable_warnings as disable_request_warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from waitress import serve

import feedcrawler.myjdapi
import feedcrawler.search.shared.content_all
import feedcrawler.search.shared.content_shows
from feedcrawler import internal
from feedcrawler import version
from feedcrawler.common import Unbuffered
from feedcrawler.common import decode_base64
from feedcrawler.common import get_to_decrypt
from feedcrawler.common import is_device
from feedcrawler.common import remove_decrypt
from feedcrawler.common import rreplace
from feedcrawler.config import CrawlerConfig
from feedcrawler.db import FeedDb
from feedcrawler.db import ListDb
from feedcrawler.myjd import check_device
from feedcrawler.myjd import do_add_decrypted
from feedcrawler.myjd import download
from feedcrawler.myjd import get_device
from feedcrawler.myjd import get_if_one_device
from feedcrawler.myjd import get_info
from feedcrawler.myjd import get_packages_in_linkgrabber
from feedcrawler.myjd import get_state
from feedcrawler.myjd import jdownloader_pause
from feedcrawler.myjd import jdownloader_start
from feedcrawler.myjd import jdownloader_stop
from feedcrawler.myjd import move_to_downloads
from feedcrawler.myjd import remove_from_linkgrabber
from feedcrawler.myjd import reset_in_downloads
from feedcrawler.myjd import retry_decrypt
from feedcrawler.notifiers import notify
from feedcrawler.search import search

helper_active = False
already_added = []


def app_container():
    global helper_active
    global already_added

    base_dir = '.'
    if getattr(sys, 'frozen', False):
        base_dir = os.path.join(sys._MEIPASS)

    general = CrawlerConfig('FeedCrawler')
    if general.get("prefix"):
        prefix = '/' + general.get("prefix")
    else:
        prefix = ""

    def requires_auth(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            config = CrawlerConfig('FeedCrawler')
            if config.get("auth_user") and config.get("auth_hash"):
                auth = request.authorization
                if not auth or not check_auth(config, auth.username, auth.password):
                    return authenticate()
            return f(*args, **kwargs)

        return decorated

    app = Flask(__name__, template_folder=os.path.join(base_dir, 'web/dist'))

    @app.route(prefix + '/', defaults={'path': ''}, methods=['GET'])
    @app.route(prefix + '/<path:path>')
    @requires_auth
    def catch_all(path):
        return render_template('index.html')

    if prefix:
        @app.route('/')
        @requires_auth
        def index_prefix():
            return redirect(prefix)

    @app.route(prefix + '/assets/<path:path>')
    def static_files(path):
        return send_from_directory(os.path.join(base_dir, 'web/dist/assets'), path)

    @app.route(prefix + '/favicon.ico', methods=['GET'])
    def static_favicon():
        return send_from_directory(os.path.join(base_dir, 'web/dist'), 'favicon.ico')

    @app.route(prefix + '/sponsors_helper/assets/<path:path>')
    def static_files_helper(path):
        return send_from_directory(os.path.join(base_dir, 'web/dist/assets'), path)

    @app.route(prefix + '/sponsors_helper/favicon.ico', methods=['GET'])
    def static_favicon_helper():
        return send_from_directory(os.path.join(base_dir, 'web/dist'), 'favicon.ico')

    def check_auth(config, username, password):
        auth_hash = config.get("auth_hash")
        if auth_hash and "$pbkdf2-sha256" not in auth_hash:
            auth_hash = pbkdf2_sha256.hash(auth_hash)
            config.save(
                "auth_hash", to_str(auth_hash))
        return username == config.get("auth_user") and pbkdf2_sha256.verify(password, auth_hash)

    def authenticate():
        return Response(
            '''<html>
                <head><title>401 Authorization Required</title></head>
                <body bgcolor="white">
                <center><h1>401 Authorization Required</h1></center>
                <hr><center>FeedCrawler</center>
                </body>
                </html>
                ''', 401,
            {'WWW-Authenticate': 'Basic realm="FeedCrawler"'})

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

    @app.route(prefix + "/api/log/", methods=['GET', 'DELETE'])
    @requires_auth
    def get_delete_log():
        if request.method == 'GET':
            try:
                log = []
                if os.path.isfile(internal.log_file):
                    logfile = open(internal.log_file)
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
                return jsonify(
                    {
                        "log": log,
                    }
                )
            except:
                return "Failed", 400
        elif request.method == 'DELETE':
            try:
                open(internal.log_file, 'w').close()
                return "Success", 200
            except:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/log_entry/<b64_entry>", methods=['DELETE'])
    @requires_auth
    def get_delete_log_entry(b64_entry):
        if request.method == 'DELETE':
            try:
                entry = decode_base64(b64_entry)
                log = []
                if os.path.isfile(internal.log_file):
                    logfile = open(internal.log_file)
                    for line in reversed(logfile.readlines()):
                        if line and line != "\n":
                            if entry not in line:
                                log.append(line)
                    log = "".join(reversed(log))
                    with open(internal.log_file, 'w') as file:
                        file.write(log)
                return "Success", 200
            except:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/settings/", methods=['GET', 'POST'])
    @requires_auth
    def get_post_settings():
        if request.method == 'GET':
            try:
                general_conf = CrawlerConfig('FeedCrawler')
                hosters = CrawlerConfig('Hosters')
                alerts = CrawlerConfig('Notifications')
                ombi = CrawlerConfig('Ombi')
                crawljobs = CrawlerConfig('Crawljobs')
                mb_conf = CrawlerConfig('ContentAll')
                sj_conf = CrawlerConfig('ContentShows')
                dj_conf = CrawlerConfig('CustomDJ')
                f_conf = CrawlerConfig('CustomF')
                return jsonify(
                    {
                        "settings": {
                            "general": {
                                "auth_user": general_conf.get("auth_user"),
                                "auth_hash": general_conf.get("auth_hash"),
                                "myjd_user": general_conf.get("myjd_user"),
                                "myjd_pass": general_conf.get("myjd_pass"),
                                "myjd_device": general_conf.get("myjd_device"),
                                "port": to_int(general_conf.get("port")),
                                "prefix": general_conf.get("prefix"),
                                "interval": to_int(general_conf.get("interval")),
                                "flaresolverr": general_conf.get("flaresolverr"),
                                "flaresolverr_proxy": general_conf.get("flaresolverr_proxy"),
                                "english": general_conf.get("english"),
                                "surround": general_conf.get("surround"),
                                "one_mirror_policy": general_conf.get("one_mirror_policy"),
                                "packages_per_myjd_page": to_int(general_conf.get("packages_per_myjd_page")),
                            },
                            "hosters": {
                                "rapidgator": hosters.get("rapidgator"),
                                "turbobit": hosters.get("turbobit"),
                                "uploaded": hosters.get("uploaded"),
                                "zippyshare": hosters.get("zippyshare"),
                                "oboom": hosters.get("oboom"),
                                "ddl": hosters.get("ddl"),
                                "filefactory": hosters.get("filefactory"),
                                "uptobox": hosters.get("uptobox"),
                                "onefichier": hosters.get("1fichier"),
                                "filer": hosters.get("filer"),
                                "nitroflare": hosters.get("nitroflare"),
                                "ironfiles": hosters.get("ironfiles"),
                                "k2s": hosters.get("k2s"),
                            },
                            "alerts": {
                                "pushbullet": alerts.get("pushbullet"),
                                "pushover": alerts.get("pushover"),
                                "homeassistant": alerts.get("homeassistant"),
                                "telegram": alerts.get("telegram"),
                            },
                            "ombi": {
                                "url": ombi.get("url"),
                                "api": ombi.get("api"),
                            },
                            "crawljobs": {
                                "autostart": crawljobs.get("autostart"),
                                "subdir": crawljobs.get("subdir"),
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
                            "f": {
                                "interval": to_int(f_conf.get("interval")),
                                "search": to_int(f_conf.get("search"))
                            }
                        }
                    }
                )
            except:
                return "Failed", 400
        if request.method == 'POST':
            try:
                data = request.json

                section = CrawlerConfig("FeedCrawler")

                section.save(
                    "auth_user", to_str(data['general']['auth_user']))

                auth_hash = data['general']['auth_hash']
                if auth_hash and "$pbkdf2-sha256" not in auth_hash:
                    auth_hash = pbkdf2_sha256.hash(auth_hash)
                section.save(
                    "auth_hash", to_str(auth_hash))

                myjd_user = to_str(data['general']['myjd_user'])
                myjd_pass = to_str(data['general']['myjd_pass'])
                myjd_device = to_str(data['general']['myjd_device'])

                if myjd_user and myjd_pass and not myjd_device:
                    myjd_device = get_if_one_device(myjd_user, myjd_pass)
                    if myjd_device:
                        print(u"Gerätename " + myjd_device + " automatisch ermittelt.")

                if myjd_user and myjd_pass and myjd_device:
                    device_check = check_device(myjd_user, myjd_pass, myjd_device)
                    if not device_check:
                        myjd_device = get_if_one_device(myjd_user, myjd_pass)
                        if myjd_device:
                            print(u"Gerätename " + myjd_device + " automatisch ermittelt.")
                        else:
                            print(u"Fehlerhafte My JDownloader Zugangsdaten. Bitte vor dem Speichern prüfen!")
                            return "Failed", 400

                section.save("myjd_user", myjd_user)
                section.save("myjd_pass", myjd_pass)
                section.save("myjd_device", myjd_device)
                section.save("port", to_str(data['general']['port']))
                section.save("prefix", to_str(data['general']['prefix']).lower())
                interval = to_str(data['general']['interval'])
                if to_int(interval) < 5:
                    interval = '5'
                section.save("interval", interval)
                section.save("flaresolverr", to_str(data['general']['flaresolverr']))
                section.save("flaresolverr_proxy", to_str(data['general']['flaresolverr_proxy']))
                section.save("english", to_str(data['general']['english']))
                section.save("surround", to_str(data['general']['surround']))
                section.save("one_mirror_policy", to_str(data['general']['one_mirror_policy']))
                section.save("packages_per_myjd_page", to_str(data['general']['packages_per_myjd_page']))

                section = CrawlerConfig("Crawljobs")

                section.save("autostart", to_str(data['crawljobs']['autostart']))
                section.save("subdir", to_str(data['crawljobs']['subdir']))

                section = CrawlerConfig("Notifications")

                section.save("pushbullet", to_str(data['alerts']['pushbullet']))
                section.save("pushover", to_str(data['alerts']['pushover']))
                section.save("telegram", to_str(data['alerts']['telegram']))
                section.save("homeassistant", to_str(data['alerts']['homeassistant']))

                section = CrawlerConfig("Hosters")

                section.save("rapidgator", to_str(data['hosters']['rapidgator']))
                section.save("turbobit", to_str(data['hosters']['turbobit']))
                section.save("uploaded", to_str(data['hosters']['uploaded']))
                section.save("zippyshare", to_str(data['hosters']['zippyshare']))
                section.save("oboom", to_str(data['hosters']['oboom']))
                section.save("ddl", to_str(data['hosters']['ddl']))
                section.save("filefactory", to_str(data['hosters']['filefactory']))
                section.save("uptobox", to_str(data['hosters']['uptobox']))
                section.save("1fichier", to_str(data['hosters']['onefichier']))
                section.save("filer", to_str(data['hosters']['filer']))
                section.save("nitroflare", to_str(data['hosters']['nitroflare']))
                section.save("ironfiles", to_str(data['hosters']['ironfiles']))
                section.save("k2s", to_str(data['hosters']['k2s']))

                section = CrawlerConfig("Ombi")

                section.save("url", to_str(data['ombi']['url']))
                section.save("api", to_str(data['ombi']['api']))

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

                section = CrawlerConfig("CustomF")

                interval = to_str(data['f']['interval'])
                if to_int(interval) < 6:
                    interval = '6'
                section.save("interval", interval)

                search_depth = to_str(data['f']['search'])
                if to_int(search_depth) > 7:
                    search_depth = '7'
                section.save("search", search_depth)

                return "Success", 201
            except:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/version/", methods=['GET'])
    @requires_auth
    def get_version():
        if request.method == 'GET':
            try:
                ver = "v." + version.get_version()
                if version.update_check()[0]:
                    updateready = True
                    updateversion = version.update_check()[1]
                    print(u'Update steht bereit (' + updateversion +
                          ')! Weitere Informationen unter https://github.com/rix1337/FeedCrawler/releases/latest')
                else:
                    updateready = False
                return jsonify(
                    {
                        "version": {
                            "ver": ver,
                            "update_ready": updateready,
                            "docker": internal.docker,
                            "helper_active": helper_active
                        }
                    }
                )
            except:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/crawltimes/", methods=['GET'])
    @requires_auth
    def get_crawltimes():
        if request.method == 'GET':
            try:
                crawltimes = FeedDb("crawltimes")
                next_f_run = False
                try:
                    last_f_run = to_float(FeedDb('crawltimes').retrieve("last_f_run"))
                    f_interval = to_float(CrawlerConfig('CustomF').get("interval"))
                    if last_f_run:
                        next_f_run = last_f_run + 1000 * f_interval * 60 * 60
                except:
                    pass
                return jsonify(
                    {
                        "crawltimes": {
                            "active": to_bool(crawltimes.retrieve("active")),
                            "start_time": to_float(crawltimes.retrieve("start_time")),
                            "end_time": to_float(crawltimes.retrieve("end_time")),
                            "total_time": crawltimes.retrieve("total_time"),
                            "next_start": to_float(crawltimes.retrieve("next_start")),
                            "next_f_run": next_f_run
                        }
                    }
                )
            except:
                time.sleep(3)
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/hostnames/", methods=['GET'])
    @requires_auth
    def get_hostnames():
        if request.method == 'GET':
            try:
                hostnames = CrawlerConfig('Hostnames')
                fx = hostnames.get('fx')
                hw = hostnames.get('hw')
                ff = hostnames.get('ff')
                sj = hostnames.get('sj')
                dj = hostnames.get('dj')
                sf = hostnames.get('sf')
                ww = hostnames.get('ww')
                nk = hostnames.get('nk')
                by = hostnames.get('by')

                fx = fx.replace("f", "F", 1).replace("d", "D", 1).replace("x", "X", 1)
                hw = hw.replace("h", "H", 1).replace("d", "D", 1).replace("w", "W", 1)
                ff = ff.replace("f", "F", 2)
                sj = sj.replace("s", "S", 1).replace("j", "J", 1)
                dj = dj.replace("d", "D", 1).replace("j", "J", 1)
                sf = sf.replace("s", "S", 1).replace("f", "F", 1)
                ww = ww.replace("w", "W", 2)
                nk = nk.replace("n", "N", 1).replace("k", "K", 1)
                by = by.replace("b", "B", 1)
                bl = ' / '.join(list(filter(None, [fx, ff, hw, ww, nk, by])))
                s = ' / '.join(list(filter(None, [sj, sf])))
                f = ' / '.join(list(filter(None, [ff, sf])))
                sjbl = ' / '.join(list(filter(None, [s, bl])))

                if not fx:
                    fx = "Nicht gesetzt!"
                if not hw:
                    hw = "Nicht gesetzt!"
                if not ff:
                    ff = "Nicht gesetzt!"
                if not sj:
                    sj = "Nicht gesetzt!"
                if not dj:
                    dj = "Nicht gesetzt!"
                if not sf:
                    sf = "Nicht gesetzt!"
                if not ww:
                    ww = "Nicht gesetzt!"
                if not nk:
                    nk = "Nicht gesetzt!"
                if not by:
                    by = "Nicht gesetzt!"
                if not bl:
                    bl = "Nicht gesetzt!"
                if not s:
                    s = "Nicht gesetzt!"
                if not f:
                    f = "Nicht gesetzt!"
                if not sjbl:
                    sjbl = "Nicht gesetzt!"
                return jsonify(
                    {
                        "hostnames": {
                            "sj": sj,
                            "dj": dj,
                            "sf": sf,
                            "by": by,
                            "fx": fx,
                            "hw": hw,
                            "ff": ff,
                            "nk": nk,
                            "ww": ww,
                            "bl": bl,
                            "s": s,
                            "f": f,
                            "sjbl": sjbl
                        }
                    }
                )
            except:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/blocked_sites/", methods=['GET'])
    @requires_auth
    def get_blocked_sites():
        if request.method == 'GET':
            try:
                db_status = FeedDb('site_status')
                status = jsonify(
                    {
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
                                "WW": check("WW_normal", db_status)
                            },
                            "flaresolverr": {
                                "SJ": check("SJ_flaresolverr", db_status),
                                "DJ": check("DJ_flaresolverr", db_status),
                                "SF": check("SF_flaresolverr", db_status),
                                "BY": check("BY_flaresolverr", db_status),
                                "FX": check("FX_flaresolverr", db_status),
                                "HW": check("HW_flaresolverr", db_status),
                                "FF": check("FF_flaresolverr", db_status),
                                "NK": check("NK_flaresolverr", db_status),
                                "WW": check("WW_flaresolverr", db_status)
                            },
                            "flaresolverr_proxy": {
                                "SJ": check("SJ_flaresolverr_proxy", db_status),
                                "DJ": check("DJ_flaresolverr_proxy", db_status),
                                "SF": check("SF_flaresolverr_proxy", db_status),
                                "BY": check("BY_flaresolverr_proxy", db_status),
                                "FX": check("FX_flaresolverr_proxy", db_status),
                                "HW": check("HW_flaresolverr_proxy", db_status),
                                "FF": check("FF_flaresolverr_proxy", db_status),
                                "NK": check("NK_flaresolverr_proxy", db_status),
                                "WW": check("WW_flaresolverr_proxy", db_status)
                            }
                        }
                    }
                )
                return status
            except:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/start_now/", methods=['POST'])
    @requires_auth
    def start_now():
        if request.method == 'POST':
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
                    return "Success", 200
                else:
                    return "Failed", 400
            except:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/search/<title>", methods=['POST'])
    @requires_auth
    def search_title(title):
        if request.method == 'POST':
            try:
                if len(title) < 3:
                    return "Search term too short!", 400
                data = json.loads(request.data)
                slow_only = data['slow_only']
                fast_only = data['fast_only']
            except:
                slow_only = False
                fast_only = False
            try:
                results = search.get(title, only_slow=slow_only, only_fast=fast_only)
                return jsonify(
                    {
                        "results": {
                            "bl": results[0],
                            "sj": results[1],
                            "sf": results[2]
                        }
                    }
                ), 200
            except:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/download_movie/<title>", methods=['POST'])
    @requires_auth
    def download_movie(title):
        if request.method == 'POST':
            try:
                payload = feedcrawler.search.shared.content_all.get_best_result(title)
                if payload:
                    matches = feedcrawler.search.shared.content_all.download(payload)
                    return "Success: " + str(matches), 200
            except:
                pass
            return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/download_show/<title>", methods=['POST'])
    @requires_auth
    def download_show(title):
        if request.method == 'POST':
            try:
                payload = feedcrawler.search.shared.content_shows.get_best_result(title)
                if payload:
                    matches = feedcrawler.search.shared.content_shows.download(payload)
                    if matches:
                        return "Success: " + str(matches), 200
            except:
                pass
            return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/download_bl/<payload>", methods=['POST'])
    @requires_auth
    def download_bl(payload):
        if request.method == 'POST':
            try:
                if feedcrawler.search.shared.content_all.download(payload):
                    return "Success", 200
            except:
                pass
            return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/download_s/<payload>", methods=['POST'])
    @requires_auth
    def download_s(payload):
        if request.method == 'POST':
            try:
                if feedcrawler.search.shared.content_shows.download(payload):
                    return "Success", 200
            except:
                pass
            return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/myjd/", methods=['GET'])
    @requires_auth
    def myjd_info():
        if request.method == 'GET':
            try:
                myjd = get_info()
                packages_to_decrypt = get_to_decrypt()
                if myjd:
                    return jsonify(
                        {
                            "downloader_state": myjd[1],
                            "grabber_collecting": myjd[2],
                            "update_ready": myjd[3],
                            "packages": {
                                "downloader": myjd[4][0],
                                "linkgrabber_decrypted": myjd[4][1],
                                "linkgrabber_offline": myjd[4][2],
                                "linkgrabber_failed": myjd[4][3],
                                "to_decrypt": packages_to_decrypt
                            }
                        }
                    ), 200
            except:
                pass
            return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/myjd_state/", methods=['GET'])
    @requires_auth
    def myjd_state():
        if request.method == 'GET':
            try:
                myjd = get_state()
                if myjd:
                    return jsonify(
                        {
                            "downloader_state": myjd[1],
                            "grabber_collecting": myjd[2]
                        }
                    ), 200
            except:
                pass
            return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/myjd_move/<linkids>&<uuids>", methods=['POST'])
    @requires_auth
    def myjd_move(linkids, uuids):
        if request.method == 'POST':
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
                    return "Success", 200
            except:
                pass
            return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/myjd_remove/<linkids>&<uuids>", methods=['POST'])
    @requires_auth
    def myjd_remove(linkids, uuids):
        if request.method == 'POST':
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
                    return "Success", 200
            except:
                pass
            return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/myjd_reset/<linkids>&<uuids>", methods=['POST'])
    @requires_auth
    def myjd_reset(linkids, uuids):
        if request.method == 'POST':
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
                    return "Success", 200
            except:
                pass
            return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/internal_remove/<name>", methods=['POST'])
    @requires_auth
    def internal_remove(name):
        if request.method == 'POST':
            try:
                delete = remove_decrypt(name)
                if delete:
                    return "Success", 200
            except:
                pass
            return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/myjd_retry/<linkids>&<uuids>&<b64_links>", methods=['POST'])
    @requires_auth
    def myjd_retry(linkids, uuids, b64_links):
        if request.method == 'POST':
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
                    return "Success", 200
            except:
                pass
            return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/myjd_start/", methods=['POST'])
    @requires_auth
    def myjd_start():
        if request.method == 'POST':
            try:
                if jdownloader_start():
                    return "Success", 200
            except:
                pass
            return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/myjd_pause/<bl>", methods=['POST'])
    @requires_auth
    def myjd_pause(bl):
        if request.method == 'POST':
            try:
                bl = json.loads(bl)
                if jdownloader_pause(bl):
                    return "Success", 200
            except:
                pass
            return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/myjd_stop/", methods=['POST'])
    @requires_auth
    def myjd_stop():
        if request.method == 'POST':
            try:
                if jdownloader_stop():
                    return "Success", 200
            except:
                pass
            return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/internal_cnl/<name>&<password>", methods=['POST'])
    @requires_auth
    def internal_cnl(name, password):
        if request.method == 'POST':
            try:
                packages = get_info()
                if packages:
                    decrypted_packages = packages[4][1]
                    offline_packages = packages[4][2]
                else:
                    decrypted_packages = False
                    offline_packages = False

                known_packages = []
                if decrypted_packages:
                    for dp in decrypted_packages:
                        known_packages.append(dp['uuid'])
                if offline_packages:
                    for op in offline_packages:
                        known_packages.append(op['uuid'])

                cnl_packages = []
                grabber_was_collecting = False
                i = 12
                while i > 0:
                    i -= 1
                    time.sleep(5)
                    packages = get_info()
                    if packages:
                        grabber_collecting = packages[2]
                        if grabber_was_collecting or grabber_collecting:
                            grabber_was_collecting = grabber_collecting
                            i -= 1
                            time.sleep(5)
                        else:
                            if not grabber_collecting:
                                decrypted_packages = packages[4][1]
                                offline_packages = packages[4][2]
                                if not grabber_collecting and decrypted_packages:
                                    for dp in decrypted_packages:
                                        if dp['uuid'] not in known_packages:
                                            cnl_packages.append(dp)
                                            i = 0
                                if not grabber_collecting and offline_packages:
                                    for op in offline_packages:
                                        if op['uuid'] not in known_packages:
                                            cnl_packages.append(op)
                                            i = 0

                if not cnl_packages:
                    return "No Package added through Click'n'Load in time!", 504

                if do_add_decrypted(name, password, cnl_packages):
                    remove_decrypt(name)
                    return "Success", 200
            except:
                pass
            return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/lists/", methods=['GET', 'POST'])
    @requires_auth
    def get_post_lists():
        if request.method == 'GET':
            try:
                def get_list(liste):
                    cont = ListDb(liste).retrieve()
                    return "\n".join(cont) if cont else ""

                return jsonify(
                    {
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
                            "mbsj": {
                                "staffeln": get_list('List_ContentAll_Seasons'),
                            }
                        },
                    }
                )
            except:
                return "Failed", 400
        if request.method == 'POST':
            try:
                data = request.json
                ListDb("List_ContentAll_Movies").store_list(
                    data['mb']['filme'].split('\n'))
                ListDb("List_ContentAll_Seasons").store_list(
                    data['mbsj']['staffeln'].split('\n'))
                ListDb("List_ContentAll_Movies_Regex").store_list(
                    data['mb']['regex'].split('\n'))
                ListDb("List_ContentShows_Shows").store_list(
                    data['sj']['serien'].split('\n'))
                ListDb("List_ContentShows_Shows_Regex").store_list(
                    data['sj']['regex'].split('\n'))
                ListDb("List_ContentShows_Seasons_Regex").store_list(
                    data['sj']['staffeln_regex'].split('\n'))
                ListDb("List_CustomDJ_Documentaries").store_list(
                    data['dj']['dokus'].split('\n'))
                ListDb("List_CustomDJ_Documentaries_Regex").store_list(
                    data['dj']['regex'].split('\n'))
                return "Success", 201
            except:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/sponsors_helper/feedcrawler_helper_sj.user.js", methods=['GET'])
    @requires_auth
    def feedcrawler_helper_sj():
        if request.method == 'GET':
            try:
                hostnames = CrawlerConfig('Hostnames')
                sj = hostnames.get('sj')
                dj = hostnames.get('dj')
                return """// ==UserScript==
// @name            FeedCrawler Helper (SJ/DJ)
// @author          rix1337
// @description     Forwards decrypted SJ/DJ Download links to FeedCrawler
// @version         0.3.0
// @require         https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js
// @match           https://""" + sj + """/*
// @match           https://""" + dj + """/*
// @exclude         https://""" + sj + """/serie/search?q=*
// @exclude         https://""" + dj + """/serie/search?q=*
// ==/UserScript==

document.body.addEventListener('mousedown', function (e) {
    if (e.target.tagName != "A") return;
    var anchor = e.target;
    if (anchor.href.search(/""" + sj + """\/serie\//i) != -1) {
        anchor.href = anchor.href + '#' + anchor.text;
    } else if (anchor.href.search(/""" + dj + """\/serie\//i) != -1) {
        anchor.href = anchor.href + '#' + anchor.text;
    }
});

var tag = window.location.hash.replace("#", "").split('|');
var title = tag[0];
var password = tag[1];
if (title) {
    $('.wrapper').prepend('<h3>[FeedCrawler Helper] ' + title + '</h3>');
    $(".container").hide();
    var checkExist = setInterval(async function () {
        if ($("tr:contains('" + title + "')").length) {
            $(".container").show();
            $("tr:contains('" + title + "')")[0].lastChild.firstChild.click();
            clearInterval(checkExist);
        }
    }, 100);
}

""", 200
            except:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/sponsors_helper/feedcrawler_sponsors_helper_sj.user.js", methods=['GET'])
    @requires_auth
    def feedcrawler_sponsors_helper_sj():
        if not helper_active:
            return "Forbidden", 403
        if request.method == 'GET':
            try:
                hostnames = CrawlerConfig('Hostnames')
                sj = hostnames.get('sj')
                dj = hostnames.get('dj')
                return """// ==UserScript==
// @name            FeedCrawler Sponsors Helper (SJ/DJ)
// @author          rix1337
// @description     Clicks the correct download button on SJ/DJ sub pages to speed up Click'n'Load
// @version         0.5.2
// @require         https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js
// @match           https://""" + sj + """/*
// @match           https://""" + dj + """/*
// @exclude         https://""" + sj + """/serie/search?q=*
// @exclude         https://""" + dj + """/serie/search?q=*
// @grant           window.close
// ==/UserScript==

// Hier muss die von außen erreichbare Adresse des FeedCrawlers stehen (nicht bspw. die Docker-interne):
const sponsorsURL = '""" + internal.local_address + """';
// Hier kann ein Wunschhoster eingetragen werden (ohne www. und .tld):
const sponsorsHoster = '';

$.extend($.expr[':'], {
  'containsi': function(elem, i, match, array) {
    return (elem.textContent || elem.innerText || '').toLowerCase()
        .indexOf((match[3] || "").toLowerCase()) >= 0;
  }
});

document.body.addEventListener('mousedown', function (e) {
    if (e.target.tagName != "A") return;
    var anchor = e.target;
    if (anchor.href.search(/""" + sj + """\/serie\//i) != -1) {
        anchor.href = anchor.href + '#' + anchor.text;
    } else if (anchor.href.search(/""" + dj + """\/serie\//i) != -1) {
        anchor.href = anchor.href + '#' + anchor.text;
    }
});

const tag = window.location.hash.replace("#", "").split('|');
const title = tag[0];
const password = tag[1];
if (title && title !== "login") {
    $('.wrapper').prepend('<h3>[FeedCrawler Sponsors Helper] ' + title + '</h3>');
    $(".container").hide();
    let i = 0;
    const checkExist = setInterval(function () {
        i++;
        if ($("tr:contains('" + title + "')").length) {
            $(".container").show();
            $("tr:contains('" + title + "')")[0].lastChild.firstChild.click();
            if (i > 24) {
                const requiresLogin = $(".alert-warning").length;
                if (requiresLogin) {
                    console.log("[FeedCrawler Sponsors Helper] Login required for: " + title);
                    clearInterval(checkExist);
                    window.open("https://" + $(location).attr('hostname') + "#login|" + btoa(window.location));
                    window.close();
                }
                clearInterval(checkExist);
            } else {
                console.log("miss")
            }
        }
    }, 100);

	let j = 0;
	let dl = false;
	const dlExists = setInterval(function () {
		j++;
		if ($("tr:contains('Download Part')").length) {
			const items = $("tr:contains('Download Part')").find("a");
			const links = [];
			items.each(function (index) {
				links.push(items[index].href);
			});
			console.log("[FeedCrawler Sponsors Helper] found download links: " + links);
			clearInterval(dlExists);
			window.open(sponsorsURL + '/sponsors_helper/to_download/' + btoa(links + '|' + title + '|' + password));
			window.close();
		} else if (j > 24 && !dl) {
			if (sponsorsHoster && $("button:containsi('" + sponsorsHoster + "')").length) {
				$("button:containsi('" + sponsorsHoster + "')").click();
			} else if ($("button:containsi('1fichier')").length) {
				$("button:containsi('1fichier')").click();
			} else if ($("button:containsi('ddownload')").length) {
				$("button:containsi('ddownload')").click();
			} else if ($("button:containsi('turbo')").length) {
				$("button:containsi('turbo')").click();
			} else if ($("button:containsi('filer')").length) {
				$("button:containsi('filer')").click();
			} else {
				$("div.modal-body").find("button.btn.btn-secondary.btn-block").click();
			}
			console.log("[FeedCrawler Sponsors Helper] Clicked Download button to trigger reCAPTCHA");
			dl = true;
		}
	}, 100);
}
""", 200
            except:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/sponsors_helper/feedcrawler_sponsors_helper_fc.user.js", methods=['GET'])
    @requires_auth
    def feedcrawler_sponsors_helper_fc():
        if not helper_active:
            return "Forbidden", 403
        if request.method == 'GET':
            hostnames = CrawlerConfig('Hostnames')
            fx = hostnames.get('fx')
            sf = hostnames.get('sf')
            try:
                return """// ==UserScript==
// @name            FeedCrawler Sponsors Helper (FC)
// @author          rix1337
// @description     Forwards Click'n'Load to FeedCrawler
// @version         0.7.4
// @match           *.filecrypt.cc/*
// @match           *.filecrypt.co/*
// @match           *.filecrypt.to/*
// @exclude         http://filecrypt.cc/helper.html*
// @exclude         http://filecrypt.co/helper.html*
// @exclude         http://filecrypt.to/helper.html*
// @grant           window.close
// ==/UserScript==

// Hier muss die von außen erreichbare Adresse des FeedCrawlers stehen (nicht bspw. die Docker-interne):
const sponsorsURL = '""" + internal.local_address + """';
// Hier kann ein Wunschhoster eingetragen werden (ohne www. und .tld):
const sponsorsHoster = '';

const tag = window.location.hash.replace("#", "").split('|');
const title = tag[0];
const password = tag[1];
const ids = tag[2];
const urlParams = new URLSearchParams(window.location.search);


function Sleep(milliseconds) {
    return new Promise(resolve => setTimeout(resolve, milliseconds));
}

let pw = "";


let fx = false
try {
    fx = (document.getElementById("customlogo").getAttribute('src') === '/css/custom/f38ed.png')
} catch {
}

const checkPass = setInterval(function () {
	if (document.getElementById("p4assw0rt")) {
		if (password) {
			pw = password;
		} else if (fx) {
			pw = '""" + fx.split('.')[0] + """';
		} else {
			pw = '""" + sf + """';
		}
	} else {
		pw = "";
	}
	clearInterval(checkPass);
}, 100);

const enterPass = setInterval(function () {
	if (pw) {
		console.log("[FeedCrawler Sponsors Helper] entering Password: " + pw);
		try {
			document.getElementById("p4assw0rt").value = pw;
			document.getElementById("p4assw0rt").parentNode.nextElementSibling.click();
		} catch (e) {
			console.log("[FeedCrawler Sponsors Helper] Password set Error: " + e);
		}
		clearInterval(enterPass);
	}
}, 100);

const checkAd = setInterval(function () {
	if (document.querySelector('#cform > div > div > div > div > ul > li:nth-child(2)') !== null) {
		document.querySelector('#cform > div > div > div > div > ul > li:nth-child(2)').style.display = 'none';
		clearInterval(checkAd);
	}
}, 100);

let mirrorsAvailable = false;
try {
	mirrorsAvailable = document.querySelector('.mirror').querySelectorAll("a");
} catch {
}
let cnlAllowed = false;

if (mirrorsAvailable && sponsorsHoster) {
	const currentURL = window.location.href;
	let desiredMirror = "";
	let i;
	for (i = 0; i < mirrorsAvailable.length; i++) {
		if (mirrorsAvailable[i].text.includes(sponsorsHoster)) {
			let ep = "";
			const cur_ep = urlParams.get('episode');
			if (cur_ep) {
				ep = "&episode=" + cur_ep;
			}
			desiredMirror = mirrorsAvailable[i].href + ep + window.location.hash;
		}
	}

	if (desiredMirror) {
		if (!currentURL.toLowerCase().includes(desiredMirror.toLowerCase())) {
			console.log("[FeedCrawler Sponsors Helper] switching to desired Mirror: " + sponsorsHoster);
			window.location = desiredMirror;
		} else {
			console.log("[FeedCrawler Sponsors Helper] already at the desired Mirror: " + sponsorsHoster);
			cnlAllowed = true;
		}
	} else {
		console.log("[FeedCrawler Sponsors Helper] desired Mirror not available: " + sponsorsHoster);
		cnlAllowed = true;
	}
} else {
	cnlAllowed = true;
}


const cnlExists = setInterval(async function () {
	if (cnlAllowed && document.getElementsByClassName("cnlform").length) {
		clearInterval(cnlExists);
		document.getElementById("cnl_btn").click();
		console.log("[FeedCrawler Sponsors Helper] attempting Click'n'Load");
		await Sleep(10000);
		window.close();
	}
}, 100);
""", 200
            except:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/sponsors_helper/api/to_decrypt/", methods=['GET'])
    def to_decrypt_api():
        global helper_active
        if request.method == 'GET':
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

                return jsonify(
                    {
                        "to_decrypt": {
                            "name": decrypt_name,
                            "url": decrypt_url,
                            "password": decrypt_password
                        }
                    }
                )
            except:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/sponsors_helper/api/f_blocked/<payload>", methods=['GET'])
    def f_blocked(payload):
        if request.method == 'GET':
            try:
                payload = to_bool(payload)
                db_status = FeedDb('site_status')
                if payload:
                    db_status.update_store("SF_FF", "Blocked")
                    return "<script type='text/javascript'>" \
                           "function closeWindow(){window.close()}window.onload=closeWindow;</script>" \
                           "Block status saved", 200
                else:
                    hostnames = CrawlerConfig('Hostnames')
                    next_f_run = False
                    try:
                        last_f_run = to_float(FeedDb('crawltimes').retrieve("last_f_run"))
                        f_interval = to_float(CrawlerConfig('CustomF').get("interval"))
                        if last_f_run:
                            next_f_run = last_f_run + 1000 * f_interval * 60 * 60
                    except:
                        pass
                    return jsonify(
                        {
                            "blocked_sites": {
                                "sf_ff": check("SF_FF", db_status),
                                "sf_hostname": hostnames.get('sf'),
                                "ff_hostname": hostnames.get('ff'),
                                "next_f_run": next_f_run
                            }
                        })
            except:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/sponsors_helper/to_download/<payload>", methods=['GET'])
    def to_download(payload):
        if request.method == 'GET':
            try:
                global already_added

                try:
                    payload = decode_base64(payload.replace("%3D", "=")).split("|")
                except:
                    return "Failed", 400
                if payload:
                    links = payload[0]
                    package_name = payload[1].replace("%20", "")
                    name = package_name

                    try:
                        password = payload[2]
                    except:
                        password = ""
                    try:
                        ids = payload[3]
                    except:
                        ids = False

                    FeedDb('crawldog').store(package_name, 'added')
                    if internal.device:
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
                        else:
                            is_episode = re.findall(r'.*\.(S\d{1,3}E\d{1,3})\..*', package_name)
                            if not is_episode:
                                re_name = rreplace(package_name.lower(), "-", ".*", 1)
                                re_name = re_name.replace(".untouched", ".*").replace("dd+51", "dd.51")
                                season_string = re.findall(r'.*(s\d{1,3}).*', re_name)
                                if season_string:
                                    re_name = re_name.replace(season_string[0], season_string[0] + '.*')
                                codec_tags = [".h264", ".x264"]
                                for tag in codec_tags:
                                    re_name = re_name.replace(tag, ".*264")
                                web_tags = [".web-rip", ".webrip", ".webdl", ".web-dl"]
                                for tag in web_tags:
                                    re_name = re_name.replace(tag, ".web.*")
                                multigroup = re.findall(r'.*-((.*)\/(.*))', package_name.lower())
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
                            except feedcrawler.myjdapi.TokenExpiredException:
                                get_device()
                                if not internal.device or not is_device(internal.device):
                                    return "Failed", 500
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
                                                    FeedDb('episode_remover').store(package_name, str(int(episode[0])))
                                                linkids = check_package['linkids']
                                                uuids = [check_package['uuid']]
                                                remove_from_linkgrabber(linkids, uuids)
                                                remove_decrypt(package_name)
                                                return True

                                try:
                                    check_if_broken(failed)
                                    check_if_broken(offline)
                                except:
                                    pass

                            packages = get_to_decrypt()
                            if packages:
                                for package in packages:
                                    if name == package["name"].strip():
                                        name = package["name"]
                                    elif re.match(re.compile(re_name),
                                                  package['name'].lower().strip().replace(".untouched", ".*").replace(
                                                      "dd+51",
                                                      "dd.51")):
                                        episode = re.findall(r'.*\.S\d{1,3}E(\d{1,3})\..*', package['name'])
                                        remove_decrypt(package['name'])
                                        if episode:
                                            episode_to_keep = str(int(episode[0]))
                                            episode = str(episode[0])
                                            if len(episode) == 1:
                                                episode = "0" + episode
                                            name = name.replace(season_string + ".",
                                                                season_string + "E" + episode + ".")
                                            episode_in_remover = FeedDb('episode_remover').retrieve(package_name)
                                            if episode_in_remover:
                                                episode_to_keep = episode_in_remover + "|" + episode_to_keep
                                                FeedDb('episode_remover').delete(package_name)
                                                time.sleep(1)
                                            FeedDb('episode_remover').store(package_name, episode_to_keep)
                                            break
                            time.sleep(1)
                            remove_decrypt(name)
                        try:
                            epoch = int(time.time())
                            for item in already_added:
                                if item[0] == package_name:
                                    if int(item[1]) + 30 > epoch:
                                        print(name + u" wurde in den letzten 30 Sekunden bereits hinzugefügt")
                                        return name + u" wurde in den letzten 30 Sekunden bereits hinzugefügt", 400
                                    else:
                                        already_added.remove(item)

                            download(package_name, "FeedCrawler", links, password)
                            db = FeedDb('FeedCrawler')
                            if not db.retrieve(name):
                                db.store(name, 'added')
                            try:
                                notify(["[FeedCrawler Sponsors Helper erfolgreich] - " + name])
                            except:
                                print(u"Benachrichtigung konnte nicht versendet werden!")
                            print(u"[FeedCrawler Sponsors Helper erfolgreich] - " + name)
                            already_added.append([name, str(epoch)])
                            return "<script type='text/javascript'>" \
                                   "function closeWindow(){window.close()}window.onload=closeWindow;</script>" \
                                   "[FeedCrawler Sponsors Helper erfolgreich] - " + name, 200
                        except:
                            print(name + u" konnte nicht hinzugefügt werden!")
            except:
                pass
            return "Failed", 400
        else:
            return "Failed", 405

    serve(app, host='0.0.0.0', port=internal.port, threads=10, _quiet=True)


def start():
    sys.stdout = Unbuffered(sys.stdout)
    disable_request_warnings(InsecureRequestWarning)

    if version.update_check()[0]:
        updateversion = version.update_check()[1]
        print(u'Update steht bereit (' + updateversion +
              ')! Weitere Informationen unter https://github.com/rix1337/FeedCrawler/releases/latest')

    app_container()


def web_server(global_variables):
    internal.set_globals(global_variables)
    start()
