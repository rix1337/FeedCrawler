### Installation und Update:

`pip install -U feedcrawler`

---

### Changelog FeedCrawler:

- **18.0.3** Verbessertes Wording
  - Die Titel der Suchlisten im Web-Interface beschreiben nun besser, welchen Inhalt sie berücksichtigen.
  - Folgen werden nun als "Folge" und nicht mehr als "Episode" bezeichnet.
- **18.0.3** Verbesserte Zuordnung von Feed-Einträgen zur Downloadseite bei SF.
- **18.0.3** Erzwinge erfolgreiche Verbindung zum JDownloader bei jedem Aufruf über My JDownloader (#735).
- **18.0.2** Die Konsole der Desktop-GUI behält aus Performancegründen nur die letzten 999 ausgegebenen Zeilen.
- **18.0.2** Nutze ausschließlich manager.dict() um Objekte zwischen Prozessen zu teilen.
- **18.0.2** SF/FF werden nicht mehr als dauerhaft von Cloudflare blockierte Seiten behandelt.
- **18.0.1** Der FeedCrawler-Cache (HTTP-Aufrufe eines Suchlaufes) nutzt nun den RAM, anstelle der `FeedCrawler.db` 
- **18.0.1** Entferne überflüssige Tabellen automatisch aus der `FeedCrawler.db`
- **18.0.1** Entferne überflüssige Sektionen und Optionen automatisch aus der `FeedCrawler.ini`
- **18.0.1** Aktive My JDownloader Geräteverbindungen werden nun im RAM, anstelle der `FeedCrawler.db` gespeichert 
- **18.0.1** Verhindere doppelte Zeilenumbrüche in der Standard-Konsole bei aktiver Desktop-GUI
- **18.0.1** Setze das Icon aller Fenster der Desktop-GUI auf das FeedCrawler-Logo
- **18.0.0** Eigene [Desktop-GUI](https://github.com/rix1337/FeedCrawler/wiki/7.-Desktop-GUI), die anstelle der Konsole verwendet werden kann
  - Wird automatisch genutzt, wenn `PySimpleGUI` und `psgtray` installiert sind
  - Wird für die Windows-Exe verwendet
  - Bei Erstinstallation werden My JDownloader Zugangsdaten in der GUI abgefragt (inklusive Auswahl des JDownloaders)

### Changelog [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper):

Punkte, die den [FeedCrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-FeedCrawler-Sponsors-Helper)
betreffen, werden erst nach dessen Update aktiv.

- **9.0.4** Bugfix beim Auswählen des Wunschhosters auf FC
- **9.0.3** Update auf Chrome 111
- **9.0.2** Weitergabe des lokalen Proxies für die Verwendung im FeedCrawler
- **9.0.1** Freischaltung benötigter Cloudflare Domains
- **9.0.0** Neue Möglichkeit, Cloudflare-Blockaden zu lösen.
- **9.0.0** Ausführliche Fehlermeldungen bei Fehlern in der Proxy-Prüfung
