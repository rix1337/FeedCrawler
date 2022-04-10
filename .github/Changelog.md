### Installation und Update:

`pip install -U feedcrawler`

---

### Changelog FeedCrawler:

- **13.1.0** Integration von [Overseerr](https://overseerr.dev/) als bessere Alternative zu [Ombi](https://ombi.io/)
  - Ombi ist über die Jahre imperformant und unzuverlässig geworden und steht ab sofort nicht mehr im Fokus dieses Projektes.
  - Overseerr bietet eine deutlich zuverlässigere und schnellere Basis für Medienserver-Anfragen
  - Ein Wechsel von Ombi zu Overseerr wird empfohlen.
- **13.0.8** Bevorzuge SF-Web-Suche in Ombi-Anbindung
- **13.0.7** Integration der SF-Web-Suche
- **13.0.7** Fehlerbehebung in der SF-Feed-Suche
- **13.0.7** Verbesserte Erkennung von Blockaden auf SJ/DJ
- **13.0.6** Dependency Flask-CORS zugunsten eigener Implementierung entfernt
- **13.0.6** Dependency Rapidfuzz zugunsten eigener Implementierung entfernt
- **13.0.6** Detailverbesserungen im Web-Interface (RegEx-Hilfe/Seitenstatus)
- **13.0.5** Fehlerbehebung im Laden der Suchlisten
- **13.0.5** RegEx-Hilfe überarbeitet
- **13.0.5** Verbesserungen in der Web-Suche
- **13.0.5** Fehlgeschlagene Downloads können jetzt zurückgesetzt werden
- **13.0.4** Die Web-Suche zeigt die Ergebnisse von schnell durchsuchbaren Seiten schon an, 
      während langsame Seiten noch laden.
- **13.0.4** Ladehinweis für Suchlisten/Einstellungen ergänzt
- **13.0.4** Fehlerbehebungen in der SJ-Web-Suche
- **13.0.4** Weitere Fehlerbehebungen in der Ombi-Anbindung (#600)
- **13.0.3** Fehlerbehebung im [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper),
      wenn ein Prefix für das Web-Interface genutzt wird.
- **13.0.2** Fehlerbehebung in der Ombi-Anbindung #600 (Danke @jankete)
- **13.0.1** Detailverbesserungen
    - Verhindere vertikales Scrollen im Log
    - Redundanzen im Vue-Router entfernt
    - FF-Zeitstempel in der Hilfe werden menschenlesbar ausgegeben.
    - Links für Tampermonkey-Scripte korrigiert
    - Affiliate-Links korrigiert
    - Option zum geschlossen halten des My JDownloader Tabs aus Performancegründen entfernt
- **13.0.0** Migration des AngularJS Frontends zu [Vue.js 3](https://vuejs.org/)
    - AngularJS ist seit Ende 2021 [End-of-Life](https://docs.angularjs.org/misc/version-support-status) und wird nicht
      mehr aktiv gepflegt.
    - Vue.js ist ein modernes und aktiv gepflegtes Framework für Single-Page-Applications.
    - Vue.js setzt in Version 3 auf den pfeilschnellen `vite`-Compiler, der für `dev` und `build` wesentlich schneller
      als `webpack` ist.
    - Danke an alle [Sponsoren](https://github.com/sponsors/rix1337/)! Ohne eure Unterstützung wäre die technische
      Pflege des FeedCrawlers nicht möglich.
    - Der Wechsel der Frameworks war nicht zwingend notwendig, macht den FeedCrawler jedoch zukunftssicherer und das
      Frontend spürbar schneller.
    - Bei Installation per Docker, pip oder Windows Exe ist nichts weiter zu tun. Das Frontend muss jedoch vor der
      manuellen Installation per setup.py bereits per "npm run build" im Ordner `feedcrawler/web` kompiliert worden
      sein.
    - Die Migration umfasst mehr als [5000 Zeilen Code](https://github.com/rix1337/FeedCrawler/pull/594/files). Nutzt
      daher im Fehlerfall ein aussagekräftiges [Issue](https://github.com/rix1337/FeedCrawler/issues/new), statt einer
      Wortmeldung im Gitter.
- **13.0.0** Fix CVE-2022-24761 (HTTP Request Smuggling in waitress)
- **13.0.0** PL entfernt
- **13.0.0** Das offizielle [Docker-Image](https://registry.hub.docker.com/r/rix1337/docker-feedcrawler) nutzt jetzt
  Python 3.9

### Changelog [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper):

Punkte, die den [FeedCrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-FeedCrawler-Sponsors-Helper)
betreffen, werden erst nach dessen Update aktiv.

- **5.0.0** Basiert ab sofort auf eigenem Basis-Image (Ubuntu 22.04 und Google Chrome 100)
  - Die Funktionalität entspricht der Vorversion inklusive Zugriff per VNC/Web-Browser.
  - Die Parameter `--shm-size 2g` und `--restart unless-stopped` sind nicht mehr notwendig.
  - Mit dem `--privileged`-Parameter kann ab sofort die `--no-sandbox`-Warnung in Chrome deaktiviert werden.
- **4.0.3** Entschlüssele PL-Links automatisch per Click'n'Load oder DLC, wenn der FeedCrawler daran gescheitert ist.
- **4.0.2** Der AntiGateHandler entschlüsselt nun die DLC-Datei, sofern der Click'n'Load-Button fehlt.
- **4.0.1** Der lokale HTTP-Proxy läuft ab sofort dauerhaft.
    - Die Zugangsdaten werden weiterhin bei jedem Start zufallsgeneriert.
    - Der Proxy blockiert alle Domains außer denen, die für das Lösen von CutCaptchas notwendig sind.
- **4.0.1** Es wird kein Timeout beim Lösen der CutCaptchas mehr forciert.
- **4.0.0** Click'n'Load wird nicht mehr im Chrome gelöst (da langsam und fehleranfällig), sondern direkt im
  AntiGateHandler. Danke an das JDownloader-Team für die Umsetzungsidee!
- **4.0.0** Prüfe anhand des Links, ob ein Passwort für den AntiGateTask gesetzt werden muss, um den korrekten
  AntiGateTask zu starten.
- **4.0.0** Prüfe anhand des Links, ob überhaupt ein Captcha gelöst werden muss. Dies verhindert, dass ein AntiGateTask
  für nicht geschützte Links erzeugt wird.
- **4.0.0** Der lokale HTTP-Proxy wird separat vom AntiGateHandler gestartet (verhindert, dass der Proxy im AntiGateTask
  nicht zur Verfügung steht). 
