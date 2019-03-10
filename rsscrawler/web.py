# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import ast
import json
import logging
import os
import re
import sys
import time
from logging import handlers

import gevent
import six
from functools import wraps
from flask import Flask, request, send_from_directory, render_template, jsonify, Response
from passlib.hash import pbkdf2_sha256
from gevent.pywsgi import WSGIServer
from six.moves import StringIO

from rsscrawler import search
from rsscrawler import version
from rsscrawler.common import decode_base64
from rsscrawler.myjd import check_device
from rsscrawler.myjd import check_failed_packages
from rsscrawler.myjd import get_if_one_device
from rsscrawler.myjd import get_info
from rsscrawler.myjd import get_state
from rsscrawler.myjd import jdownloader_pause
from rsscrawler.myjd import jdownloader_start
from rsscrawler.myjd import jdownloader_stop
from rsscrawler.myjd import move_to_downloads
from rsscrawler.myjd import package_merge_check
from rsscrawler.myjd import package_replace
from rsscrawler.myjd import remove_from_linkgrabber
from rsscrawler.myjd import retry_decrypt
from rsscrawler.myjd import update_jdownloader
from rsscrawler.output import Unbuffered
from rsscrawler.rssconfig import RssConfig
from rsscrawler.rssdb import ListDb
from rsscrawler.rssdb import RssDb


