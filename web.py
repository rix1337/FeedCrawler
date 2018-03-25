# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

from flask import Flask, request, send_from_directory, render_template, jsonify

from output import Unbuffered
from output import CutLog
from rssconfig import RssConfig
from rssdb import RssDb
import search
import files
import version

import os
import re
import sys
import gevent
from gevent.wsgi import WSGIServer
import logging
from logging import handlers
try:
    # For Python 2.0 and later
    import StringIO
except ImportError:
    # For Python 3.0 and later
    import io as StringIO

app = Flask(__name__, static_url_path='/web', template_folder='web')

if not os.path.exists(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen')):
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
        yt = RssConfig('YT')
        ver = version.getVersion()
        if version.updateCheck()[0]:
            updateready = True
            updateversion = version.updateCheck()[1]
            print('Update steht bereit (' + updateversion +')! Weitere Informationen unter https://github.com/rix1337/RSScrawler/releases/latest')
        else:
            updateready = False
        log = ''
        logfile = os.path.join(os.path.dirname(sys.argv[0]), 'RSScrawler.log')
        if os.path.isfile(logfile):
            logfile = open(os.path.join(logfile))
            output = StringIO.StringIO()
            for line in reversed(logfile.readlines()):
                output.write("<p>" + line.replace("\n","</p>"))
                log = output.getvalue()
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
                        "english": bool(general.get("english")),
                        "hoster": general.get("hoster"),
                    },
                    "alerts": {
                        "homeassistant": alerts.get("homeassistant"),
                        "pushbullet": alerts.get("pushbullet"),
                        "pushover": alerts.get("pushover"),
                    },
                    "crawljobs": {
                        "autostart": bool(crawljobs.get("autostart")),
                        "subdir": bool(crawljobs.get("subdir")),
                    },
                    "mb": {
                        "quality": mb.get("quality"),
                        "ignore": mb.get("ignore"),
                        "regex": bool(mb.get("regex")),
                        "imdb_score": to_float(mb.get("imdb")),
                        "imdb_year": to_int(mb.get("imdbyear")),
                        "historical": bool(mb.get("historical")),
                        "force_dl": bool(mb.get("enforcedl")),
                        "cutoff": bool(mb.get("cutoff")),
                        "crawl_3d": bool(mb.get("crawl3d")),
                    },
                    "sj": {
                        "quality": sj.get("quality"),
                        "ignore": sj.get("rejectlist"),
                        "regex": bool(sj.get("regex")),
                    },
                    "mbsj": {
                        "enabled": bool(mb.get("crawlseasons")),
                        "quality": mb.get("seasonsquality"),
                        "packs": bool(mb.get("seasonpacks")),
                        "source": mb.get("seasonssource"),
                    },
                    "yt": {
                        "enabled": bool(yt.get("youtube")),
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
                output.write("<p>" + line.replace("\n","</p>"))
                log = output.getvalue()
        return jsonify(
            {
                "log": log,
            }
        )
    if request.method == 'DELETE':
        open(os.path.join(os.path.dirname(sys.argv[0]), 'RSScrawler.log'), 'w').close()
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
        yt = RssConfig('YT')
        return jsonify(
            {
                "settings": {
                    "general": {
                        "pfad": general.get("jdownloader"),
                        "port": to_int(general.get("port")),
                        "prefix": general.get("prefix"),
                        "interval": to_int(general.get("interval")),
                        "english": bool(general.get("english")),
                        "hoster": general.get("hoster"),
                    },
                    "alerts": {
                        "homeassistant": alerts.get("homeassistant"),
                        "pushbullet": alerts.get("pushbullet"),
                        "pushover": alerts.get("pushover"),
                    },
                    "crawljobs": {
                        "autostart": bool(crawljobs.get("autostart")),
                        "subdir": bool(crawljobs.get("subdir")),
                    },
                    "mb": {
                        "quality": mb.get("quality"),
                        "ignore": mb.get("ignore"),
                        "regex": bool(mb.get("regex")),
                        "imdb_score": to_float(mb.get("imdb")),
                        "imdb_year": to_int(mb.get("imdbyear")),
                        "historical": bool(mb.get("historical")),
                        "force_dl": bool(mb.get("enforcedl")),
                        "cutoff": bool(mb.get("cutoff")),
                        "crawl_3d": bool(mb.get("crawl3d")),
                    },
                    "sj": {
                        "quality": sj.get("quality"),
                        "ignore": sj.get("rejectlist"),
                        "regex": bool(sj.get("regex")),
                    },
                    "mbsj": {
                        "enabled": bool(mb.get("crawlseasons")),
                        "quality": mb.get("seasonsquality"),
                        "packs": bool(mb.get("seasonpacks")),
                        "source": mb.get("seasonssource"),
                    },
                    "yt": {
                        "enabled": bool(yt.get("youtube")),
                        "max": to_int(yt.get("maxvideos")),
                        "ignore": yt.get("ignore"),
                    }
                }
            }
        )
    if request.method == 'POST':
        data = request.json
        with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/RSScrawler.ini'), 'wb') as f:
            f.write('# RSScrawler.ini (Stand: RSScrawler ' + version.getVersion() + ')\n')
            f.write("\n[RSScrawler]\n")
            f.write("jdownloader = " + to_str(data['general']['pfad']).encode('utf-8') + "\n")
            f.write("port = " + to_str(data['general']['port']).encode('utf-8') + "\n")
            f.write("prefix = " + to_str(data['general']['prefix']).encode('utf-8').lower() + "\n")
            interval = to_str(data['general']['interval']).encode('utf-8')
            if to_int(interval) < 3:
                interval = '3'
            f.write("interval = " + interval + "\n")
            f.write("english = " + to_str(data['general']['english']).encode('utf-8') + "\n")
            f.write("hoster = " + to_str(data['general']['hoster']).encode('utf-8') + "\n")
            f.write("\n[MB]\n")
            f.write("quality = " + to_str(data['mb']['quality']).encode('utf-8') + "\n")
            f.write("ignore = " + to_str(data['mb']['ignore']).encode('utf-8').lower() + "\n")
            f.write("historical = " + to_str(data['mb']['historical']).encode('utf-8') + "\n")
            f.write("regex = " + to_str(data['mb']['regex']).encode('utf-8') + "\n")
            f.write("cutoff = " + to_str(data['mb']['cutoff']).encode('utf-8') + "\n")
            f.write("crawl3d = " + to_str(data['mb']['crawl_3d']).encode('utf-8') + "\n")
            f.write("enforcedl = " + to_str(data['mb']['force_dl']).encode('utf-8') + "\n")
            f.write("crawlseasons = " + to_str(data['mbsj']['enabled']).encode('utf-8') + "\n")
            f.write("seasonsquality = " + to_str(data['mbsj']['quality']).encode('utf-8') + "\n")
            f.write("seasonpacks = " + to_str(data['mbsj']['packs']).encode('utf-8') + "\n")
            f.write("seasonssource = " + to_str(data['mbsj']['source']).encode('utf-8').lower() + "\n")
            f.write("imdbyear = " + to_str(data['mb']['imdb_year']).encode('utf-8') + "\n")
            imdb = to_str(data['mb']['imdb_score']).encode('utf-8')
            if re.match('[^0-9]', imdb):
                imdb = 0.0
            elif imdb == '':
                imdb = 0.0
            else:
                imdb = round(float(to_str(data['mb']['imdb_score']).encode('utf-8').replace(",", ".")), 1)
            if imdb > 10:
                imdb = 10.0
            f.write("imdb = " + to_str(imdb) + "\n")
            f.write("\n[SJ]\n")
            f.write("quality = " + to_str(data['sj']['quality']).encode('utf-8') + "\n")
            f.write("rejectlist = " + to_str(data['sj']['ignore']).encode('utf-8').lower() + "\n")
            f.write("regex = " + to_str(data['sj']['regex']).encode('utf-8') + "\n")
            f.write("\n[YT]\n")
            f.write("youtube = " + to_str(data['yt']['enabled']).encode('utf-8') + "\n")
            maxvideos = to_str(data['yt']['max']).encode('utf-8')
            if maxvideos == "":
                maxvideos = "10"
            if to_int(maxvideos) < 1:
                f.write("maxvideos = 1\n")
            elif to_int(maxvideos) > 50:
                f.write("maxvideos = 50\n")
            else:
                f.write("maxvideos = " + to_str(maxvideos) + "\n")
            f.write("ignore = " + to_str(data['yt']['ignore']).encode('utf-8') + "\n")
            f.write("\n[Notifications]\n")
            f.write("homeassistant = " + to_str(data['alerts']['homeassistant']).encode('utf-8') + "\n")
            f.write("pushbullet = " + to_str(data['alerts']['pushbullet']).encode('utf-8') + "\n")
            f.write("pushover = " + to_str(data['alerts']['pushover']).encode('utf-8') + "\n")
            f.write("\n[Crawljobs]\n")
            f.write("autostart = " + to_str(data['crawljobs']['autostart']).encode('utf-8') + "\n")
            f.write("subdir = " + to_str(data['crawljobs']['subdir']).encode('utf-8') + "\n")
        files.check()
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
            print('Update steht bereit (' + updateversion +')! Weitere Informationen unter https://github.com/rix1337/RSScrawler/releases/latest')
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
        db = RssDb(os.path.join(os.path.dirname(sys.argv[0]), "Einstellungen/Downloads/Downloads.db"))
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
        with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/MB_Filme.txt'), 'wb') as f:
            f.write(data['mb']['filme'].encode('utf-8'))
        with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/MB_3D.txt'), 'wb') as f:
            f.write(data['mb']['filme3d'].encode('utf-8'))
        with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/MB_Staffeln.txt'), 'wb') as f:
            f.write(data['mbsj']['staffeln'].encode('utf-8'))
        with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/MB_Regex.txt'), 'wb') as f:
            f.write(data['mb']['regex'].encode('utf-8'))
        with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/SJ_Serien.txt'), 'wb') as f:
            f.write(data['sj']['serien'].encode('utf-8'))
        with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/SJ_Serien_Regex.txt'), 'wb') as f:
            f.write(data['sj']['regex'].encode('utf-8'))
        with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/SJ_Staffeln_Regex.txt'), 'wb') as f:
            f.write(data['sj']['staffeln_regex'].encode('utf-8'))
        with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/YT_Channels.txt'), 'wb') as f:
            f.write(data['yt']['kanaele_playlisten'].encode('utf-8'))
        files.check()
        return "Success", 201
    else:
        return "Failed", 405

def getListe(liste):
    if not os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/' + liste + '.txt')):
        return "Liste nicht gefunden"
    else:
        file = open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/' + liste + '.txt'))
        output = StringIO.StringIO()
        for line in file.readlines():
            output.write(line.replace("XXXXXXXXXX",""))
    return output.getvalue()

def start(port, docker_arg, jd, log_level, log_file, log_format):
    global docker
    docker = docker_arg
    global jdpath
    jdpath = jd

    sys.stdout = Unbuffered(sys.stdout)

    console = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter(log_format)
    console.setFormatter(CutLog(log_format))

    logfile = logging.handlers.RotatingFileHandler(log_file, maxBytes=100000, backupCount=5)
    logfile.setFormatter(formatter)

    logger = logging.getLogger('')
    logger.addHandler(logfile)
    logger.addHandler(console)
    logger.setLevel(log_level)

    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # Disable both log and exceptions in the gevent WSGIServer
    no_logger = logging.getLogger("gevent").setLevel(logging.WARNING)
    gevent.hub.Hub.NOT_ERROR=(Exception,)

    if version.updateCheck()[0]:
        updateversion = version.updateCheck()[1]
        print('Update steht bereit (' + updateversion +')! Weitere Informationen unter https://github.com/rix1337/RSScrawler/releases/latest')
    http_server = WSGIServer(('0.0.0.0', port), app, log = no_logger)
    http_server.serve_forever()
