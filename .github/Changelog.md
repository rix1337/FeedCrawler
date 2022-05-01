### Installation und Update:

`pip install -U feedcrawler`

---

### Changelog FeedCrawler:

- **14.0.3** Erhöhte Stabilität in der Verbindung zum JDownloader
    - Docker-interne IP-Adressen werden bei der Verbindung ignoriert
    - Für alle anderen IP-Adressen wurde der Timeout erhöht
    - So kommt es zu weniger Timeouts und Verbindungsabbrüchen
- **14.0.3** Der Sponsors-Helper-Click'n'Load funktioniert wieder.
- **14.0.2** Lösche Paket durch [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper) nach drei Fehlversuchen.
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

- **5.2.0** Der Helper funktioniert jetzt in Kombination mit aktivem Benutzernamen/Passwort im FeedCrawler, siehe [Wiki](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper#passwortgesch%C3%BCtzter-feedcrawler).
- **5.1.0** Das interne Webinterface nutzt ab sofort [petite-vue](https://github.com/vuejs/petite-vue).
- **5.0.0** Basiert ab sofort auf eigenem Basis-Image (Ubuntu 22.04 und Google Chrome 100)
    - Die Funktionalität entspricht der Vorversion inklusive Zugriff per VNC/Web-Browser.
    - Die Parameter `--shm-size 2g` und `--restart unless-stopped` sind nicht mehr notwendig.
    - Mit dem `--privileged`-Parameter kann ab sofort die `--no-sandbox`-Warnung in Chrome deaktiviert werden.
