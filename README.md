# FeedCrawler

<img src="./feedcrawler/web/img/favicon.ico" data-canonical-src="./feedcrawler/web/img/favicon.ico" width="64" height="64" />

FeedCrawler (ehemals RSScrawler) automatisiert bequem das Hinzufügen von Links für den JDownloader.

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

## Docker

* Offizielles Repo im Docker Hub: [docker-feedcrawler](https://hub.docker.com/r/rix1337/docker-feedcrawler/)
* Der Betrieb als Docker-Container empfiehlt sich als Standardinstallation - vor allem für NAS-Systeme, Homeserver und
  sonstige Geräte die dauerhaft und möglichst wartungsfrei (headless) betrieben werden sollen. Beim (Neu-)Start des
  Containers wird automatisch die neueste Version heruntergeladen. Wird ein neues Image im Docker Hub bereitgestellt,
  sollte dennoch auf dieses aktualisiert werden!
* Für UNRAID-Server kann das Image direkt über die Community Applications bezogen und der Container so eingerichtet
  werden.
* Ein [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) muss lokal verfügbar sein um Cloudflare-Blockaden zu
  umgehen (optional)

## Windows

* Jedem [Release](https://github.com/rix1337/FeedCrawler/releases) wird eine selbstständig unter Windows lauffähige
  Version des Feedcrawlers beigefügt.
* Hierfür müssen weder Python, noch die Zusatzpakete installiert werden.
* Einfach die jeweilige Exe herunterladen und ausführen bzw. bei Updates die Exe ersetzen.
* Ein [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) muss lokal verfügbar sein um Cloudflare-Blockaden zu
  umgehen (optional)

## Manuelle Installation

### Voraussetzungen

* [Python 3.6](https://www.python.org/downloads/) oder neuer
* [pip](https://pip.pypa.io/en/stable/installing/)
* [JDownloader 2](http://www.jdownloader.org/jdownloader2) mit [My JDownloader-Konto](https://my.jdownloader.org)
* [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) um Cloudflare-Blockaden zu umgehen (optional)

### Installation

```pip install feedcrawler```

Hinweise zur manuellen Installation und Einrichtung finden sich im [Wiki](https://github.com/rix1337/FeedCrawler/wiki)!

### Bekannte Fehler

Kommt es nach einem Update oder Neustart des Containers zu einer `sqlite3.OperationalError: database is locked`
-Fehlermeldungen, so muss der Container gestoppt, die `FeedCrawler.db` beliebig (bspw. zu `FeedCrawler-Temp.db`)
umbenannt und direkt wieder zurück zu `FeedCrawler.db` umbenannt werden. Hintergrund ist, dass der FeedCrawler nicht
während die Datenbank verwendet wird (bspw. bei aktiver Feedsuche) gestoppt werden sollte. Der Umbenennungs-Workaround
stellt sicher, dass das Betriebssystem die Datei wieder freigibt (also den Lock loslässt).

Fehler im Installationsprozess per _pip_ deuten auf fehlende Compiler im System hin. Meist muss ein Zusatzpaket
nachinstalliert werden (Beispielsweise die [VS C++ Build Tools](https://aka.ms/vs/16/release/vs_buildtools.exe) für
Windows oder libffi per `apt-get install libffi-dev` für den Raspberry Pi).

### Update

```pip install -U feedcrawler```

### Starten

```feedcrawler``` in der Konsole (Python muss im System-PATH hinterlegt sein)

## Hostnamen festlegen

FeedCrawler kann zum durchsuchen beliebiger Webseiten verwendet werden. Ausschließlich der Anwender entscheidet, welche
Seiten durchsucht werden sollen. Diese Entscheidung trifft der Anwender selbstständig, indem er die _Feedcrawler.ini_ in
der Kategorie _[Hostnames]_ manuell befüllt (_ab = xyz.com_). Eingetragen werden dort reine Hostnamen (ohne _https://_).

### Dabei gilt

* Welcher Hostname aufgerufen wird entscheidet allein der Anwender.
* Ist nicht mindestens ein Hostname gesetzt, wird der FeedCrawler nicht starten.
* Passt die aufgerufene Seite hinter dem jeweiligen Hostnamen nicht zum Suchmuster des Feedcrawlers, kann es zu Fehlern
  kommen.
* Weder FeedCrawler noch der Autor benennen oder befürworten spezifische Hostnamen. Fragen hierzu werden ignoriert!

## Sicherheitshinweis

Der Webserver sollte nie ohne Absicherung im Internet freigegeben werden. Dazu lassen sich im Webinterface Nutzername
und Passwort festlegen.

Es empfiehlt sich, zusätzlich einen Reverse-Proxy mit HTTPs-Zertifikat,
bspw. [kostenlos von letsencrypt](https://letsencrypt.org/), zu verwenden.

## Startparameter

| Parameter | Erläuterung |
|---|---|
| ```--log-level=<LOGLEVEL>``` | Legt fest, wie genau geloggt wird (`CRITICAL`, `ERROR`, `WARNING`, `INFO`, `DEBUG`, `NOTSET`) |
| ```--config="<CFGPFAD>"``` | Legt den Ablageort für Einstellungen und Logs fest |
| ```--port=<PORT>``` | Legt den Port des Webservers fest |
| ```--jd-user=<NUTZERNAME>``` | Legt den Nutzernamen für My JDownloader fest |
| ```--jd-pass=<PASSWORT>``` | Legt das Passwort für My JDownloader fest |
| ```--jd-device=<GERÄTENAME>``` | Legt den Gerätenamen für My JDownloader fest (optional, wenn nur ein Gerät vorhanden ist) |
| ``` --keep-cdc``` | Leere die CDC-Tabelle (Feed ab hier bereits gecrawlt) nicht vor dem ersten Suchlauf |

## Credits

* [mmarquezs](https://github.com/mmarquezs/)
* [Gutz-Pilz](https://github.com/Gutz-Pilz/)
* [zapp-brannigan](https://github.com/zapp-brannigan/)
* [JetBrains PyCharm](https://www.jetbrains.com/?from=FeedCrawler)
