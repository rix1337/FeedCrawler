<img src="rsscrawler.png" align="left" height="64" width="64">

#  RSScrawler

RSScrawler durchsucht vordefinierte Seiten nach Titeln und reicht Links an JDownloader weiter.

## Credits

[dmitryint](https://github.com/dmitryint/) | [zapp-brannigan](https://github.com/zapp-brannigan/) | [Gutz-Pilz](https://github.com/Gutz-Pilz/) | [bharnett](https://github.com/bharnett/) | [colorlib](http://codepen.io/colorlib/) | [cbracco](http://codepen.io/cbracco/) | [jaysonwm](https://github.com/jaysonwm/) | [Itsie](https://github.com/Itsie) | [sweatcher](https://github.com/sweatcher)
---|---|---|---|---|---|---|---|---
[Portierung](https://github.com/dmitryint/RSScrawler)* | [Suche](https://github.com/zapp-brannigan/own-pyload-plugins/blob/master/hooks/MovieblogFeed.py) | [Suche](https://github.com/Gutz-Pilz/pyLoad-stuff/blob/master/SJ.py) | [Crawljobs](https://github.com/bharnett/Infringer/blob/master/LinkRetrieve.py) | [HTML](http://codepen.io/colorlib/pen/KVoZyv) | [Tooltips](http://codepen.io/cbracco/pen/qzukg) | [Buttons](https://github.com/jaysonwm/popupmodal.js) | [Ubuntu/Debian Setup](https://github.com/rix1337/RSScrawler/issues/88#issuecomment-251078409) | [Synology Setup](https://github.com/rix1337/RSScrawler/issues/7#issuecomment-271187968)

*Im Auftrag des Projekteigners

## Installation

Hinweise zur Installation und Einrichtung finden sich im [Wiki](https://github.com/rix1337/RSScrawler/wiki)!

## RSScrawler starten

```python RSScrawler.py``` führt RSScrawler aus

## Startparameter:

  ```--testlauf```                Einmalige Ausführung von RSScrawler
  
  ```--docker```                  Sperre Pfad und Port auf Docker-Standardwerte (um falsche Einstellungen zu vermeiden)

  ```--port=<PORT>```             Legt den Port des Webservers fest
  
  ```--jd-pfad="<JDPFAD>"```      Legt den Pfad von JDownloader fest um nicht die RSScrawler.ini direkt bearbeiten zu müssen

  ```--log-level=<LOGLEVEL>```    Legt fest, wie genau geloggt wird (CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET )
