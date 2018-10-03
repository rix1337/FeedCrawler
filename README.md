#  RSScrawler

RSScrawler automatisiert bequem das Hinzufügen von Links für den JDownloader.

[![Chat aufrufen unter https://gitter.im/RSScrawler/Lobby](https://badges.gitter.im/RSScrawler/Lobby.svg)](https://gitter.im/RSScrawler/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Build Status](https://travis-ci.org/rix1337/RSScrawler.svg?branch=master)](https://travis-ci.org/rix1337/RSScrawler)[![GitHub license](https://img.shields.io/github/license/rix1337/RSScrawler.svg)](https://github.com/rix1337/RSScrawler/blob/master/LICENSE.md)
[![GitHub issues](https://img.shields.io/github/issues/rix1337/RSScrawler.svg)](https://github.com/rix1337/RSScrawler/issues)
[![GitHub stars](https://img.shields.io/github/stars/rix1337/RSScrawler.svg)](https://github.com/rix1337/RSScrawler/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/rix1337/RSScrawler.svg)](https://github.com/rix1337/RSScrawler/network)

## Credits

Die Suchfunktionen basieren auf pyLoad-Erweiterungen von:

[zapp-brannigan](https://github.com/zapp-brannigan/)

[Gutz-Pilz](https://github.com/Gutz-Pilz/pyLoad-stuff/blob/master/SJ.py)

##  Vorraussetzungen
* [Python ab 3.6 empfohlen (2.7 wird noch unterstützt)](https://www.python.org/downloads/)
* [JDownloader 2 (benötigt JRE)](http://www.jdownloader.org/jdownloader2)
* [Zusatzpakete](https://github.com/rix1337/RSScrawler/blob/master/requirements.txt)
* [Optional, aber empfohlen: node.js](https://nodejs.org/en/)

## Installation

Hinweise zur Installation und Einrichtung finden sich im [Wiki](https://github.com/rix1337/RSScrawler/wiki)!

## Sicherheitshinweis

Der Webserver sollte nie ohne adequate Absicherung im Internet freigegeben werden. Dazu empfiehlt sich ein Reverse-Proxy bspw. über nginx mit Letsencrypt (automatisches, kostenloses HTTPs-Zertifikat), HTTPauth (Passwortschutz - Nur sicher über HTTPs!) und fail2ban (limitiert falsche Logins pro IP).

## RSScrawler starten

```python RSScrawler.py``` führt RSScrawler aus

## Startparameter:

  ```--testlauf```                Einmalige Ausführung von RSScrawler
  
  ```--docker```                  Sperre Pfad und Port auf Docker-Standardwerte (um falsche Einstellungen zu vermeiden)

  ```--port=<PORT>```             Legt den Port des Webservers fest
  
  ```--jd-pfad="<JDPFAD>"```      Legt den Pfad von JDownloader fest um nicht die RSScrawler.ini direkt bearbeiten zu müssen

  ``` --cdc-reset```              Leert die CDC-Tabelle (Feed ab hier bereits gecrawlt) vor dem ersten Suchlauf

  ```--log-level=<LOGLEVEL>```    Legt fest, wie genau geloggt wird (CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET)
