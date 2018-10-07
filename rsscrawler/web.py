# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337
import six
if six.PY2:
    from StringIO import StringIO
else:
    from io import StringIO
import logging
import os
import re
import sys
from logging import handlers

import gevent
from flask import Flask, request, send_from_directory, render_template, jsonify
from gevent.pywsgi import WSGIServer

from rsscrawler import search
from rsscrawler import version
from rsscrawler.output import CutLog
from rsscrawler.output import Unbuffered
from rsscrawler.rssconfig import RssConfig
from rsscrawler.rssdb import ListDb
from rsscrawler.rssdb import RssDb


def app_container(port, docker, jdpath, configfile, dbfile, log_file, no_logger):
    app = Flask(__name__, template_folder='web')

    general = RssConfig('RSScrawler', configfile)
    if general.get("prefix"):
        prefix = '/' + general.get("prefix")
    else:
        prefix = ""
    
    
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
    def send_html(path):
        return send_from_directory('web', path)

    @app.route(prefix + '/')
    def index():
        return render_template('index.html')

    @app.route(prefix + "/api/all/", methods=['GET'])
    def get_all():
        if request.method == 'GET':
            general = RssConfig('RSScrawler', configfile)
            alerts = RssConfig('Notifications', configfile)
            crawljobs = RssConfig('Crawljobs', configfile)
            mb = RssConfig('MB', configfile)
            sj = RssConfig('SJ', configfile)
            dd = RssConfig('DD', configfile)
            yt = RssConfig('YT', configfile)
            ver = version.getVersion()
            if version.updateCheck()[0]:
                updateready = True
                updateversion = version.updateCheck()[1]
                print('Update steht bereit (' + updateversion +
                      ')! Weitere Informationen unter https://github.com/rix1337/RSScrawler/releases/latest')
            else:
                updateready = False
            log = ''
            if os.path.isfile(log_file):
                logfile = open(os.path.join(log_file))
                output = StringIO()
                for line in reversed(logfile.readlines()):
                    output.write("<p>" + line.replace("\n", "</p>"))
                    log = output.getvalue()
            if not mb.get("crawl3dtype"):
                crawl_3d_type = "hsbs"
            else:
                crawl_3d_type = mb.get("crawl3dtype")
            return jsonify(
                {
                    "version": {
                        "ver": ver,
                        "update_ready": updateready,
                        "docker": docker,
                    },
                    "log": log,
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
                        "mbsj": {
                            "staffeln": get_list('MB_Staffeln'),
                        },
                        "yt": {
                            "kanaele_playlisten": get_list('YT_Channels'),
                        },
                    },
                    "settings": {
                        "general": {
                            "pfad": general.get("jdownloader"),
                            "port": to_int(general.get("port")),
                            "prefix": general.get("prefix"),
                            "interval": to_int(general.get("interval")),
                            "english": general.get("english"),
                            "surround": general.get("surround"),
                            "proxy": general.get("proxy"),
                            "fallback": general.get("fallback"),
                        },
                        "alerts": {
                            "pushbullet": alerts.get("pushbullet"),
                            "pushover": alerts.get("pushover"),
                            "homeassistant": alerts.get("homeassistant"),
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
        else:
            return "Failed", 405

    @app.route(prefix + "/api/log/", methods=['GET', 'DELETE'])
    def get_delete_log():
        if request.method == 'GET':
            log = ''
            if os.path.isfile(log_file):
                logfile = open(os.path.join(log_file))
                output = StringIO()
                for line in reversed(logfile.readlines()):
                    output.write("<p>" + line.replace("\n", "</p>"))
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
    def get_post_settings():
        if request.method == 'GET':
            general = RssConfig('RSScrawler', configfile)
            alerts = RssConfig('Notifications', configfile)
            crawljobs = RssConfig('Crawljobs', configfile)
            mb = RssConfig('MB', configfile)
            sj = RssConfig('SJ', configfile)
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
                            "pfad": general.get("jdownloader"),
                            "port": to_int(general.get("port")),
                            "prefix": general.get("prefix"),
                            "interval": to_int(general.get("interval")),
                            "english": general.get("english"),
                            "surround": general.get("surround"),
                            "proxy": general.get("proxy"),
                            "fallback": general.get("fallback"),
                        },
                        "alerts": {
                            "pushbullet": alerts.get("pushbullet"),
                            "pushover": alerts.get("pushover"),
                            "homeassistant": alerts.get("homeassistant"),
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
            section.save("jdownloader",
                         to_str(data['general']['pfad']))
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
            section = RssConfig("Crawljobs", configfile)
            section.save(
                "autostart", to_str(data['crawljobs']['autostart']))
            section.save("subdir",
                         to_str(data['crawljobs']['subdir']))
            return "Success", 201
        else:
            return "Failed", 405

    @app.route(prefix + "/api/version/", methods=['GET'])
    def get_version():
        if request.method == 'GET':
            ver = version.getVersion()
            if version.updateCheck()[0]:
                updateready = True
                updateversion = version.updateCheck()[1]
                print('Update steht bereit (' + updateversion +
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

    @app.route(prefix + "/api/delete/<title>", methods=['DELETE'])
    def delete_title(title):
        if request.method == 'DELETE':
            db = RssDb(dbfile, 'rsscrawler')
            db.delete(title)
            return "Success", 200
        else:
            return "Failed", 405

    @app.route(prefix + "/api/search/<title>", methods=['GET'])
    def search_title(title):
        if request.method == 'GET':
            results = search.get(title, configfile)
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
    def download_movie(title):
        if request.method == 'POST':
            best_result = search.best_result_mb(title, configfile)
            if best_result and search.mb(best_result, jdpath, configfile):
                return "Success", 200
            else:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/download_show/<title>", methods=['POST'])
    def download_show(title):
        if ";" in title:
            split = title.split(";")
            title = split[0]
            special = split[1]
        else:
            special = None
        if request.method == 'POST':
            best_result = search.best_result_sj(title, configfile)
            if best_result and search.sj(best_result, special, jdpath, configfile):
                return "Success", 200
            else:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/download_mb/<permalink>", methods=['POST'])
    def download_mb(permalink):
        if request.method == 'POST':
            if search.mb(permalink, jdpath, configfile):
                return "Success", 200
            else:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/download_sj/<info>", methods=['POST'])
    def download_sj(info):
        split = info.split(";")
        id = split[0]
        special = split[1]
        if special == "null":
            special = None
        if request.method == 'POST':
            if search.sj(id, special, jdpath, configfile):
                return "Success", 200
            else:
                return "Failed", 400
        else:
            return "Failed", 405

    @app.route(prefix + "/api/lists/", methods=['GET', 'POST'])
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
            ListDb(dbfile, "YT_Channels").store_list(
                data['yt']['kanaele_playlisten'].split('\n'))
            return "Success", 201
        else:
            return "Failed", 405

    def get_list(liste):
        cont = ListDb(dbfile, liste).retrieve()
        return "\n".join(cont) if cont else ""


    http_server = WSGIServer(('0.0.0.0', port), app, log=no_logger)
    http_server.serve_forever()


def start(port, docker, jdpath, configfile, dbfile, log_level, log_file, log_format):
    sys.stdout = Unbuffered(sys.stdout)

    logger = logging.getLogger('')
    logger.setLevel(log_level)

    console = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter(log_format)
    console.setFormatter(CutLog(log_format))
    console.setLevel(log_level)

    logfile = logging.handlers.RotatingFileHandler(log_file)
    logfile.setFormatter(formatter)
    logfile.setLevel(logging.INFO)

    logger.addHandler(logfile)
    logger.addHandler(console)

    if log_level == 10:
        logfile_debug = logging.handlers.RotatingFileHandler(
            log_file.replace("RSScrawler.log", "RSScrawler_DEBUG.log"), maxBytes=100000, backupCount=5)
        logfile_debug.setFormatter(formatter)
        logfile_debug.setLevel(10)
        logger.addHandler(logfile_debug)

    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    no_logger = logging.getLogger("gevent").setLevel(logging.WARNING)
    gevent.hub.Hub.NOT_ERROR = (Exception,)

    if version.updateCheck()[0]:
        updateversion = version.updateCheck()[1]
        print('Update steht bereit (' + updateversion +
              ')! Weitere Informationen unter https://github.com/rix1337/RSScrawler/releases/latest')

    app_container(port, docker, jdpath, configfile, dbfile, log_file, no_logger)
