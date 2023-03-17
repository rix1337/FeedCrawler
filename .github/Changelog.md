### Installation und Update:

`pip install -U feedcrawler`

---

### Changelog FeedCrawler:

- **17.0.9** Fix in der Link-Übergabe zum Helper
- **17.0.8** Cloudflare-Umgehung auf HW korrigiert
- **17.0.7** Alle Seiten mit bekannten Cloudflare-Blockaden in die Wartezeit aufgenommen
- **17.0.7** Verbesserte Cloudflare-Blockaden-Überprüfung für HW
- **17.0.7** Überspringe Suchläufe blockierter Seiten
- **17.0.7** Zeige korrekte Anzahl von **Sponsors-Helper** Fehlversuchen im Log an
- **17.0.6** Werte Fehlversuche im **Sponsors-Helper** nur, wenn der vorhergehende Suchlauf vollständig beendet wurde.
- **17.0.6** Erkenne und umgehe Cloudflare-Blockaden auch während eines Suchlaufes, statt nur davor.
- **17.0.5** Ermittle und nutze die lokale Adresse des **Sponsors-Helper**-Proxies anhand der **Sponsors-Helper**-URL.
  - Bei einigen Benutzern traten mit der externen Proxy-Adresse Probleme auf (bspw. bei @mx-hero)
  - Die lokale Adresse ist nutzbar, da diese bereits für den Aufruf des **Sponsors-Helpers** verwendet wird.
- **17.0.4** Status bestehender Cloudflare-Blockaden wird wieder korrekt aktualisiert
- **17.0.3** FlareSolverr-Anbindung überarbeitet:
  - Die Implementierung folgt jetzt der deutlich effizienteren Lösung auf Basis des **Sponsors Helpers**.
  - FlareSolverr wird nur noch für die Erzeugung gültiger Cloudflare-Cookies verwendet.
  - Zuvor wurden alle Requests zu gesperrten Seiten über den FlareSolverr geschickt.
  - Da FlareSolverr gratis ist, wird dieser von FeedCrawler bevorzugt zur Cloudflare-Umgehung eingesetzt.
  - Ist ein **Sponsors Helper** konfiguriert, wird dieser nur verwendet, wenn FlareSolverr gescheitert ist.
- **17.0.3** Neue Fehlermeldung, wenn Release aus SF-Feed nicht auf Download-Seite verfügbar ist 
- **17.0.3** Schalter für Medientypen merkt sich die Einstellung im Browser-Storage, analog zum Dark Mode
- **17.0.3** Schalter für Medientypen in der mobilen Ansicht stärker zentriert (#712), Danke @kroeberd
- **17.0.2** Timeout für die Cloudflare-Umgehung des **Sponsors Helper** auf 3 Minuten erhöht
- **17.0.2** Schalter für Medientypen (Filme und/oder Serien) im Web-Interface
- **17.0.1** Neue Option, Serien und Filme in getrennte Unterordner zu verschieben
- **17.0.1** NX-Web-Suche beachtet nun die gesetzte Auflösung (#708), Danke @kroeberd
- **17.0.1** Umgehe Cloudflare-Blockade für die Web-Suche auch während der SJ/DJ/SF/FF-Wartezeit
- **17.0.0** Neue Option, die Cloudflare-Blockaden durch den **Sponsors Helper** zu lösen

### Changelog [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper):

Punkte, die den [FeedCrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-FeedCrawler-Sponsors-Helper)
betreffen, werden erst nach dessen Update aktiv.

- **9.0.4** Bugfix beim Auswählen des Wunschhosters auf FC
- **9.0.3** Update auf Chrome 111
- **9.0.2** Weitergabe des lokalen Proxies für die Verwendung im FeedCrawler
- **9.0.1** Freischaltung benötigter Cloudflare Domains
- **9.0.0** Neue Möglichkeit, Cloudflare-Blockaden zu lösen.
- **9.0.0** Ausführliche Fehlermeldungen bei Fehlern in der Proxy-Prüfung
