### Installation und Update:

`pip install -U feedcrawler`

- Leert unbedingt nach jedem Update den Browser-Cache!

- Punkte, die  den [FeedCrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-FeedCrawler-Sponsors-Helper)  betreffen, werden erst nach dessen Update aktiv.

---

### Changelog FeedCrawler:

- **12.1.1** HW wieder in die Web-Suche integriert
- **12.1.0** HW wieder in die Feed-Suche integriert
- **12.0.5** "Neu laden" auf Helper-Seite funktioniert wieder.
- **12.0.4** Fix beim Bereitstellen von WW-Links
- **12.0.3** Der Helper erkennt, wenn ein Link erfolglos entschlüsselt wurde und versucht es erneut.
- **12.0.2** Fix #557 - Danke @DKeppi
- **12.0.2** Fehler bei IMDB-Eintrag ohne Jahreszahl behoben
- **12.0.1** Fix beim Erzeugen neuer FlareSolverr-Sessions für den Aufruf mit Proxy
- **12.0.0** Unterstützung für [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper) Version 3.0.0
- **12.0.0** Demaskiere FX-Links vor dem Download
- **12.0.0** Erzeuge neue FlareSolverr-Session für den Aufruf mit Proxy

### Changelog [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper):
- **3.2.4** Ab sofort werden FC-Links inklusive CutCaptcha durch den AntiGateHandler automatisch entschlüsselt:
    - Da FC-CAPTCHA eine deutsche IP-Adresse voraussetzen, wird die eigene IP-Adresse automatisch extern freigegeben.
    - Zu diesem Zweck wird für den kurzen Zeitraum der CAPTCHA-Lösung ein HTTP-Proxy im Helper gestartet.
    - Dieser muss extern per IPv4/TCP erreichbar sein (Port 33333 ist dabei fix, IPv6 ist nicht nutzbar):
       - Der HTTP-Proxy wird ausschließlich während des Lösungszeitraums gestartet, dazwischen ist Port 33333 inaktiv.
       - Port 33333 muss per Portfreigabe im Router an den Docker-Host weitergegeben (IPv4/TCP) werden.
       - Der HTTP-Proxy ist durch zufallsgenerierte Zugangsdaten ausschließlich für den einzelnen Lösungsvorgang erreichbar.
       - Die Zugangsdaten werden zu Beginn jedes Lösungsvorganges automatisch angelegt und sind danach nicht mehr gültig.
       - Die eigene IP-Adresse wird dabei dem CAPTCHA-Löser über Anti-Captcha.com kurzfristig freigegeben,
         sodass das gelöste CAPTCHA lokal für die Entschlüsselung verwendet werden kann.
       - Ein kostenpflichtiger HTTP-Proxy ist nicht notwendig.
    - Genutzt wird wie bisher der [Anti-Captcha-API-Key (das Entschlüsseln kostet ca. 0,5-1 ct pro CAPTCHA)](http://getcaptchasolution.com/zuoo67f5cq)
    - Das Lösen der Captchas und die Implementierung im Helpers ist brandneu - Fehler sind also erwartbar.
    - Es werden maximal 10 CAPTCHAs pro Stunde auf diesem Weg entschlüsselt um einen Ban der eigenen IP-Adresse zu vermeiden.
