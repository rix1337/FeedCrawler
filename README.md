#  RSScrawler

RSScrawler durchsucht vordefinierte Seiten nach Titeln und reicht Links an JDownloader weiter.

[![Chat aufrufen unter https://gitter.im/RSScrawler/Lobby](https://badges.gitter.im/RSScrawler/Lobby.svg)](https://gitter.im/RSScrawler/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

## Credits

Die Suchfunktionen basieren auf pyLoad-Erweiterungen von:

[zapp-brannigan](https://github.com/zapp-brannigan/)

[Gutz-Pilz](https://github.com/Gutz-Pilz/pyLoad-stuff/blob/master/SJ.py)

##  Vorraussetzungen
* [Python 2.7](https://synocommunity.com/package/python)
* [Java 8](https://github.com/rednoah/java-installer)
* [JDownloader 2](http://www.synology-forum.de/showthread.html?68134-JDownloader-2-%28noarch%29-Paketzentrum)
* [Optional, aber empfohlen: node.js](https://www.synology.com/de-de/dsm/packages/Node.js_v4)
* [Zusatzpakete](https://github.com/rix1337/RSScrawler/blob/master/requirements.txt)

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

  ```--log-level=<LOGLEVEL>```    Legt fest, wie genau geloggt wird (CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET )
  
  ```--ersatzblogs```            Erweitert die Suche allgemeiner Blogs auf weitere Seiten (langsamer)
  
