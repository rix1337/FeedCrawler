#  RSScrawler

RSScrawler automatisiert bequem das Hinzufügen von Links für den JDownloader.

[![PyPI version](https://badge.fury.io/py/rsscrawler.svg)](https://badge.fury.io/py/rsscrawler)
[![Chat aufrufen unter https://gitter.im/RSScrawler/Lobby](https://badges.gitter.im/RSScrawler/Lobby.svg)](https://gitter.im/RSScrawler/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Build Status](https://travis-ci.org/rix1337/RSScrawler.svg?branch=master)](https://travis-ci.org/rix1337/RSScrawler)
[![GitHub license](https://img.shields.io/github/license/rix1337/RSScrawler.svg)](https://github.com/rix1337/RSScrawler/blob/master/LICENSE.md)
[![GitHub issues](https://img.shields.io/github/issues/rix1337/RSScrawler.svg)](https://github.com/rix1337/RSScrawler/issues)
[![GitHub stars](https://img.shields.io/github/stars/rix1337/RSScrawler.svg)](https://github.com/rix1337/RSScrawler/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/rix1337/RSScrawler.svg)](https://github.com/rix1337/RSScrawler/network)

##  Vorraussetzungen

* [Python ab 3.5 empfohlen (2.7 wird noch unterstützt)](https://www.python.org/downloads/)
* [pip, falls nicht vorhanden](https://pip.pypa.io/en/stable/installing/)
* [JDownloader 2 (benötigt JRE)](http://www.jdownloader.org/jdownloader2)
* [Zusatzpakete](https://github.com/rix1337/RSScrawler/blob/master/requirements.txt)
* [Optional, aber empfohlen: node.js](https://nodejs.org/en/)

## Installation

```pip install rsscrawler```

Hinweise zur manuellen Installation und Einrichtung finden sich im [Wiki](https://github.com/rix1337/RSScrawler/wiki)!

## Bekannte Fehler

Die folgenden Fehler lassen sich nicht im Code von RSScrawler beheben, sondern nur auf Systemseite:

* Kommt es direkt beim Programmstart zu einem _UnicodeEncodeError_ einfach `export PYTHONIOENCODING=utf-8` vor Programmstart ausführen
* Python _Levenshtein_ wird aussschließlich in der Suche per Webinterface/API von der _fuzzywuzzy_ Bibliothek verwendet, die notfalls auf eine langsamere Alternative ausweicht. Die Warnung beim Start, dass das Modul fehlt, lässt sich optional per `pip install python-Levenshtein` vermeiden.
* Fehler im Installationsprozess per _pip_ deuten auf fehlende Compiler im System hin. Meist muss ein Zusatzpaket nachinstalliert werden (Beispielsweise die [VS C++ Build Tools](https://visualstudio.microsoft.com/de/visual-cpp-build-tools/) für Windows oder libffi per `apt-get install libffi-dev` für den Raspberry Pi).

## Update

```pip install -U rsscrawler```

## Sicherheitshinweis

Der Webserver sollte nie ohne adequate Absicherung im Internet freigegeben werden. Dazu empfiehlt sich ein Reverse-Proxy bspw. über nginx mit Letsencrypt (automatisches, kostenloses HTTPs-Zertifikat), HTTPauth (Passwortschutz - Nur sicher über HTTPs!) und fail2ban (limitiert falsche Logins pro IP).

## Starten

```rsscrawler``` in der Konsole (Python muss im System-PATH hinterlegt sein)

## Startparameter

  ```--config="<CFGPFAD>"```      Legt den Ablageort für Einstellungen und Logs fest

  ```--testlauf```                Einmalige Ausführung von RSScrawler
  
  ```--docker```                  Sperre Pfad und Port auf Docker-Standardwerte (um falsche Einstellungen zu vermeiden)

  ```--port=<PORT>```             Legt den Port des Webservers fest
  
  ```--jd-pfad="<JDPFAD>"```      Legt den Pfad von JDownloader fest um nicht die RSScrawler.ini direkt bearbeiten zu müssen

  ``` --cdc-reset```              Leert die CDC-Tabelle (Feed ab hier bereits gecrawlt) vor dem ersten Suchlauf

  ```--log-level=<LOGLEVEL>```    Legt fest, wie genau geloggt wird (CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET)

## Credits

* [mmarquezs](https://github.com/mmarquezs/)
* [Gutz-Pilz](https://github.com/Gutz-Pilz/)
* [zapp-brannigan](https://github.com/zapp-brannigan/)
