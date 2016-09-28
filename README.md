#  RSScrawler - Version 2.0.0
Projekt von [RiX](https://github.com/rix1337/RSScrawler/commits)

RSScrawler durchsucht MB/SJ nach in .txt Listen hinterlegten Titeln und reicht diese im .crawljob Format an JDownloader weiter.

Zum **automatischen Lösen von Captchas** empfiehlt sich [9kw.eu](https://www.9kw.eu/register_87296.html)!

**Den JDownloader betreffende Probleme (ReCaptcha benötigt Browserfenster, Link ist angeblich offline, etc.) müssen in dessen Entwicklerforum gelöst werden.**

**Um das Projekt zu erweitern muss entsprechender Code als Pull-Request eingereicht werden! Issues dienen nur der Fehlermeldung.**

## Credits:
[dmitryint](https://github.com/dmitryint/RSScrawler/) (im Auftrag von [rix1337](https://github.com/rix1337))

[zapp-brannigan](https://github.com/zapp-brannigan/own-pyload-plugins/blob/master/hooks/MovieblogFeed.py)

[Gutz-Pilz](https://github.com/Gutz-Pilz/pyLoad-stuff/blob/master/SJ.py)

[bharnett](https://github.com/bharnett/Infringer/blob/master/LinkRetrieve.py)

## Bedanken:

**Das Projekt nimmt keine Spenden an.** Um sich für den aktuellen Stand von RSScrawler zu bedanken können Bitcoin gesendet werden. Features und Support werden hier nicht verkauft.

[Danke!](https://github.com/rix1337/thanks)

## TLDR:

1. Aktiviere Ordnerüberwachung im JDownloader 2
2. Installiere Python 2.7 und die Zusatzpakete: docopt, feedparser, BeautifulSoup, pycurl, lxml, requests, cherrypy
3. Starte RSScrawler einmalig, dies erstellt den Einstellungen-Ordner inklusive aller benötigter Dateien
4. Passe den ```jdownloaderpath```, sowie ```port``` in der ```RSScrawler.ini``` an.
5. Nutze RSScrawler. Alle Einstellungen sind nun unter dem gewählten Port und der IP des Rechners verfügbar!

Optional stehen [fertige Builds für docker, Windows und Synology](#releases) zur Verfügung!

Für OS X bitte beachten:

Die fehlenden Module müssen mit:

```python -m pip install [MODULNAME]``` installiert werden

## RSScrawler starten:

```python RSScrawler.py``` führt RSScrawler aus

## Startparameter:

  ```--testlauf```                Einmalige Ausführung von RSScrawler

  ```--port=<PORT>```             Legt den Port des Webservers fest
  
  ```--jd-pfad=<JDPFAD>```        Legt den Pfad von JDownloader fest (nützlich bei headless-Systemen), diese Option darf keine Leerzeichen enthalten

  ```--log-level=<LOGLEVEL>```    Legt fest, wie genau geloggt wird (CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET )

## Einstellungen:
*Die RSScrawler.ini liegt im ```Einstellungen``` Ordner und wird (inklusive der Listen) beim ersten Start automatisch generiert. Danach ist der RSScrawler noch nicht einsatzbereit.*

**Zunächst muss der JDownloader-Pfad muss hinterlegt werden, ansonsten beendet sich RSScrawler automatisch mit einem Warnhinweis!**

**Der JDownloader-Pfad und der Port des Webserver kann daher per Startparameter festgelegt werden**

Sollte kein unmittelbarer Zugriff auf die RSScrawler.ini möglich sein, lässt sich RSScrawler mit den Parametern ```--jd-pfad``` und ```--port``` korrekt starten. Hierbei werden die entsprechenden Einträge der RSScrawler.ini ignoriert.

Für Pfade mit Leerzeichen kann nicht der ```--jd-pfad``` Parameter verwendet werden. Diese müssen direkt in der RSScrawler.ini hinterlegt werden.

Alle weiteren Einstellungen können nach Belieben über den Webserver angepasst werden und sind dort hinreichend erklärt. Ein direktes Bearbeiten der Einstellungen und Listen ist möglich, aber nicht empfehlenswert.

## Releases:

Plattform | Autor | Status
---|---|---
[Windows](https://github.com/rix1337/RSScrawler/releases) | [rix1337](https://github.com/rix1337) | Offiziell
[Docker](https://hub.docker.com/r/rix1337/docker-rsscrawler/) | [rix1337](https://github.com/rix1337) | Offiziell
[Synology](https://spk.netzbaer.de/rsscrawler) | [neutron666](https://github.com/neutron666) | Inoffiziell*

*eventuell nicht auf aktuellem Stand