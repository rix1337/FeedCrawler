### Installation und Update:

`pip install -U feedcrawler`

- Leert unbedingt nach jedem Update den Browser-Cache!

- Punkte, die den [FeedCrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-FeedCrawler-Sponsors-Helper)  betreffen, werden erst nach dessen Update aktiv.

---

### Changelog FeedCrawler:

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
- **12.1.2** Nutze ausschließlich FlareSolverr bei SF, FF und WW, sofern dieser eingerichtet ist.
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
- **3.2.7** Pausiere Entschlüsselung von SF/FF-Links bis zum Ablauf des 6-stündigen Mindest-Intervalls, wenn eine Blockade erkannt wurde.
- **3.2.6** Ab sofort werden FC-Links auch von HW korrekt entschlüsselt
- **3.2.0** Ab sofort werden FC-Links inklusive CutCaptcha durch den AntiGateHandler automatisch entschlüsselt:
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
