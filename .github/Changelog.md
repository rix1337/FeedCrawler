### Installation und Update:

`pip install -U feedcrawler`

- Leert unbedingt nach jedem Update den Browser-Cache!

- Punkte, die den [FeedCrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-FeedCrawler-Sponsors-Helper)  betreffen, werden erst nach dessen Update aktiv.

---

### Changelog FeedCrawler:

- **12.2.11** Löse SJ und DJ Links vor FC und maskierten SF/FF und WW Links im [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper).
- **12.2.11** Bugfix im Speichern des Passwortes
- **12.2.11** Folge Upstream-Ubenennung von IMDbPy auf Cinemagoer
- **12.2.10** Benachrichtigung, wenn ein Titel aus der Suchliste für Filme entfernt wurde. Danke @mx-hero
- **12.2.9** Fix #579 - Danke @jankete
- **12.2.8** Verhindere das Speichern im Web-Interface, wenn Minima/Maxima gerissen wurden.
- **12.2.8** Interval und Suchtiefe auf SF/FF sind im Web-Interface konfigurierbar.
- **12.2.7** Prüfe die Erreichbarkeit von SF/FF ebenfalls erst nach dem Mindest-Intervall (verhindert Bans).
- **12.2.7** Senke Suchintervall bei SF/FF-Feedsuchen wieder auf 6 Stunden.
- **12.2.6** Erhöhe Suchintervall bei SF/FF-Feedsuchen.
- **12.2.5** Verbesserte Icon-Darstellung der Seitenstatus (OK/Gesperrt/Wartet) im Hilfe-Bereich.
- **12.2.5** Löse SJ/DJ und FC Links vor maskierten SF/FF und WW Links im [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper).
- **12.2.5** Demaskiere SF/FF-Links vor Weitergabe an den [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper) um Sperren vorzubeugen.
- **12.2.5** Übergib auch bei BY/NK die FC-Links nicht dem JDownloader.
- **12.2.4** Beachte das Mindest-Intervall für SF/FF-Feedsuchen auch im [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper).
- **12.2.3** Speichere das Mindest-Intervall für SF/FF-Feedsuchen in der Datenbank um dieses auch bei Neustarts des FeedCrawlers korrekt zu beachten.
- **12.2.2** Verhindere unerwünschte Ergebnisse in HW-Websuche
- **12.2.2** Erzwinge 6 Stunden Mindest-Intervall für SF/FF-Feedsuchen
- **12.2.2** Bugfix in FF-Feedsuche bei fehlendem IMDb-Link
- **12.2.1** Fix in durch FF hinzugefügten Links
- **12.2.0** FF in die Feed-Suche integriert 🧑🏻‍🎄🎄🎅🏻 - Frohe Weihnachten!
- **12.2.0** SF und FF durchsuchen nur die letzten beiden Tage um die Ban-Wahrscheinlichkeit zu senken.


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
