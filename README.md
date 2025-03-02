> ## Important Notice / Wichtiger Hinweis
> 
> **English:**  
> This project is now a public archive and is no longer under active development.  
> It is recommended to switch to the much more streamlined [Quasarr](https://github.com/rix1337/Quasarr). 😃🚀
> 
> **Deutsch:**  
> Dieses Projekt ist nun ein öffentliches Archiv und wird nicht mehr aktiv weiterentwickelt.  
> Es empfiehlt sich, zum wesentlich schlankeren [Quasarr](https://github.com/rix1337/Quasarr) zu wechseln. 😃🚀



# FeedCrawler

<img src="https://raw.githubusercontent.com/rix1337/FeedCrawler/main/FeedCrawler.png" data-canonical-src="https://raw.githubusercontent.com/rix1337/FeedCrawler/main/FeedCrawler.png" width="64" height="64" />

FeedCrawler automatisiert bequem das Hinzufügen von Links für den JDownloader.

[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/rix1337/FeedCrawler/CreateRelease.yml?branch=main)](https://github.com/rix1337/FeedCrawler/actions/workflows/CreateRelease.yml)
[![GitHub stars](https://img.shields.io/github/stars/rix1337/FeedCrawler?style=flat)](https://github.com/rix1337/FeedCrawler/stargazers)
[![GitHub all releases](https://img.shields.io/github/downloads/rix1337/feedcrawler/total?label=github%20downloads)](https://github.com/rix1337/FeedCrawler/releases)

[![PyPI](https://img.shields.io/pypi/v/feedcrawler?label=pypi%20package)](https://pypi.org/project/feedcrawler/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/feedcrawler?label=pypi%20downloads)](https://pypi.org/project/feedcrawler/#files)

[![Docker Image Version (latest semver)](https://img.shields.io/docker/v/rix1337/docker-feedcrawler?label=docker%20image&sort=semver)](https://hub.docker.com/r/rix1337/docker-feedcrawler/tags)
[![Docker Pulls](https://img.shields.io/docker/pulls/rix1337/docker-feedcrawler)](https://hub.docker.com/r/rix1337/docker-feedcrawler/)

[![GitHub license](https://img.shields.io/github/license/rix1337/FeedCrawler.svg)](https://github.com/rix1337/FeedCrawler/blob/main/LICENSE.md)
[![Python 3 Backend](https://img.shields.io/badge/backend-python%203-blue.svg)](https://github.com/rix1337/FeedCrawler/tree/main/feedcrawler)
[![Vue.js 3 Frontend](https://img.shields.io/badge/frontend-vue.js%203-brightgreen.svg)](https://github.com/rix1337/FeedCrawler/tree/main/feedcrawler/web_interface/vuejs_frontend)
[![GitHub last commit](https://img.shields.io/github/last-commit/rix1337/FeedCrawler)](https://github.com/rix1337/FeedCrawler/commits/main)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/y/rix1337/feedcrawler)](https://github.com/rix1337/FeedCrawler/graphs/commit-activity)
[![Lines of code](https://img.shields.io/endpoint?url=https://ghloc.vercel.app/api/rix1337/FeedCrawler/badge?filter=.py$,.vue$,js$,scss$,yml$&style=flat&logoColor=white&label=Lines%20of%20Code)](https://github.com/rix1337/FeedCrawler/pulse)

[![GitHub Sponsorship](https://img.shields.io/badge/support-me-red.svg)](https://github.com/users/rix1337/sponsorship)
[![Discord](https://img.shields.io/discord/1075348594225315891)](https://discord.gg/eM4zA2wWQb)
[![GitHub issues](https://img.shields.io/github/issues/rix1337/FeedCrawler.svg)](https://github.com/rix1337/FeedCrawler/issues)

***

## Installation

## Manuelle Installation

### Voraussetzungen

* [Python 3.8](https://www.python.org/downloads/) oder neuer (nur
  5 [externe Abhängigkeiten](https://github.com/rix1337/FeedCrawler/blob/main/requirements.txt)!)
* [JDownloader 2](http://www.jdownloader.org/jdownloader2) mit
  aktivem [My JDownloader-Konto](https://my.jdownloader.org)
* _optional: [FlareSolverr 3](https://github.com/FlareSolverr/FlareSolverr) um Cloudflare-Blockaden zu umgehen_

### Installation / Update durch [pip](https://pip.pypa.io/en/stable/installation/)

```pip install -U feedcrawler```

### Lokaler Build

Benötigt [Node.js](https://nodejs.org/en/download/), [npm](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm)
und [pip](https://pip.pypa.io/en/stable/installation/):

1. Frontend-Pfad aufrufen: `cd feedcrawler/web_interface/vuejs_frontend`
2. Dependencies installieren: `npm ci`
3. [Vue.js 3](https://vuejs.org/) Frontend kompilieren: `npm run build`
4. Zurück in das Hauptverzeichnis wechseln: `cd ../../..`
5. FeedCrawler auf Basis der _setup.py_ installieren: `pip install .`

### Start

```feedcrawler``` in der Konsole (Python muss im System-PATH hinterlegt sein)

### [Docker Image](https://hub.docker.com/r/rix1337/docker-feedcrawler/)

```
docker run -d \
  --name="FeedCrawler" \
  -p port:9090 \
  -v /path/to/config/:/config:rw \
  -e DELAY=30 \
  -e LOGLEVEL=[INFO/DEBUG] \
  --log-opt max-size=50m \
  rix1337/docker-feedcrawler
  ```

* Der Betrieb als Docker-Container empfiehlt sich als Standardinstallation - vor allem für NAS-Systeme, Homeserver und
  sonstige Geräte die dauerhaft und möglichst wartungsfrei (headless) betrieben werden sollen.
* Bei jedem Release wird ein getaggtes Image erstellt. Damit kann man auf der Wunschversion verbleiben oder im Falle
  eines Bugs zu einer stabilen Version zurück kehren.
* Um immer auf dem aktuellen Stand zu sein, einfach das mit `latest` getaggte Image nutzen.
* Für UNRAID-Server kann das Image direkt über die Community Applications bezogen und der Container so eingerichtet
  werden.

##### Spezifische Version nutzen

Das Image `rix1377/docker-feedcrawler` wird standardmäßig auf das `:latest`-Tag aufgelöst. Dieses wird mit jedem Release
auf die neue Version aktualisiert. Mit jedem Release wird ebenfalls eine getaggte Version des Images erzeugt. Auf
letztere kann man wechseln, um beispielsweise bei Fehlern in der neuen Version auf einen funktionierenden Stand zurück
zu kehren.

Beispiel:

`docker pull rix1337/docker-feedcrawler:13.3.7`

### Windows Build

* Jedem [Release](https://github.com/rix1337/FeedCrawler/releases) wird eine selbstständig unter Windows lauffähige
  Version des FeedCrawlers beigefügt.
* Hierfür müssen weder Python, noch die Zusatzpakete installiert werden.
* Einfach die jeweilige Exe herunterladen und ausführen bzw. bei Updates die Exe ersetzen.

## Hostnamen

FeedCrawler kann zum Durchsuchen beliebiger Webseiten verwendet werden.
Welche das sind, entscheiden Anwender selbständig bei der Einrichtung. Es gilt dabei:

* Welche Hostname aufgerufen werden entscheidet allein der Anwender.
* Ist nicht mindestens ein Hostname gesetzt, wird der FeedCrawler nicht starten.
* Passen Hostnamen nicht zum jeweiligen Suchmuster des FeedCrawlers, sind Fehlermeldungen möglich.

## Startparameter

| Parameter                    | Erläuterung                                                        |
|------------------------------|--------------------------------------------------------------------|
| ```--log-level=<LOGLEVEL>``` | Legt fest, wie genau geloggt wird (`INFO` oder `DEBUG`)            |
| ```--port=<PORT>```          | Legt den Port des Webservers fest                                  |
| ```--delay=<SEKUNDEN>```     | Verzögere Suchlauf nach Start um ganze Zahl in Sekunden (optional) |

## Sicherheitshinweis

Der Webserver sollte nie ohne Absicherung im Internet freigegeben werden. Dazu lassen sich im Webinterface Nutzername
und Passwort festlegen.

Es empfiehlt sich, zusätzlich einen Reverse-Proxy mit HTTPs-Zertifikat,
bspw. [kostenlos von letsencrypt](https://letsencrypt.org/), zu verwenden.

## Credits

* [mmarquezs](https://github.com/mmarquezs/) (My-JDownloader-API für Python)
