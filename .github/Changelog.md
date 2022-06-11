### Installation und Update:

`pip install -U feedcrawler`

---

### Changelog FeedCrawler:

- **15.0.0** DW Web-Suche hinzugefügt.
- **15.0.0** Korrektur in der Prüfung der Verbindung zu My JDownloader beim Start
- **15.0.0** Interne Paketstruktur erneut überarbeitet.
- **15.0.0** Der interne Request Handler unterstützt nun auch HTTP-Authentifizierung per URL und Proxies
  (derzeit ungenutzt).

### Changelog [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper):

Punkte, die den [FeedCrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-FeedCrawler-Sponsors-Helper)
betreffen, werden erst nach dessen Update aktiv.

- **6.0.0** Der Helper nutzt analog zum FeedCrawler weniger externe Python-Dependencies
  (`docopt`, `flask` und `waitress` wurden entfernt).
- **5.3.0** Der Helper nutzt jetzt [Click'n'Load2FeedCrawler](https://github.com/rix1337/ClickNLoad2FeedCrawler)
  in Version 2.0.1.
- **5.3.0** Der Helper nutzt jetzt Chrome (Version 102) im Dark Mode.
- **5.2.0** Der Helper funktioniert jetzt in Kombination mit aktivem Benutzernamen/Passwort im FeedCrawler,
  siehe [Wiki](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper#passwortgesch%C3%BCtzter-feedcrawler).
- **5.1.0** Das interne Webinterface nutzt ab sofort [petite-vue](https://github.com/vuejs/petite-vue).
- **5.0.0** Basiert ab sofort auf eigenem Basis-Image (Ubuntu 22.04 und Google Chrome 100)
    - Die Funktionalität entspricht der Vorversion inklusive Zugriff per VNC/Web-Browser.
    - Die Parameter `--shm-size 2g` und `--restart unless-stopped` sind nicht mehr notwendig.
    - Mit dem `--privileged`-Parameter kann ab sofort die `--no-sandbox`-Warnung in Chrome deaktiviert werden.
