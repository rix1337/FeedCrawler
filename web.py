# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

from flask import Flask, request, send_from_directory, render_template, jsonify

from output import Unbuffered
from output import CutLog
from rssconfig import RssConfig
from rssdb import RssDb
from rssdb import ListDb
import search
import files
import version

import StringIO
import os
import re
import sys
import gevent
from gevent.wsgi import WSGIServer

import logging
from logging import handlers

app = Flask(__name__, static_url_path='/web', template_folder='web')

if not os.path.exists(os.path.join(os.path.dirname(sys.argv[0]), 'RSScrawler.ini')):
    prefix = ""
else:
    general = RssConfig('RSScrawler')
    if general.get("prefix"):
        prefix = '/' + general.get("prefix")
    else:
        prefix = ""


def to_int(i):
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
        general = RssConfig('RSScrawler')
        alerts = RssConfig('Notifications')
        crawljobs = RssConfig('Crawljobs')
        mb = RssConfig('MB')
        sj = RssConfig('SJ')
        dd = RssConfig('DD')
        yt = RssConfig('YT')
        ver = version.getVersion()
        if version.updateCheck()[0]:
            updateready = True
            updateversion = version.updateCheck()[1]
            print('Update steht bereit (' + updateversion +
                  ')! Weitere Informationen unter https://github.com/rix1337/RSScrawler/releases/latest')
        else:
            updateready = False
        log = ''
        logfile = os.path.join(os.path.dirname(sys.argv[0]), 'RSScrawler.log')
        if os.path.isfile(logfile):
            logfile = open(os.path.join(logfile))
            output = StringIO.StringIO()
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
                        "filme": getListe('MB_Filme'),
                        "filme3d": getListe('MB_3D'),
                        "regex": getListe('MB_Regex'),
                    },
                    "sj": {
                        "serien": getListe('SJ_Serien'),
                        "regex": getListe('SJ_Serien_Regex'),
                        "staffeln_regex": getListe('SJ_Staffeln_Regex'),
                    },
                    "mbsj": {
                        "staffeln": getListe('MB_Staffeln'),
                    },
                    "yt": {
                        "kanaele_playlisten": getListe('YT_Channels'),
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
                        "ignore": mb.get("ignore"),
                        "regex": mb.get("regex"),
                        "imdb_score": to_float(mb.get("imdb")),
                        "imdb_year": to_int(mb.get("imdbyear")),
                        "historical": mb.get("historical"),
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
        logfile = os.path.join(os.path.dirname(sys.argv[0]), 'RSScrawler.log')
        if os.path.isfile(logfile):
            logfile = open(os.path.join(logfile))
            output = StringIO.StringIO()
            for line in reversed(logfile.readlines()):
                output.write("<p>" + line.replace("\n", "</p>"))
                log = output.getvalue()
        return jsonify(
            {
                "log": log,
            }
        )
    if request.method == 'DELETE':
        open(os.path.join(os.path.dirname(
            sys.argv[0]), 'RSScrawler.log'), 'w').close()
        return "Success", 200
    else:
        return "Failed", 405


@app.route(prefix + "/api/settings/", methods=['GET', 'POST'])
def get_post_settings():
    if request.method == 'GET':
        general = RssConfig('RSScrawler')
        alerts = RssConfig('Notifications')
        crawljobs = RssConfig('Crawljobs')
        mb = RssConfig('MB')
        sj = RssConfig('SJ')
        dd = RssConfig('DD')
        yt = RssConfig('YT')
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
                        "ignore": mb.get("ignore"),
                        "regex": mb.get("regex"),
                        "imdb_score": to_float(mb.get("imdb")),
                        "imdb_year": to_int(mb.get("imdbyear")),
                        "historical": mb.get("historical"),
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

        section = RssConfig("RSScrawler")
        section.save("jdownloader",
                     to_str(data['general']['pfad']).encode('utf-8'))
        section.save(
            "port", to_str(data['general']['port']).encode('utf-8'))
        section.save(
            "prefix", to_str(data['general']['prefix']).encode('utf-8').lower())
        interval = to_str(data['general']['interval']).encode('utf-8')
        if to_int(interval) < 5:
            interval = '5'
        section.save("interval", interval)
        section.save("english",
                     to_str(data['general']['english']).encode('utf-8'))
        section.save("surround",
                     to_str(data['general']['surround']).encode('utf-8'))
        section.save("proxy",
                     to_str(data['general']['proxy']).encode('utf-8'))
        section.save("fallback",
                     to_str(data['general']['fallback']).encode('utf-8'))
        section = RssConfig("MB")
        section.save("hoster",
                     to_str(data['mb']['hoster']).encode('utf-8'))
        section.save("quality",
                     to_str(data['mb']['quality']).encode('utf-8'))
        section.save(
            "ignore", to_str(data['mb']['ignore']).encode('utf-8').lower())
        section.save("regex",
                     to_str(data['mb']['regex']).encode('utf-8'))
        section.save("cutoff",
                     to_str(data['mb']['cutoff']).encode('utf-8'))
        section.save("crawl3d",
                     to_str(data['mb']['crawl_3d']).encode('utf-8'))
        section.save("crawl3dtype",
                     to_str(data['mb']['crawl_3d_type']).encode('utf-8'))
        section.save("enforcedl",
                     to_str(data['mb']['force_dl']).encode('utf-8'))
        section.save("crawlseasons",
                     to_str(data['mbsj']['enabled']).encode('utf-8'))
        section.save("seasonsquality",
                     to_str(data['mbsj']['quality']).encode('utf-8'))
        section.save("seasonpacks",
                     to_str(data['mbsj']['packs']).encode('utf-8'))
        section.save("seasonssource",
                     to_str(data['mbsj']['source']).encode('utf-8').lower())
        section.save("imdbyear",
                     to_str(data['mb']['imdb_year']).encode('utf-8'))
        imdb = to_str(data['mb']['imdb_score']).encode('utf-8')
        if re.match('[^0-9]', imdb):
            imdb = 0.0
        elif imdb == '':
            imdb = 0.0
        else:
            imdb = round(float(to_str(data['mb']['imdb_score']).encode(
                'utf-8').replace(",", ".")), 1)
        if imdb > 10:
            imdb = 10.0
        section.save("imdb", to_str(imdb))
        section.save("historical",
                     to_str(data['mb']['historical']).encode('utf-8'))
        section = RssConfig("SJ")
        section.save("hoster",
                     to_str(data['sj']['hoster']).encode('utf-8'))
        section.save("quality",
                     to_str(data['sj']['quality']).encode('utf-8'))
        section.save("rejectlist",
                     to_str(data['sj']['ignore']).encode('utf-8').lower())
        section.save("regex",
                     to_str(data['sj']['regex']).encode('utf-8'))
        section = RssConfig("DD")
        section.save("hoster",
                     to_str(data['dd']['hoster']).encode('utf-8'))
        section.save("feeds",
                     to_str(data['dd']['feeds']).encode('utf-8'))
        section = RssConfig("YT")
        section.save("youtube",
                     to_str(data['yt']['enabled']).encode('utf-8'))
        maxvideos = to_str(data['yt']['max']).encode('utf-8')
        if maxvideos == "":
            maxvideos = "10"
        if to_int(maxvideos) < 1:
            section.save("maxvideos", "1")
        elif to_int(maxvideos) > 50:
            section.save("maxvideos", "50")
        else:
            section.save("maxvideos", to_str(maxvideos))
        section.save("ignore",
                     to_str(data['yt']['ignore']).encode('utf-8'))
        section = RssConfig("Notifications")
        section.save("pushbullet",
                     to_str(data['alerts']['pushbullet']).encode('utf-8'))
        section.save("pushover",
                     to_str(data['alerts']['pushover']).encode('utf-8'))
        section.save("homeassistant",
                     to_str(data['alerts']['homeassistant']).encode('utf-8'))
        section = RssConfig("Crawljobs")
        section.save(
            "autostart", to_str(data['crawljobs']['autostart']).encode('utf-8'))
        section.save("subdir",
                     to_str(data['crawljobs']['subdir']).encode('utf-8'))
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
        db = RssDb(os.path.join(os.path.dirname(
            sys.argv[0]), "RSScrawler.db"), 'rsscrawler')
        db.delete(title)
        return "Success", 200
    else:
        return "Failed", 405


@app.route(prefix + "/api/search/<title>", methods=['GET'])
def search_title(title):
    if request.method == 'GET':
        results = search.get(title)
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


@app.route(prefix + "/api/download_mb/<permalink>", methods=['POST'])
def download_mb(permalink):
    if request.method == 'POST':
        if search.mb(permalink, jdpath):
            return "Success", 200
        else:
            return "Failed", 400
    else:
        return "Failed", 40


@app.route(prefix + "/api/download_sj/<id>", methods=['POST'])
def download_sj(id):
    if request.method == 'POST':
        if search.sj(id, jdpath):
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
                        "filme": getListe('MB_Filme'),
                        "filme3d": getListe('MB_3D'),
                        "regex": getListe('MB_Regex'),
                    },
                    "sj": {
                        "serien": getListe('SJ_Serien'),
                        "regex": getListe('SJ_Serien_Regex'),
                        "staffeln_regex": getListe('SJ_Staffeln_Regex'),
                    },
                    "mbsj": {
                        "staffeln": getListe('MB_Staffeln'),
                    },
                    "yt": {
                        "kanaele_playlisten": getListe('YT_Channels'),
                    },
                },
            }
        )
    if request.method == 'POST':
        data = request.json
        ListDb(os.path.join(os.path.dirname(sys.argv[0]), "RSScrawler.db"), "MB_Filme").store_list(
            data['mb']['filme'].encode('utf-8').split('\n'))
        ListDb(os.path.join(os.path.dirname(sys.argv[0]), "RSScrawler.db"), "MB_3D").store_list(
            data['mb']['filme3d'].encode('utf-8').split('\n'))
        ListDb(os.path.join(os.path.dirname(sys.argv[0]), "RSScrawler.db"), "MB_Staffeln").store_list(
            data['mbsj']['staffeln'].encode('utf-8').split('\n'))
        ListDb(os.path.join(os.path.dirname(sys.argv[0]), "RSScrawler.db"), "MB_Regex").store_list(
            data['mb']['regex'].encode('utf-8').split('\n'))
        ListDb(os.path.join(os.path.dirname(sys.argv[0]), "RSScrawler.db"), "SJ_Serien").store_list(
            data['sj']['serien'].encode('utf-8').split('\n'))
        ListDb(os.path.join(os.path.dirname(sys.argv[0]), "RSScrawler.db"), "SJ_Serien_Regex").store_list(
            data['sj']['regex'].encode('utf-8').split('\n'))
        ListDb(os.path.join(os.path.dirname(sys.argv[0]), "RSScrawler.db"), "SJ_Staffeln_Regex").store_list(
            data['sj']['staffeln_regex'].encode('utf-8').split('\n'))
        ListDb(os.path.join(os.path.dirname(sys.argv[0]), "RSScrawler.db"), "YT_Channels").store_list(
            data['yt']['kanaele_playlisten'].encode('utf-8').split('\n'))
        return "Success", 201
    else:
        return "Failed", 405


def getListe(liste):
    cont = ListDb(os.path.join(os.path.dirname(
        sys.argv[0]), "RSScrawler.db"), liste).retrieve()
    return "\n".join(cont) if cont else ""


def start(port, docker_arg, jd, log_level, log_file, log_format):
    global docker
    docker = docker_arg
    global jdpath
    jdpath = jd

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

    # Disable both log and exceptions in the gevent WSGIServer
    no_logger = logging.getLogger("gevent").setLevel(logging.WARNING)
    gevent.hub.Hub.NOT_ERROR = (Exception,)

    if version.updateCheck()[0]:
        updateversion = version.updateCheck()[1]
        print('Update steht bereit (' + updateversion +
              ')! Weitere Informationen unter https://github.com/rix1337/RSScrawler/releases/latest')
    http_server = WSGIServer(('0.0.0.0', port), app, log=no_logger)
    http_server.serve_forever()
