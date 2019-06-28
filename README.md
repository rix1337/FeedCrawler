#  RSScrawler

RSScrawler automatisiert bequem das Hinzufügen von Links für den JDownloader.

[![PyPI version](https://badge.fury.io/py/rsscrawler.svg)](https://badge.fury.io/py/rsscrawler)
[![Chat aufrufen unter https://gitter.im/RSScrawler/Lobby](https://badges.gitter.im/RSScrawler/Lobby.svg)](https://gitter.im/RSScrawler/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Build Status](https://travis-ci.org/rix1337/RSScrawler.svg?branch=master)](https://travis-ci.org/rix1337/RSScrawler)
[![GitHub license](https://img.shields.io/github/license/rix1337/RSScrawler.svg)](https://github.com/rix1337/RSScrawler/blob/master/LICENSE.md)
[![GitHub issues](https://img.shields.io/github/issues/rix1337/RSScrawler.svg)](https://github.com/rix1337/RSScrawler/issues)
[![GitHub stars](https://img.shields.io/github/stars/rix1337/RSScrawler.svg)](https://github.com/rix1337/RSScrawler/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/rix1337/RSScrawler.svg)](https://github.com/rix1337/RSScrawler/network)

[![ko-fi](https://www.ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/J3J4Y2R6)

##  Voraussetzungen

* [Python 3.7](https://www.python.org/downloads/)
* [pip](https://pip.pypa.io/en/stable/installing/)
* [JDownloader 2](http://www.jdownloader.org/jdownloader2)

## Installation

```pip install rsscrawler```

Hinweise zur manuellen Installation und Einrichtung finden sich im [Wiki](https://github.com/rix1337/RSScrawler/wiki)!

## Bekannte Fehler

Die folgenden Fehler lassen sich nicht im Code von RSScrawler beheben, sondern nur auf Systemseite:

* Python _Levenshtein_ wird ausschließlich in der Suche per Webinterface/API von der _fuzzywuzzy_ Bibliothek verwendet, die notfalls auf eine langsamere Alternative ausweicht. Die Warnung beim Start, dass das Modul fehlt, lässt sich optional per `pip install python-Levenshtein` vermeiden.
* Fehler im Installationsprozess per _pip_ deuten auf fehlende Compiler im System hin. Meist muss ein Zusatzpaket nachinstalliert werden (Beispielsweise die [VS C++ Build Tools](https://visualstudio.microsoft.com/de/visual-cpp-build-tools/) für Windows oder libffi per `apt-get install libffi-dev` für den Raspberry Pi).

## Update

```pip install -U rsscrawler```

## Sicherheitshinweis

Der Webserver sollte nie ohne Absicherung im Internet freigegeben werden. Dazu lassen sich im Webinterface Nutzername und Passwort festlegen.

Es empfiehlt sich, zusätzlich einen Reverse-Proxy mit HTTPs-Zertifikat, bspw. [kostenlos von letsencrypt](https://letsencrypt.org/), zu verwenden.

## Starten

```rsscrawler``` in der Konsole (Python muss im System-PATH hinterlegt sein)

## Startparameter

| Parameter | Erläuterung |
|---|---|
| ```--log-level=<LOGLEVEL>``` | Legt fest, wie genau geloggt wird (`CRITICAL`, `ERROR`, `WARNING`, `INFO`, `DEBUG`, `NOTSET`) |
| ```--config="<CFGPFAD>"``` | Legt den Ablageort für Einstellungen und Logs fest |
| ```--port=<PORT>``` | Legt den Port des Webservers fest |
| ```--jd-user=<NUTZERNAME>``` | Legt den Nutzernamen für My JDownloader fest |
| ```--jd-pass=<PASSWORT>``` | Legt das Passwort für My JDownloader fest |
| ```--jd-device=<GERÄTENAME>``` | Legt den Gerätenamen für My JDownloader fest (optional, wenn nur ein Gerät vorhanden ist) |
| ```--jd-pfad="<JDPFAD>"``` | Legt den Pfad von JDownloader fest (nicht empfohlen - stattdessen My JDownloader nutzen) |
| ``` --keep-cdc``` | _Leere die CDC-Tabelle (Feed ab hier bereits gecrawlt) nicht vor dem ersten Suchlauf_ |
| ```--testlauf``` | _Intern: Einmalige Ausführung von RSScrawler_ |
| ```--docker``` | _Intern: Sperre Pfad und Port auf Docker-Standardwerte (um falsche Einstellungen zu vermeiden)_ |

## Credits

* [mmarquezs](https://github.com/mmarquezs/)
* [Gutz-Pilz](https://github.com/Gutz-Pilz/)
* [zapp-brannigan](https://github.com/zapp-brannigan/)
* [JetBrains PyCharm](https://www.jetbrains.com/?from=RSScrawler)
