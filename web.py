from flask import Flask, request, send_from_directory, render_template, jsonify

from rssconfig import RssConfig
import files
import version

import StringIO
import os
import re
import sys

import logging

app = Flask(__name__, static_url_path='/web', template_folder='web')

general = RssConfig('RSScrawler')
if general.get("prefix"):
    prefix = '/' + general.get("prefix")
else:
    prefix = ""

def to_int(i):
    i = i.strip()
    return int(i) if i else ""

def to_float(i):
    i = i.strip()
    return float(i) if i else ""

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
                        "hoster": general.get("hoster"),
                    },
                    "alerts": {
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
                        "hoster": general.get("hoster"),
                    },
                    "alerts": {
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
            f.write("jdownloader = " + str(data['general']['pfad']).encode('utf-8') + "\n")
            f.write("port = " + str(data['general']['port']).encode('utf-8') + "\n")
            f.write("prefix = " + str(data['general']['prefix']).encode('utf-8').lower() + "\n")
            interval = str(data['general']['interval']).encode('utf-8')
            if to_int(interval) < 3:
                interval = '3'
            f.write("interval = " + interval + "\n")
            f.write("hoster = " + str(data['general']['hoster']).encode('utf-8') + "\n")
            f.write("\n[MB]\n")
            f.write("quality = " + str(data['mb']['quality']).encode('utf-8') + "\n")
            f.write("ignore = " + str(data['mb']['ignore']).encode('utf-8').lower() + "\n")
            f.write("historical = " + str(data['mb']['historical']).encode('utf-8') + "\n")
            f.write("regex = " + str(data['mb']['regex']).encode('utf-8') + "\n")
            f.write("cutoff = " + str(data['mb']['cutoff']).encode('utf-8') + "\n")
            f.write("crawl3d = " + str(data['mb']['crawl_3d']).encode('utf-8') + "\n")
            f.write("enforcedl = " + str(data['mb']['force_dl']).encode('utf-8') + "\n")
            f.write("crawlseasons = " + str(data['mbsj']['enabled']).encode('utf-8') + "\n")
            f.write("seasonsquality = " + str(data['mbsj']['quality']).encode('utf-8') + "\n")
            f.write("seasonpacks = " + str(data['mbsj']['packs']).encode('utf-8') + "\n")
            f.write("seasonssource = " + str(data['mbsj']['source']).encode('utf-8').lower() + "\n")
            f.write("imdbyear = " + str(data['mb']['imdb_year']).encode('utf-8') + "\n")
            imdb = str(data['mb']['imdb_score']).encode('utf-8')
            if re.match('[^0-9]', imdb):
                imdb = 0.0
            elif imdb == '':
                imdb = 0.0
            else:
                imdb = round(float(str(data['mb']['imdb_score']).encode('utf-8').replace(",", ".")), 1)
            if imdb > 10:
                imdb = 10.0
            f.write("imdb = " + str(imdb) + "\n")
            f.write("\n[SJ]\n")
            f.write("quality = " + str(data['sj']['quality']).encode('utf-8') + "\n")
            f.write("rejectlist = " + str(data['sj']['ignore']).encode('utf-8').lower() + "\n")
            f.write("regex = " + str(data['sj']['regex']).encode('utf-8') + "\n")
            f.write("\n[YT]\n")
            f.write("youtube = " + str(data['yt']['enabled']).encode('utf-8') + "\n")
            maxvideos = str(data['yt']['max']).encode('utf-8')
            if maxvideos == "":
                maxvideos = "10"
            if to_int(maxvideos) < 1:
                f.write("maxvideos = 1\n")
            elif to_int(maxvideos) > 50:
                f.write("maxvideos = 50\n")
            else:
                f.write("maxvideos = " + str(maxvideos) + "\n")
            f.write("ignore = " + str(data['yt']['ignore']).encode('utf-8') + "\n")
            f.write("\n[Notifications]\n")
            f.write("pushbullet = " + str(data['alerts']['pushbullet']).encode('utf-8') + "\n")
            f.write("pushover = " + str(data['alerts']['pushover']).encode('utf-8') + "\n")
            f.write("\n[Crawljobs]\n")
            f.write("autostart = " + str(data['crawljobs']['autostart']).encode('utf-8') + "\n")
            f.write("subdir = " + str(data['crawljobs']['subdir']).encode('utf-8') + "\n")
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

def start(port, docker_arg):
    global docker
    docker = docker_arg
    if version.updateCheck()[0]:
        updateversion = version.updateCheck()[1]
        print('Update steht bereit (' + updateversion +')! Weitere Informationen unter https://github.com/rix1337/RSScrawler/releases/latest')
    logger = logging.getLogger('werkzeug')
    logger.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=port)
