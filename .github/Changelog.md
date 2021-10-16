### Installation und Update:

`pip install -U feedcrawler`

- Leert unbedingt nach jedem Update den Browser-Cache!

- Punkte, die den [FeedCrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-FeedCrawler-Sponsors-Helper) betreffen, werden erst nach dessen Update aktiv.

---

### Changelog:
- **11.0.15** Release der neuen Version 2.0.0
  des [FeedCrawler Sponsors Helpers](https://github.com/rix1337/RSScrawler/wiki/5.-FeedCrawler-Sponsors-Helper)
  - Der Helper basiert ab sofort auf Chromium, statt Firefox.
  - Damit werden Captchas auf DW wieder automatisch und zuverlässig gelöst.
  - Außerdem wurden alle Scripte aktualisiert um stabiler zu laufen.
  - Es sind folgende Anpassungen der Docker Konfiguration des Helpers sinnvoll:
    - das `--privileged`-Flag entfernen
    - das `--restart unless-stopped`-Flag ergänzen
- **11.0.15** Anpassung der Startseite des [FeedCrawler Sponsors Helpers](https://github.com/rix1337/RSScrawler/wiki/5.-FeedCrawler-Sponsors-Helper)
  - Die Seite aktualisiert ab sofort zweimalig je Minute, anstatt einmalig.
  - Wurde ein Captcha nicht gelöst, öffnet der Helper die Seite erneut, statt abzuwarten.
- **11.0.14** Bugfixes
- **11.0.13** Fix: Exception bei Hinzufügen von DW-Links über
  den [FeedCrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-FeedCrawler-Sponsors-Helper)
- **11.0.13** Fix: Exception bei fehlenden IMDb-Votes
- **11.0.13** Update auf Bootstrap Icons 1.6.0
- **11.0.13** Update auf Bootstrap 5.1.3
- **11.0.12** IMDb Schreibweise korrigiert
- **11.0.11** Fix: Exception in IMDb-Suche
- **11.0.10** Fix: Exception in IMDb-Suche
- **11.0.10** Update auf Bootstrap 5.1.1
- **11.0.9** Update auf aktuelle [IMDbPY](https://imdbpy.github.io/) um lokalisierte Titel in Ombi zu laden / Fix #526
- **11.0.9** Automatisierter Releaseprozess
  über [Github Actions](https://github.com/rix1337/FeedCrawler/actions/workflows/CreateRelease.yml)
- **11.0.8** Integration von [IMDbPY](https://imdbpy.github.io/) um IMDb deutlich stabiler zu parsen
- **11.0.7** Fix #523 Danke @9Mad-Max5
- **11.0.6** Fehlerbehebung im Handling von Episodenpaketen
  - Nicht benötigte Episoden werden wieder korrekt entfernt
  - Das hinzugefügte Paket enthält die verbliebenen Episoden im Namen
- **11.0.5** Update auf Bootstrap 5.0.2
- **11.0.5** Fix beim Abruf von Filmtiteln durch Ombi
- **11.0.5** Fix der doppelten Logeinträge #519 Danke @jankete
- **11.0.4** Fix #518 Danke @jankete
- **11.0.3** Bugfixes #517
- **11.0.2** Bugfixes #516
- **11.0.1** Bugfixes #515
- **11.0.0**  Update des [FeedCrawler Sponsors Helpers](https://github.com/rix1337/RSScrawler/wiki/5.-FeedCrawler-Sponsors-Helper) auf Version 1.0.4
  - Verbessertes Laden neuer Releases
  - Update des Anti-Captcha-Addons auf v.0.56 (mit verbesserter hCaptcha-Erkennung)
- **11.0.0** **Großes Refactoring**: Verwendung globaler Variablen für wesentliche Informationen (erhöht die Pflegbarkeit des Codes deutlich)
- **11.0.0** **[FlareSolverr](https://github.com/FlareSolverr/FlareSolverr)-Integration** zur Umgehung von Cloudflare-Blockaden
  - Aufgrund der erhöhten Komplexität entfällt damit die direkte Integration von Proxys im FeedCrawler. [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) soll in Zukunft HTTP-Proxies unterstützen.
  - [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) muss lokal verfügbar sein
  - [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) wird nur verwendet, sofern eine CloudFlare-Blockade erkannt wurde
  - [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) ist nicht immer in der Lage, die Blockade zu umgehen. Ggf. muss ein Captcha-Löser im FlareSolverr konfiguriert werden um die Umgehung zu verbessern.
- **11.0.0** Update von Bootstrap auf stabile v.5.0.1 / Bootstrap Icons auf stabile v.1.5.0
- **11.0.0** Dependencies entfernt: cloudscraper, feedparser
- **11.0.0** DD-Feedsuche entfernt
