# FeedCrawler

<img src="./feedcrawler/web/public/favicon.ico" data-canonical-src="./feedcrawler/web/img/favicon.ico" width="64" height="64" />

FeedCrawler automatisiert bequem das Hinzufügen von Links für den JDownloader.

[![Release Artifacts](https://github.com/rix1337/FeedCrawler/actions/workflows/CreateRelease.yml/badge.svg?branch=master)](https://github.com/rix1337/FeedCrawler/actions/workflows/CreateRelease.yml)
[![PyPI version](https://badge.fury.io/py/feedcrawler.svg)](https://badge.fury.io/py/feedcrawler)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/feedcrawler)](https://github.com/rix1337/FeedCrawler/releases)
[![Github Sponsorship](https://img.shields.io/badge/support-me-red.svg)](https://github.com/users/rix1337/sponsorship)
[![Chat aufrufen unter https://gitter.im/FeedCrawler/community](https://badges.gitter.im/FeedCrawler/community.svg)](https://gitter.im/FeedCrawler/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![GitHub license](https://img.shields.io/github/license/rix1337/FeedCrawler.svg)](https://github.com/rix1337/FeedCrawler/blob/master/LICENSE.md)
[![GitHub issues](https://img.shields.io/github/issues/rix1337/FeedCrawler.svg)](https://github.com/rix1337/FeedCrawler/issues)
[![GitHub stars](https://img.shields.io/github/stars/rix1337/FeedCrawler.svg)](https://github.com/rix1337/FeedCrawler/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/rix1337/FeedCrawler.svg)](https://github.com/rix1337/FeedCrawler/network)

***

## Installation

### Voraussetzungen

* [Python 3.7](https://www.python.org/downloads/) oder neuer
* [JDownloader 2](http://www.jdownloader.org/jdownloader2) mit [My JDownloader-Konto](https://my.jdownloader.org)
* [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) ab v.2.0.0 um Cloudflare-Blockaden zu umgehen (optional)

### Lokaler Build
Benötigt [Node.js](https://nodejs.org/en/download/), [npm](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) und [pip](https://pip.pypa.io/en/stable/installation/):

1. Frontend-Pfad aufrufen: `cd feedcrawler/web`
2. Dependencies installieren: `npm ci`
3. [Vue.js 3](https://vuejs.org/) Frontend kompilieren: `npm run build`
4. Zurück in das Hauptverzeichnis wechseln: `cd ../..`
5. FeedCrawler auf Basis der _setup.py_ installieren: `pip install .`

### [pip](https://pip.pypa.io/en/stable/installation/)

#### Installieren

```pip install feedcrawler```

Hinweise zur manuellen Installation und Einrichtung finden sich im [Wiki](https://github.com/rix1337/FeedCrawler/wiki)!

#### Update

```pip install -U feedcrawler```

#### Starten

```feedcrawler``` in der Konsole (Python muss im System-PATH hinterlegt sein)

### [Docker Image](https://hub.docker.com/r/rix1337/docker-feedcrawler/)

* Der Betrieb als Docker-Container empfiehlt sich als Standardinstallation - vor allem für NAS-Systeme, Homeserver und
  sonstige Geräte die dauerhaft und möglichst wartungsfrei (headless) betrieben werden sollen.
* Bei jedem Release wird ein getaggtes Image erstellt. Damit kann man auf der Wunschversion verbleiben oder im Falle
  eines Bugs zu einer stabilen Version zurück kehren.
* Um immer auf dem aktuellen Stand zu sein, einfach das mit `latest` getaggte Image nutzen.
* Für UNRAID-Server kann das Image direkt über die Community Applications bezogen und der Container so eingerichtet
  werden.

### Windows Exe

* Jedem [Release](https://github.com/rix1337/FeedCrawler/releases) wird eine selbstständig unter Windows lauffähige
  Version des FeedCrawlers beigefügt.
* Hierfür müssen weder Python, noch die Zusatzpakete installiert werden.
* Einfach die jeweilige Exe herunterladen und ausführen bzw. bei Updates die Exe ersetzen.

### Hostnamen festlegen

FeedCrawler kann zum durchsuchen beliebiger Webseiten verwendet werden. Ausschließlich der Anwender entscheidet, welche
Seiten durchsucht werden sollen. Diese Entscheidung trifft der Anwender selbstständig, indem er die _FeedCrawler.ini_ in
der Kategorie _[Hostnames]_ manuell befüllt (_ab = xyz.com_). Eingetragen werden dort reine Hostnamen (ohne _https://_).

#### Dabei gilt

* Welcher Hostname aufgerufen wird entscheidet allein der Anwender.
* Ist nicht mindestens ein Hostname gesetzt, wird der FeedCrawler nicht starten.
* Passt die aufgerufene Seite hinter dem jeweiligen Hostnamen nicht zum Suchmuster des FeedCrawlers, kann es zu Fehlern
  kommen.
* Weder FeedCrawler noch der Autor benennen oder befürworten spezifische Hostnamen. Fragen hierzu werden ignoriert!

### Startparameter

| Parameter | Erläuterung |
|---|---|
| ```--log-level=<LOGLEVEL>``` | Legt fest, wie genau geloggt wird (`CRITICAL`, `ERROR`, `WARNING`, `INFO`, `DEBUG`, `NOTSET`) |
| ```--config="<CFGPFAD>"``` | Legt den Ablageort für Einstellungen und Logs fest |
| ```--port=<PORT>``` | Legt den Port des Webservers fest |
| ```--jd-user=<NUTZERNAME>``` | Legt den Nutzernamen für My JDownloader fest |
| ```--jd-pass=<PASSWORT>``` | Legt das Passwort für My JDownloader fest |
| ```--jd-device=<GERÄTENAME>``` | Legt den Gerätenamen für My JDownloader fest (optional, wenn nur ein Gerät vorhanden ist) |
| ``` --keep-cdc``` | Leere die CDC-Tabelle (Feed ab hier bereits gecrawlt) nicht vor dem ersten Suchlauf |


### Sicherheitshinweis

Der Webserver sollte nie ohne Absicherung im Internet freigegeben werden. Dazu lassen sich im Webinterface Nutzername
und Passwort festlegen.

Es empfiehlt sich, zusätzlich einen Reverse-Proxy mit HTTPs-Zertifikat,
bspw. [kostenlos von letsencrypt](https://letsencrypt.org/), zu verwenden.

## Credits

* [zapp-brannigan](https://github.com/zapp-brannigan/) (Idee)
* Gutz-Pilz (Idee)
* [mmarquezs](https://github.com/mmarquezs/) (MyJDownloader-API für Python)
* [JetBrains PyCharm](https://www.jetbrains.com/?from=FeedCrawler) (Lizenz für die IDE)
