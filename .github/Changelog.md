### Installation und Update:

`pip install -U feedcrawler`

- Leert unbedingt nach jedem Update den Browser-Cache!

- Punkte, die
  den [FeedCrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-FeedCrawler-Sponsors-Helper)
  betreffen, werden erst nach dessen Update aktiv.

---

### Changelog:

- **12.0.0** Update
  des [FeedCrawler Sponsors Helpers](https://github.com/rix1337/RSScrawler/wiki/5.-FeedCrawler-Sponsors-Helper) auf
  Version 3.0.1
    - Ab sofort werden FC-Links durch den AntiGateHandler automatisch entschlüsselt
    - Voraussetzung dafür ist
      ein [privater deutscher HTTP-Proxy (kostet ca. 2 € pro Monat)](https://www.highproxies.com/billing/aff.php?aff=1278)
    - Voraussetzung ist ebenfalls
      ein [Anti-Captcha-API-Key (das Entschlüsseln kostet ca. 0,5-1 ct pro CAPTCHA)](http://getcaptchasolution.com/zuoo67f5cq)
    - Das Lösen der Captchas und die Implementierung im Helpers ist brandneu - Fehler sind also erwartbar.
    - Aufgerufenen-FC-Links werden automatisch an AntiGateHandler übergeben, sofern dieser verfügbar ist.
    - Es dürfen maximal 10 Links pro Stunde auf diesem Weg entschlüsselt werden.
- **12.0.0** Demaskiere FX-Links vor dem Download
- **12.0.0** Erzeuge neue FlareSolverr-Session für den Aufruf mit Proxy