def app_container(port, docker, configfile, dbfile, log_file, no_logger, _device):
    global device
    device = _device

    app = Flask(__name__, template_folder='web')

    general = RssConfig('RSScrawler', configfile)
    if general.get("prefix"):
        prefix = '/' + general.get("prefix")
    else:
        prefix = ""

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
                <hr><center>RSScrawler</center>
                </body>
                </html>
                ''', 401,
            {'WWW-Authenticate': 'Basic realm="RSScrawler"'})

    def requires_auth(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            config = RssConfig('RSScrawler', configfile)
            if config.get("auth_user") and config.get("auth_hash"):
                auth = request.authorization
                if not auth or not check_auth(config, auth.username, auth.password):
                    return authenticate()
            return f(*args, **kwargs)

        return decorated

    def to_int(i):
        if six.PY3:
            if isinstance(i, bytes):
                i = i.decode()
        i = i.strip().replace("None", "")
        return int(i) if i else ""

    def to_float(i):
        i = i.strip().replace("None", "")
        return float(i) if i else ""

    def to_str(i):
        return '' if i is None else str(i)

    @app.route(prefix + '/<path:path>')
    @requires_auth
    def send_html(path):
        return send_from_directory('web', path)

    @app.route(prefix + '/')
    @requires_auth
    def index():
        return render_template('index.html')

    @app.route(prefix + "/api/log/", methods=['GET', 'DELETE'])
    @requires_auth
    def get_delete_log():
        if request.method == 'GET':
            log = ''
            if os.path.isfile(log_file):
                logfile = open(log_file)
                output = StringIO()
                for line in reversed(logfile.readlines()):
                    line = re.sub(r' - <a href.*<\/a>', '', line).replace('<b>', '').replace('</b>', '')
                    output.write(line)
                log = output.getvalue()
            return jsonify(
                {
                    "log": log,
                }
            )
        if request.method == 'DELETE':
            open(log_file, 'w').close()
            return "Success", 200
        else:
            return "Failed", 405

    @app.route(prefix + "/api/settings/", methods=['GET', 'POST'])
    @requires_auth
    def get_post_settings():
        if request.method == 'GET':
            general_conf = RssConfig('RSScrawler', configfile)
            alerts = RssConfig('Notifications', configfile)
            ombi = RssConfig('Ombi', configfile)
            crawljobs = RssConfig('Crawljobs', configfile)
            mb = RssConfig('MB', configfile)
            sj = RssConfig('SJ', configfile)
            dj = RssConfig('DJ', configfile)
            dd = RssConfig('DD', configfile)
            yt = RssConfig('YT', configfile)
            if not mb.get("crawl3dtype"):
                crawl_3d_type = "hsbs"
            else:
                crawl_3d_type = mb.get("crawl3dtype")
            return jsonify(
                {
                    "settings": {
                        "general": {
                            "auth_user": general_conf.get("auth_user"),
                            "auth_hash": general_conf.get("auth_hash"),
                            "myjd_user": general_conf.get("myjd_user"),
                            "myjd_pass": general_conf.get("myjd_pass"),
                            "myjd_device": general_conf.get("myjd_device"),
                            "pfad": general_conf.get("jdownloader"),
                            "port": to_int(general_conf.get("port")),
                            "prefix": general_conf.get("prefix"),
                            "interval": to_int(general_conf.get("interval")),
                            "english": general_conf.get("english"),
                            "surround": general_conf.get("surround"),
                            "proxy": general_conf.get("proxy"),
                            "fallback": general_conf.get("fallback"),
                        },
                        "alerts": {
                            "pushbullet": alerts.get("pushbullet"),
                            "pushover": alerts.get("pushover"),
                            "homeassistant": alerts.get("homeassistant"),
                        },
                        "ombi": {
                            "url": ombi.get("url"),
                            "api": ombi.get("api"),
                            "mdb_api": ombi.get("mdb_api"),
                            "tvd_api": ombi.get("tvd_api"),
                            "tvd_user": ombi.get("tvd_user"),
                            "tvd_userkey": ombi.get("tvd_userkey")
                        },
                        "crawljobs": {
                            "autostart": crawljobs.get("autostart"),
                            "subdir": crawljobs.get("subdir"),
                        },
                        "mb": {
                            "hoster": mb.get("hoster"),
                            "quality": mb.get("quality"),
                            "search": mb.get("search"),
                            "ignore": mb.get("ignore"),
                            "regex": mb.get("regex"),
                            "imdb_score": to_float(mb.get("imdb")),
                            "imdb_year": to_int(mb.get("imdbyear")),
                            "force_dl": mb.get("enforcedl"),
                            "cutoff": mb.get("cutoff"),
                            "crawl_3d": mb.get("crawl3d"),
                            "crawl_3d_type": crawl_3d_type,
                        },
                        "sj": {
                            "hoster": sj.get("hoster"),
                            "quality": sj.get("quality"),
                            "ignore": sj.get("rejectlist"),
                            "regex": sj.get("regex"),
                        },
                        "mbsj": {
                            "enabled": mb.get("crawlseasons"),
                            "quality": mb.get("seasonsquality"),
                            "packs": mb.get("seasonpacks"),
                            "source": mb.get("seasonssource"),
                        },
                        "dj": {
                            "hoster": dj.get("hoster"),
                            "quality": dj.get("quality"),
                            "ignore": dj.get("rejectlist"),
                            "regex": dj.get("regex"),
                            "genres": dj.get("genres"),
                        },
                        "dd": {
                            "hoster": dd.get("hoster"),
                            "feeds": dd.get("feeds"),
                        },
                        "yt": {
                            "enabled": yt.get("youtube"),
                            "max": to_int(yt.get("maxvideos")),
                            "ignore": yt.get("ignore"),
                        }
                    }
                }
            )
        if request.method == 'POST':
            data = request.json

            section = RssConfig("RSScrawler", configfile)

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
                jdownloader = ""
                if not device_check:
                    myjd_device = get_if_one_device(myjd_user, myjd_pass)
                    if myjd_device:
                        print(u"Gerätename " + myjd_device + " automatisch ermittelt.")
                    else:
                        print(u"Fehlerhafte My JDownloader Zugangsdaten. Bitte vor dem Speichern prüfen!")
                        return "Failed", 400
            else:
                jdownloader = to_str(data['general']['pfad'])
                if not jdownloader:
                    print(u"Ohne My JDownloader Zugangsdaten oder JDownloader-Pfad funktioniert RSScrawler nicht!")
                    print(u"Bitte vor dem Speichern prüfen")
                    return "Failed", 400
                else:
                    if not os.path.exists(jdownloader + "/folderwatch"):
                        print(
                            u'Der Pfad des JDownloaders enthält nicht das "folderwatch" Unterverzeichnis. Sicher, dass der Pfad stimmt?')
                        return "Failed", 400

            section.save("myjd_user", myjd_user)
            section.save("myjd_pass", myjd_pass)
            section.save("myjd_device", myjd_device)
            section.save("jdownloader", jdownloader)
            section.save(
                "port", to_str(data['general']['port']))
            section.save(
                "prefix", to_str(data['general']['prefix']).lower())
            interval = to_str(data['general']['interval'])
            if to_int(interval) < 5:
                interval = '5'
            section.save("interval", interval)
            section.save("english",
                         to_str(data['general']['english']))
            section.save("surround",
                         to_str(data['general']['surround']))
            section.save("proxy",
                         to_str(data['general']['proxy']))
            section.save("fallback",
                         to_str(data['general']['fallback']))
            section = RssConfig("MB", configfile)
            section.save("hoster",
                         to_str(data['mb']['hoster']))
            section.save("quality",
                         to_str(data['mb']['quality']))
            section.save("search",
                         to_str(data['mb']['search']))
            section.save(
                "ignore", to_str(data['mb']['ignore']).lower())
            section.save("regex",
                         to_str(data['mb']['regex']))
            section.save("cutoff",
                         to_str(data['mb']['cutoff']))
            section.save("crawl3d",
                         to_str(data['mb']['crawl_3d']))
            section.save("crawl3dtype",
                         to_str(data['mb']['crawl_3d_type']))
            section.save("enforcedl",
                         to_str(data['mb']['force_dl']))
            section.save("crawlseasons",
                         to_str(data['mbsj']['enabled']))
            section.save("seasonsquality",
                         to_str(data['mbsj']['quality']))
            section.save("seasonpacks",
                         to_str(data['mbsj']['packs']))
            section.save("seasonssource",
                         to_str(data['mbsj']['source']).lower())
            section.save("imdbyear",
                         to_str(data['mb']['imdb_year']))
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
            section = RssConfig("SJ", configfile)
            section.save("hoster",
                         to_str(data['sj']['hoster']))
            section.save("quality",
                         to_str(data['sj']['quality']))
            section.save("rejectlist",
                         to_str(data['sj']['ignore']).lower())
            section.save("regex",
                         to_str(data['sj']['regex']))
            section = RssConfig("DJ", configfile)
            section.save("hoster",
                         to_str(data['dj']['hoster']))
            section.save("quality",
                         to_str(data['dj']['quality']))
            section.save("rejectlist",
                         to_str(data['dj']['ignore']).lower())
            section.save("regex",
                         to_str(data['dj']['regex']))
            section.save("genres",
                         to_str(data['dj']['genres']))
            section = RssConfig("DD", configfile)
            section.save("hoster",
                         to_str(data['dd']['hoster']))
            section.save("feeds",
                         to_str(data['dd']['feeds']))
            section = RssConfig("YT", configfile)
            section.save("youtube",
                         to_str(data['yt']['enabled']))
            maxvideos = to_str(data['yt']['max'])
            if maxvideos == "":
                maxvideos = "10"
            if to_int(maxvideos) < 1:
                section.save("maxvideos", "1")
            elif to_int(maxvideos) > 50:
                section.save("maxvideos", "50")
            else:
                section.save("maxvideos", to_str(maxvideos))
            section.save("ignore",
                         to_str(data['yt']['ignore']))
            section = RssConfig("Notifications", configfile)
            section.save("pushbullet",
                         to_str(data['alerts']['pushbullet']))
            section.save("pushover",
                         to_str(data['alerts']['pushover']))
            section.save("homeassistant",
                         to_str(data['alerts']['homeassistant']))
            section = RssConfig("Ombi", configfile)
            section.save("url",
                         to_str(data['ombi']['url']))
            section.save("api",
                         to_str(data['ombi']['api']))
            section.save("mdb_api",
                         to_str(data['ombi']['mdb_api']))
            section.save("tvd_api",
                         to_str(data['ombi']['tvd_api']))
            section.save("tvd_user",
                         to_str(data['ombi']['tvd_user']))
            section.save("tvd_userkey",
                         to_str(data['ombi']['tvd_userkey']))
            section = RssConfig("Crawljobs", configfile)
            section.save(
                "autostart", to_str(data['crawljobs']['autostart']))
            section.save("subdir",
                         to_str(data['crawljobs']['subdir']))
            return "Success", 201
        else:
            return "Failed", 405

    @app.route(prefix + "/api/version/", methods=['GET'])
    @requires_auth
    def get_version():
        if request.method == 'GET':
            ver = version.get_version()
            if version.update_check()[0]:
                updateready = True
                updateversion = version.update_check()[1]
                print(u'Update steht bereit (' + updateversion +
                      ')! Weitere Informationen unter https://github.com/rix1337/RSScrawler/releases/latest')
            else:
                updateready = False
            return jsonify(
                {
                    "version": {
                        "ver": ver,
                        "update_ready": updateready,
                        "docker": docker,
                    }
                }
            )
        else:
            return "Failed", 405

    @app.route(prefix + "/api/search/<title>", methods=['GET'])
    @requires_auth
    def search_title(title):
        if request.method == 'GET':
            results = search.get(title, configfile, dbfile)
            return jsonify(
                {
                    "results": {
                        "mb": results[0],
                        "sj": results[1]
                    }
                }
            ), 200
        else:
            return "Failed", 405

    @app.route(prefix + "/api/download_movie/<title>", methods=['POST'])
    @requires_auth
    def download_movie(title):
        global device
        if request.method == 'POST':
            best_result = search.best_result_bl(title, configfile, dbfile)
            if best_result and search.download_bl(best_result, device, configfile, dbfile):
                return "Success", 200
            else:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/download_show/<title>", methods=['POST'])
    @requires_auth
    def download_show(title):
        global device
        if ";" in title:
            split = title.split(";")
            title = split[0]
            special = split[1]
        else:
            special = None
        if request.method == 'POST':
            best_result = search.best_result_sj(title, configfile, dbfile)
            if best_result and search.download_sj(best_result, special, device, configfile, dbfile):
                return "Success", 200
            else:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/download_bl/<permalink>", methods=['POST'])
    @requires_auth
    def download_bl(permalink):
        global device
        if request.method == 'POST':
            if search.download_bl(permalink, device, configfile, dbfile):
                return "Success", 200
            else:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/download_sj/<info>", methods=['POST'])
    @requires_auth
    def download_sj(info):
        global device
        split = info.split(";")
        sj_id = split[0]
        special = split[1]
        if special == "null":
            special = None
        if request.method == 'POST':
            if search.download_sj(sj_id, special, device, configfile, dbfile):
                return "Success", 200
            else:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/myjd/", methods=['GET'])
    @requires_auth
    def myjd_info():
        global device
        if request.method == 'GET':
            myjd = get_info(configfile, device)
            if myjd:
                device = myjd[0]
                return jsonify(
                    {
                        "downloader_state": myjd[1],
                        "grabber_collecting": myjd[2],
                        "update_ready": myjd[3],
                        "packages": {
                            "downloader": myjd[4][0],
                            "linkgrabber_decrypted": myjd[4][1],
                            "linkgrabber_offline": myjd[4][2],
                            "linkgrabber_failed": myjd[4][3]
                        }
                    }
                ), 200
            else:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/myjd_state/", methods=['GET'])
    @requires_auth
    def myjd_state():
        global device
        if request.method == 'GET':
            myjd = get_state(configfile, device)
            if myjd:
                device = myjd[0]
                return jsonify(
                    {
                        "downloader_state": myjd[1],
                        "grabber_collecting": myjd[2]
                    }
                ), 200
            else:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/myjd_move/<linkids>&<uuids>", methods=['POST'])
    @requires_auth
    def myjd_move(linkids, uuids):
        global device
        if request.method == 'POST':
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
            device = move_to_downloads(configfile, device, linkids, uuids)
            if device:
                return "Success", 200
            else:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/myjd_remove/<linkids>&<uuids>", methods=['POST'])
    @requires_auth
    def myjd_remove(linkids, uuids):
        global device
        if request.method == 'POST':
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
            device = remove_from_linkgrabber(configfile, device, linkids, uuids)
            if device:
                # TODO remove from db.failed with title
                return "Success", 200
            else:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/myjd_retry/<linkids>&<uuids>&<b64_links>", methods=['POST'])
    @requires_auth
    def myjd_retry(linkids, uuids, b64_links):
        global device
        if request.method == 'POST':
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
            device = retry_decrypt(configfile, device, linkids, uuids, links)
            if device:
                return "Success", 200
            else:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/myjd_update/", methods=['POST'])
    @requires_auth
    def myjd_update():
        global device
        if request.method == 'POST':
            device = update_jdownloader(configfile, device)
            if device:
                return "Success", 200
            else:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/myjd_start/", methods=['POST'])
    @requires_auth
    def myjd_start():
        global device
        if request.method == 'POST':
            device = jdownloader_start(configfile, device)
            if device:
                return "Success", 200
            else:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/myjd_pause/<bl>", methods=['POST'])
    @requires_auth
    def myjd_pause(bl):
        global device
        bl = json.loads(bl)
        if request.method == 'POST':
            device = jdownloader_pause(configfile, device, bl)
            if device:
                return "Success", 200
            else:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/myjd_stop/", methods=['POST'])
    @requires_auth
    def myjd_stop():
        global device
        if request.method == 'POST':
            device = jdownloader_stop(configfile, device)
            if device:
                return "Success", 200
            else:
                return "Failed", 400
        else:
            return "Failed", 405

    def get_list(liste):
        cont = ListDb(dbfile, liste).retrieve()
        return "\n".join(cont) if cont else ""

    @app.route(prefix + "/api/myjd_cnl/<uuid>", methods=['POST'])
    @requires_auth
    def myjd_cnl(uuid):
        global device
        if request.method == 'POST':
            failed = check_failed_packages(configfile, device)
            if failed:
                device = failed[0]
                decrypted_packages = failed[2]
                failed_packages = failed[4]
            else:
                failed_packages = False
                decrypted_packages = False
            if not failed_packages:
                return "Failed", 500

            title = False
            old_package = False
            if failed_packages:
                for op in failed_packages:
                    if str(op['uuid']) == str(uuid):
                        title = op['name']
                        old_package = op
                        break

            if not old_package or not title:
                return "Failed", 500

            known_packages = []
            if decrypted_packages:
                for dp in decrypted_packages:
                    known_packages.append(dp['uuid'])

            cnl_package = False
            i = 12
            subdir = RssConfig('Crawljobs', configfile).get('subdir')
            while i > 0:
                i -= 1
                time.sleep(5)
                failed = check_failed_packages(configfile, device)
                if failed:
                    device = failed[0]
                    grabber_collecting = failed[1]
                    if not grabber_collecting:
                        decrypted_packages = failed[2]
                        offline_packages = failed[3]
                        another_device = package_merge_check(configfile, device, decrypted_packages, title,
                                                             known_packages)
                        if another_device:
                            device = another_device
                            failed = check_failed_packages(configfile, device)
                            if failed:
                                device = failed[0]
                                grabber_collecting = failed[1]
                                decrypted_packages = failed[2]
                                offline_packages = failed[3]
                        if not grabber_collecting and decrypted_packages:
                            for dp in decrypted_packages:
                                if subdir and 'RSScrawler' in dp['path']:
                                    known_packages.append(dp['uuid'])
                                if dp['uuid'] not in known_packages:
                                    cnl_package = dp
                                    i = 0
                        if not grabber_collecting and offline_packages:
                            for op in offline_packages:
                                if subdir and 'RSScrawler' in op['path']:
                                    known_packages.append(op['uuid'])
                                if op['uuid'] not in known_packages:
                                    cnl_package = op
                                    i = 0

            if not cnl_package:
                return "No Package added through Click'n'Load in time!", 504

            replaced = package_replace(configfile, device, old_package, cnl_package)
            device = replaced[0]
            if device:
                title = replaced[1]
                db = RssDb(dbfile, 'failed')
                db.delete(title)
                return "Success", 200
            else:
                return "Failed", 400
        else:
            return "Failed", 405

    def get_list(liste):
        cont = ListDb(dbfile, liste).retrieve()
        return "\n".join(cont) if cont else ""

    @app.route(prefix + "/api/lists/", methods=['GET', 'POST'])
    @requires_auth
    def get_post_lists():
        if request.method == 'GET':
            return jsonify(
                {
                    "lists": {
                        "mb": {
                            "filme": get_list('MB_Filme'),
                            "filme3d": get_list('MB_3D'),
                            "regex": get_list('MB_Regex'),
                        },
                        "sj": {
                            "serien": get_list('SJ_Serien'),
                            "regex": get_list('SJ_Serien_Regex'),
                            "staffeln_regex": get_list('SJ_Staffeln_Regex'),
                        },
                        "dj": {
                            "dokus": get_list('DJ_Dokus'),
                            "regex": get_list('DJ_Dokus_Regex'),
                        },
                        "mbsj": {
                            "staffeln": get_list('MB_Staffeln'),
                        },
                        "yt": {
                            "kanaele_playlisten": get_list('YT_Channels'),
                        },
                    },
                }
            )
        if request.method == 'POST':
            data = request.json
            ListDb(dbfile, "MB_Filme").store_list(
                data['mb']['filme'].split('\n'))
            ListDb(dbfile, "MB_3D").store_list(
                data['mb']['filme3d'].split('\n'))
            ListDb(dbfile, "MB_Staffeln").store_list(
                data['mbsj']['staffeln'].split('\n'))
            ListDb(dbfile, "MB_Regex").store_list(
                data['mb']['regex'].split('\n'))
            ListDb(dbfile, "SJ_Serien").store_list(
                data['sj']['serien'].split('\n'))
            ListDb(dbfile, "SJ_Serien_Regex").store_list(
                data['sj']['regex'].split('\n'))
            ListDb(dbfile, "SJ_Staffeln_Regex").store_list(
                data['sj']['staffeln_regex'].split('\n'))
            ListDb(dbfile, "DJ_Dokus").store_list(
                data['dj']['dokus'].split('\n'))
            ListDb(dbfile, "DJ_Dokus_Regex").store_list(
                data['dj']['regex'].split('\n'))
            ListDb(dbfile, "YT_Channels").store_list(
                data['yt']['kanaele_playlisten'].split('\n'))
            return "Success", 201
        else:
            return "Failed", 405

    http_server = WSGIServer(('0.0.0.0', port), app, log=no_logger)
    http_server.serve_forever()


def start(port, docker, configfile, dbfile, log_level, log_file, log_format, _device):
    sys.stdout = Unbuffered(sys.stdout)

    logger = logging.getLogger('')
    logger.setLevel(log_level)

    console = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter(log_format)
    console.setLevel(log_level)

    logfile = logging.handlers.RotatingFileHandler(log_file)
    logfile.setFormatter(formatter)
    logfile.setLevel(logging.INFO)

    logger.addHandler(logfile)
    logger.addHandler(console)

    if log_level == 10:
        logfile_debug = logging.handlers.RotatingFileHandler(
            log_file.replace("RSScrawler.log", "RSScrawler_DEBUG.log"))
        logfile_debug.setFormatter(formatter)
        logfile_debug.setLevel(10)
        logger.addHandler(logfile_debug)

    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    no_logger = logging.getLogger("gevent").setLevel(logging.WARNING)
    gevent.hub.Hub.NOT_ERROR = (Exception,)

    if version.update_check()[0]:
        updateversion = version.update_check()[1]
        print(u'Update steht bereit (' + updateversion +
              ')! Weitere Informationen unter https://github.com/rix1337/RSScrawler/releases/latest')

    app_container(port, docker, configfile, dbfile, log_file, no_logger, _device)
