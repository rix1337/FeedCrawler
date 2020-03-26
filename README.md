#  RSScrawler

RSScrawler automatisiert bequem das Hinzufügen von Links für den JDownloader.

[![PyPI version](https://badge.fury.io/py/rsscrawler.svg)](https://badge.fury.io/py/rsscrawler)
![PyPI - Downloads](https://img.shields.io/pypi/dm/rsscrawler)
[![Github Sponsorship](https://img.shields.io/badge/support-me-red.svg)](https://github.com/users/rix1337/sponsorship)
[![Chat aufrufen unter https://gitter.im/RSScrawler/Lobby](https://badges.gitter.im/RSScrawler/Lobby.svg)](https://gitter.im/RSScrawler/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Build Status](https://travis-ci.org/rix1337/RSScrawler.svg?branch=master)](https://travis-ci.org/rix1337/RSScrawler)
[![GitHub license](https://img.shields.io/github/license/rix1337/RSScrawler.svg)](https://github.com/rix1337/RSScrawler/blob/master/LICENSE.md)
[![GitHub issues](https://img.shields.io/github/issues/rix1337/RSScrawler.svg)](https://github.com/rix1337/RSScrawler/issues)
[![GitHub stars](https://img.shields.io/github/stars/rix1337/RSScrawler.svg)](https://github.com/rix1337/RSScrawler/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/rix1337/RSScrawler.svg)](https://github.com/rix1337/RSScrawler/network)

***

####  Einfache Einrichtung

##### Docker
* Der Betrieb als Docker-Container empfiehlt sich als Standardinstallation - vor allem für NAS-Systeme, Homeserver und sonstige Geräte die dauerhaft und möglichst wartungsfrei (headless) betrieben werden sollen. Beim (Neu-)Start des Containers wird automatisch die neueste Version heruntergeladen.
* Für UNRAID-Server kann der Container direkt über die Community Applications bezogen und eingerichtet werden.
* Offizielles Repo im Docker Hub: [docker-rsscrawler](https://hub.docker.com/r/rix1337/docker-rsscrawler/)

##### Windows
* Jedem [Release](https://github.com/rix1337/RSScrawler/releases) wird eine selbstständig unter Windows lauffähige Version des RSScrawlers beigefügt.
* Hierfür müssen weder Python, noch die Zusatzpakete installiert werden.
* Einfach die jeweilige Exe herunterladen und ausführen bzw. bei Updates die Exe ersetzen.

***

## Sicherheitshinweis

Der Webserver sollte nie ohne Absicherung im Internet freigegeben werden. Dazu lassen sich im Webinterface Nutzername und Passwort festlegen.

Es empfiehlt sich, zusätzlich einen Reverse-Proxy mit HTTPs-Zertifikat, bspw. [kostenlos von letsencrypt](https://letsencrypt.org/), zu verwenden.

## Credits

* [mmarquezs](https://github.com/mmarquezs/)
* [Gutz-Pilz](https://github.com/Gutz-Pilz/)
* [zapp-brannigan](https://github.com/zapp-brannigan/)
* [JetBrains PyCharm](https://www.jetbrains.com/?from=RSScrawler)

***

### Im Folgenden wird die manuelle Installation beschrieben:

####  Voraussetzungen
* [Python 3.7](https://www.python.org/downloads/) oder neuer
* [pip](https://pip.pypa.io/en/stable/installing/)
* [JDownloader 2](http://www.jdownloader.org/jdownloader2) mit [MyJDownloader-Konto](https://my.jdownloader.org)

#### Installation

```pip install rsscrawler```

Hinweise zur manuellen Installation und Einrichtung finden sich im [Wiki](https://github.com/rix1337/RSScrawler/wiki)!

#### Bekannte Fehler

Die folgenden Fehler lassen sich nicht im Code von RSScrawler beheben, sondern nur auf Systemseite:

* Fehler im Installationsprozess per _pip_ deuten auf fehlende Compiler im System hin. Meist muss ein Zusatzpaket nachinstalliert werden (Beispielsweise die [VS C++ Build Tools](https://aka.ms/vs/16/release/vs_buildtools.exe) für Windows oder libffi per `apt-get install libffi-dev` für den Raspberry Pi).

#### Update

```pip install -U rsscrawler```

#### Starten

```rsscrawler``` in der Konsole (Python muss im System-PATH hinterlegt sein)

#### Startparameter

| Parameter | Erläuterung |
|---|---|
| ```--log-level=<LOGLEVEL>``` | Legt fest, wie genau geloggt wird (`CRITICAL`, `ERROR`, `WARNING`, `INFO`, `DEBUG`, `NOTSET`) |
| ```--config="<CFGPFAD>"``` | Legt den Ablageort für Einstellungen und Logs fest |
| ```--port=<PORT>``` | Legt den Port des Webservers fest |
| ```--jd-user=<NUTZERNAME>``` | Legt den Nutzernamen für My JDownloader fest |
| ```--jd-pass=<PASSWORT>``` | Legt das Passwort für My JDownloader fest |
| ```--jd-device=<GERÄTENAME>``` | Legt den Gerätenamen für My JDownloader fest (optional, wenn nur ein Gerät vorhanden ist) |
| ``` --keep-cdc``` | Leere die CDC-Tabelle (Feed ab hier bereits gecrawlt) nicht vor dem ersten Suchlauf |
