### Installation und Update:

`pip install -U feedcrawler`

---

### Changelog FeedCrawler:

- **14.3.0** Bugfix im Aufbau der Direktverbindung per IP zum JDownloader.
- **14.3.0** Synchronisiere Verbindung zum JDownloader zwischen Feed-Suche, Web-Interface und Paket-Überwachungsjob.
- **14.3.0** Optionale Auto-Update-Funktion für den JDownloader, die am Ende jedes Suchlaufes durchgeführt wird.
- **14.3.0** Reaktiviere JDownloader Update-Funktion im Web-Interface.
- **14.3.0** Wähle JDownloader Gerät nur dann automatisch, wenn nicht bereits ein Gerätename in den Einstellungen
  definiert ist.
- **14.3.0** Gleiche Ausgabe der Dateigrößen aus Feeds und den JDownloader-Informationen im Webinterface an.
- **14.2.8** Anzahl der maximalen Fehlversuche pro Paket im 
  [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper) sind jetzt
  konfigurierbar.
- **14.2.8** Schätze Episodengröße auf SF, auch wenn mehrere Episoden in einem Release vorhanden sind.
- **14.2.8** Bugfixes in Log-Meldung beim Start und dem Web-Interface
- **14.2.7** Schätze Episodengröße auf SF, auch wenn für das Release die Anzahl der Episoden nicht bekannt ist.
- **14.2.7** Möglicher Bugfix in Verbindung zum JDownloader
- **14.2.6** Nutze [FormKit](https://formkit.com/) für bessere Validierung der Web-Suche und Suchlisten.
- **14.2.6** Bugfix (#639): Web-Interface beachtet wieder die gesetzte Paketanzahl pro Seite
- **14.2.5** Weitere Verbesserungen in den Telegram-Benachrichtigungen
- **14.2.5** Weitere Verbesserungen in [FormKit](https://formkit.com/)-Nutzung
- **14.2.4** Nutze [FormKit](https://formkit.com/) für bessere Validierung der Einstellungen
- **14.2.4** Erkenne ob NK den Feed-Abruf blockiert.
- **14.2.4** Versuche beim Start 5x eine Verbindung zum JDownloader aufzubauen (mit 60 Sekunden Wartezeit),
  bevor der Start scheitert.
- **14.2.3** Bugfix (#635)
- **14.2.2** Für SF werden jetzt Release-Größe und IMDb-Poster erkannt, wenn verfügbar.
  - Bei Episoden wird anhand der Episodenanzahl die Release-Größe anhand der Staffel gemittelt.
  - Nicht jede Serie verfügt auf SF über eine IMDb-ID, weswegen Poster nur teilweise verfügbar sind.
  - SJ/DJ bieten weder Release-Größe, noch IMDb-IDs für den Poster-Abruf
- **14.2.2** Vereinheitlichte Schreibweise der Release-Größen.
- **14.2.1** Bugfix
- **14.2.0** Benachrichtigungen, Web-Interface und Log beinhalten Link zur Release-Quelle
- **14.2.0** Benachrichtigungen, Web-Interface und Log beinhalten die Release-Größe, wo verfügbar
- **14.2.0** Telegram Benachrichtigungen enthalten IMDb-Poster, wo verfügbar
- **14.1.3** Verhindere Incomplete-Read-Fehler (#627)
- **14.1.3** Erkenne und verhindere Verarbeitung von Ombi-Anfragen ohne IMDb-ID
- **14.1.2** Detailverbesserungen im Web-Interface, insbesondere der Log-Darstellung
- **14.1.2** Überarbeitete interne Paketstruktur
- **14.1.1** Bugfix im Log bei nicht erfolgreichem Sponsors Helper
- **14.1.0** Refactoring im Frontend um mehr Bootstrap Standards zu nutzen (sowie Sass)
- **14.1.0** Erhöhte Stabilität in der Verbindung zum JDownloader
- **14.0.4** Die Wartezeit (vormals SF/FF-Intervall) gilt jetzt auch für SJ/DJ.
    - Die Ban-Erkennung von SJ/DJ ist mittlerweile ähnlich streng wie bei SF/FF.
    - Die Einstellung wurde von SF/FF in die allgemeinen Einstellungen verschoben.
- **14.0.4** Verbesserungen beim Setzen und Auslesen der Ombi/Overseerr-URL (#622)
- **14.0.4** Bugfix in der Episodensuche per Ombi (#622)
- **14.0.4** Bugfix in der Staffelsuche auf SF (#622)
- **14.0.4** Bugfixes im Informationsabruf aus der IMDb (#622)
- **14.0.3** Erhöhte Stabilität in der Verbindung zum JDownloader
    - Docker-interne IP-Adressen werden bei der Verbindung ignoriert
    - Für alle anderen IP-Adressen wurde der Timeout erhöht
    - So kommt es zu weniger Timeouts und Verbindungsabbrüchen
- **14.0.3** Der Sponsors-Helper-Click'n'Load funktioniert wieder.
- **14.0.2** Lösche Paket
  durch [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper) nach
  drei Fehlversuchen.
- **14.0.1** Bugfixes (#614)
- **14.0.0** Die Overseerr-Suche für Serien geht jetzt Staffelweise vor.
- **14.0.0** Das Passwort für das Web-Interface muss neu vergeben werden, sofern zuvor eines genutzt wurde.
- **14.0.0** Entfernung der folgenden Dependencies:
    - docopt (zugunsten der Python-internen argparse-Bibliothek)
    - flask (zugunsten der weniger komplexen bottle-Bibliothek)
    - passlib (zugunsten der sichereren scrypt-Methode der pycryptodomex-Bibliothek)
    - python-dateutil (zugunsten einer eigenen Implementierung auf Basis der Python-internen datetime-Bibliothek)
    - requests (zugunsten einer eigenen Implementierung auf Basis der Python-internen urllib-Bibliothek)
    - simplejson (zugunsten der Python-internen json-Bibliothek)
    - waitress (zugunsten einer eigenen Implementierung auf Basis der Python-internen wsgiref-Bibliothek)

### Changelog [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper):

Punkte, die den [FeedCrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-FeedCrawler-Sponsors-Helper)
betreffen, werden erst nach dessen Update aktiv.

- **5.2.0** Der Helper funktioniert jetzt in Kombination mit aktivem Benutzernamen/Passwort im FeedCrawler,
  siehe [Wiki](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper#passwortgesch%C3%BCtzter-feedcrawler)
  .
- **5.1.0** Das interne Webinterface nutzt ab sofort [petite-vue](https://github.com/vuejs/petite-vue).
- **5.0.0** Basiert ab sofort auf eigenem Basis-Image (Ubuntu 22.04 und Google Chrome 100)
    - Die Funktionalität entspricht der Vorversion inklusive Zugriff per VNC/Web-Browser.
    - Die Parameter `--shm-size 2g` und `--restart unless-stopped` sind nicht mehr notwendig.
    - Mit dem `--privileged`-Parameter kann ab sofort die `--no-sandbox`-Warnung in Chrome deaktiviert werden.
