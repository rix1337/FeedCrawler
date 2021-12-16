### Installation und Update:

`pip install -U feedcrawler`

- Leert unbedingt nach jedem Update den Browser-Cache!

- Punkte, die  den [FeedCrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-FeedCrawler-Sponsors-Helper)  betreffen, werden erst nach dessen Update aktiv.

---

### Changelog:

- **12.0.2** Fix #557 - Danke @DKeppi
- **12.0.2** Fehler bei IMDB-Eintrag ohne Jahreszahl behoben
- **12.0.1** Fix beim Erzeugen neuer FlareSolverr-Sessions für den Aufruf mit Proxy
- **12.0.0** Update des [FeedCrawler Sponsors Helpers](https://github.com/rix1337/RSScrawler/wiki/5.-FeedCrawler-Sponsors-Helper) auf  Version 3.0.2
    - Ab sofort werden FC-Links durch den AntiGateHandler automatisch entschlüsselt
    - Voraussetzung dafür ist ein [privater deutscher HTTP-Proxy (kostet ca. 2 € pro Monat)](https://www.highproxies.com/billing/aff.php?aff=1278)
    - Zweite Voraussetzung ist wie bisher ein [Anti-Captcha-API-Key (das Entschlüsseln kostet ca. 0,5-1 ct pro CAPTCHA)](http://getcaptchasolution.com/zuoo67f5cq)
    - Das Lösen der Captchas und die Implementierung im Helpers ist brandneu - Fehler sind also erwartbar.
    - Es werden maximal 10 Links pro Stunde auf diesem Weg entschlüsselt.
    - Für die Konfiguration des HTTP-Proxies sind diese [Parameter](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper#weitere-parameter) notwendig.
- **12.0.0** Demaskiere FX-Links vor dem Download
- **12.0.0** Erzeuge neue FlareSolverr-Session für den Aufruf mit Proxy
