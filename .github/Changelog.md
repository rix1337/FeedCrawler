### Installation und Update:

`pip install -U feedcrawler`

- Leert unbedingt nach jedem Update den Browser-Cache!

- Punkte, die den [FeedCrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-FeedCrawler-Sponsors-Helper)  betreffen, werden erst nach dessen Update aktiv.

---

### Changelog FeedCrawler:

- **12.3.0** PL-Feedsuche integriert
- **12.3.0** Modulstruktur überarbeitet und Zweck der Einzelmodule dokumentiert.


### Changelog [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper):

- **4.0.2** Der AntiGateHandler entschlüsselt nun die DLC-Datei, sofern der Click'n'Load-Button fehlt.
- **4.0.1** Der lokale HTTP-Proxy läuft ab sofort dauerhaft.
  - Die Zugangsdaten werden weiterhin bei jedem Start zufallsgeneriert.
  - Der Proxy blockiert alle Domains außer denen, die für das Lösen von CutCaptchas notwendig sind.
- **4.0.1** Es wird kein Timeout beim Lösen der CutCaptchas mehr forciert.
- **4.0.0** Click'n'Load wird nicht mehr im Chrome gelöst (da langsam und fehleranfällig), sondern direkt im AntiGateHandler. Danke an das JDownloader-Team für die Umsetzungsidee!
- **4.0.0** Prüfe anhand des Links, ob ein Passwort für den AntiGateTask gesetzt werden muss, um den korrekten AntiGateTask zu starten.
- **4.0.0** Prüfe anhand des Links, ob überhaupt ein Captcha gelöst werden muss. Dies verhindert, dass ein AntiGateTask für nicht geschützte Links erzeugt wird.
- **4.0.0** Der lokale HTTP-Proxy wird separat vom AntiGateHandler gestartet (verhindert, dass der Proxy im AntiGateTask nicht zur Verfügung steht). 
