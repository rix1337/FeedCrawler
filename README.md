#  RSScrawler - Version 1.6.7
Projekt von https://github.com/rix1337

RSScrawler durchsucht MB/SJ nach in .txt Listen hinterlegten Titeln und reicht diese im .crawljob Format an JDownloader weiter.

Zum **automatischen Lösen von Captchas** empfiehlt sich [9kw.eu](https://www.9kw.eu/register_87296.html)!

**Den JDownloader betreffende Probleme (ReCaptcha benötigt Browserfenster, Link ist angeblich offline, etc.) müssen in dessen Entwicklerforum gelöst werden.**

**Um das Projekt zu erweitern muss entsprechender Code als Pull-Request eingereicht werden! Issues dienen nur der Fehlermeldung.**

## Enthaltener Code:
https://github.com/dmitryint (im Auftrag von https://github.com/rix1337)

https://github.com/zapp-brannigan/own-pyload-plugins/blob/master/hooks/MovieblogFeed.py

https://github.com/Gutz-Pilz/pyLoad-stuff/blob/master/SJ.py

https://github.com/bharnett/Infringer/blob/master/LinkRetrieve.py

## Bitcoin senden:

32TwQSAaRjeVAN4FVs7ZKiyAKtTepcmY26

![32TwQSAaRjeVAN4FVs7ZKiyAKtTepcmY26](https://raw.githubusercontent.com/rix1337/donate/master/donate.png "32TwQSAaRjeVAN4FVs7ZKiyAKtTepcmY26")

## TLDR:

1. Aktiviere Ordnerüberwachung im JDownloader 2
2. Installiere Python 2.7 und die Zusatzpakete: docopt, feedparser, BeautifulSoup, pycurl, lxml, requests
3. Starte RSScrawler einmalig, dies erstellt den Einstellungen-Ordner inklusive aller benötigter Dateien
4. Passe die ```Einstellungen.ini``` und die .txt Listen komplett an.
5. Nutze RSScrawler!

Optional stehen [fertige Builds für docker, Windows und Synology](#windows-build) zur Verfügung!

Für Mac OS X/macOS bitte beachten:

Die fehlenden Module müssen mit:

```python -m pip install [MODULNAME]``` installiert werden

## RSScrawler starten:

```python RSScrawler.py``` führt RSScrawler aus

## Startparameter:

  ```--testlauf```                Einmalige Ausführung von RSScrawler
  
  ```--jd-pfad=<JDPFAD>```        Legt den Pfad von JDownloader fest (nützlich bei headless-Systemen), diese Option darf keine Leerzeichen enthalten

  ```--log-level=<LOGLEVEL>```    Legt fest, wie genau geloggt wird (CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET )

## Einstellungen:
*Die RSScrawler.ini liegt im ```Einstellungen``` Ordner und wird (inklusive der Listen) beim ersten Start automatisch generiert*

**Der JDownloader-Pfad muss korrekt hinterlegt werden!**
Für Pfade mit Leerzeichen kann nicht der jd-pfad Parameter verwendet werden. Pfade mit Leerzeichen müssen direkt in der RSScrawler.ini hinterlegt werden.

Zur besseren Übersicht und Automatisierbarkeit (bspw. durch Filebot) werden Releases explizit in das RSScrawler-Verzeichnis heruntergeladen. Über enforcedl gefundene, zweisprachige Releases landen davon getrennt im Remux-Verzeichnis (zum automatischen Remuxen).

Alle weiteren Einstellungen können nach Belieben angepasst werden und sind hinreichend erklärt. Im Folgenden nur einige wichtige Hinweise:

### Die Listen (MB_Filme, MB_Serien, SJ_Serien, SJ_Serien_Regex):

1. ```MB_Filme.txt``` enthält pro Zeile den Titel eines Films (Film Titel), um auf MB nach Filmen zu suchen
2. ```MB_Staffeln.txt``` enthält pro Zeile den Titel einer Serie (Serien Titel), um auf MB nach kompletten Staffeln zu suchen
3. ```SJ_Serien.txt``` enthält pro Zeile den Titel einer Serie (Serien Titel), um auf SJ nach Serien zu suchen
4. ```SJ_Serien_Regex.txt``` enthält pro Zeile den Titel einer Serie in einem speziellen Format, wobei die Filter ignoriert werden:

```
DEUTSCH.*Serien.Titel.*.S01.*.720p.*-GROUP sucht nach Releases der Gruppe GROUP von Staffel 1 der Serien Titel in 720p auf Deutsch

Serien.Titel.* sucht nach allen Releases von Serien Titel (nützlich, wenn man sonst HDTV aussortiert)

Serien.Titel.*.DL.*.720p.* sucht nach zweisprachigen Releases in 720p von Serien Titel

ENGLISCH.*Serien.Titel.*.1080p.* sucht nach englischen Releases in Full-HD von Serien Titel

(?!(Diese|Andere)).*Serie.*.DL.*.720p.*-(GROUP|ANDEREGROUP) sucht nach Serie (aber nicht Diese Serie oder Andere Serie), zweisprachig und in 720p und ausschließlich nach Releases von GROUP oder ANDEREGROUP
```

Generell sollten keine Sonderzeichen in den Listen hinterlegt werden!

**Die Listen werden automatisch mit Platzhalterzeilen generiert und sind danach anzupassen. Platzhalter verhindern, dass unerwünschte Releases beim ersten Start hinzugefügt werden.**

## [MB]:

### crawl3d:

Wenn aktiviert sucht das Script nach 3D Releases (in 1080p), unabhängig von der oben gesetzten Qualität. Standartmäßig werden HOU-Releases aussortiert (ignore).

### enforcedl:

Wenn aktiviert sucht das Script zu jedem nicht-zweisprachigen Release (kein DL-Tag im Titel) ein passendes Release in 1080p mit DL Tag.
Findet das Script kein Release wird dies im Log vermerkt. Bei der nächsten Ausführung versucht das Script dann erneut ein passendes Release zu finden. Diese Funktion ist nützlich um (durch späteres Remuxen) eine zweisprachige Bibliothek in 720p zu halten.

### crawlseasons:

Komplette Staffeln von Serien landen zuverlässiger auf MB als auf SJ. Diese Option erlaubt die entsprechende Suche.

## [SJ]:

### regex:

Wenn aktiviert werden die Serien aus der SJ_Serien_Regex.txt gesucht

## Windows Build:
https://github.com/rix1337/RSScrawler/releases

## Docker Container:
https://github.com/rix1337/docker-rsscrawler

## Inoffizielles Synology Addon-Paket (Veraltet):
https://spk.netzbaer.de/rsscrawler
