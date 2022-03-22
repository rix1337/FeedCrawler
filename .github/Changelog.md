### Installation und Update:

`pip install -U feedcrawler`

- Leert unbedingt nach jedem Update den Browser-Cache!

- Punkte, die den [FeedCrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-FeedCrawler-Sponsors-Helper)  betreffen, werden erst nach dessen Update aktiv.

---

### Changelog FeedCrawler:

- **13.0.0** Migration des AngularJS Frontends zu [Vue.js 3](https://vuejs.org/)
  - AngularJS ist seit Ende 2021 [End-of-Life](https://docs.angularjs.org/misc/version-support-status) und wird nicht mehr aktiv gepflegt. 
  - Vue.js ist ein modernes und aktiv gepflegtes Framework für Single-Page-Applications.
  - Der Wechsel der Frameworks war nicht zwingend notwendig, macht den FeedCrawler jedoch zukunftssicherer und das Frontend schneller.
  - Bei Installation per Docker, PIP oder Windows Exe ist nichts weiter zu tun. Das Frontend muss jedoch vor der manuellen Installation per setup.py bereits per "npm run build" im Ordner `feedcrawler/web` kompiliert worden sein.
  - Danke an alle [Sponsoren](https://github.com/sponsors/rix1337/)! Ohne eure Unterstützung wäre die technische Pflege des FeedCrawlers nicht möglich.
- **13.0.0** Fix CVE-2022-24761 (HTTP Request Smuggling in waitress)
- **13.0.0** PL entfernt
  


### Changelog [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper):

- **4.0.3** Entschlüssele PL-Links automatisch per Click'n'Load oder DLC, wenn der FeedCrawler daran gescheitert ist.
- **4.0.2** Der AntiGateHandler entschlüsselt nun die DLC-Datei, sofern der Click'n'Load-Button fehlt.
- **4.0.1** Der lokale HTTP-Proxy läuft ab sofort dauerhaft.
  - Die Zugangsdaten werden weiterhin bei jedem Start zufallsgeneriert.
  - Der Proxy blockiert alle Domains außer denen, die für das Lösen von CutCaptchas notwendig sind.
- **4.0.1** Es wird kein Timeout beim Lösen der CutCaptchas mehr forciert.
- **4.0.0** Click'n'Load wird nicht mehr im Chrome gelöst (da langsam und fehleranfällig), sondern direkt im AntiGateHandler. Danke an das JDownloader-Team für die Umsetzungsidee!
- **4.0.0** Prüfe anhand des Links, ob ein Passwort für den AntiGateTask gesetzt werden muss, um den korrekten AntiGateTask zu starten.
- **4.0.0** Prüfe anhand des Links, ob überhaupt ein Captcha gelöst werden muss. Dies verhindert, dass ein AntiGateTask für nicht geschützte Links erzeugt wird.
- **4.0.0** Der lokale HTTP-Proxy wird separat vom AntiGateHandler gestartet (verhindert, dass der Proxy im AntiGateTask nicht zur Verfügung steht). 
