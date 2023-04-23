### Installation und Update:

`pip install -U feedcrawler`

---

### Changelog FeedCrawler:

- **18.1.0** Die [Desktop-GUI](https://github.com/rix1337/FeedCrawler/wiki/7.-Desktop-GUI) nutzt nun `tkinter`
  - Diese Bibliothek ist in Python enthalten und muss nicht mehr separat installiert werden.
  - Ab sofort ist die GUI (außer im Docker-Container) standardmäßig aktiviert.
  - Über den neuen Parameter `--no-gui` kann die GUI deaktiviert werden.
- **18.1.0** Das Tray-Icon der [Desktop-GUI](https://github.com/rix1337/FeedCrawler/wiki/7.-Desktop-GUI) nutzt nun `pystray`
  - Eine Implementierung des Tray-Icons, ohne externe Abhängigkeiten, ist aufgrund der Vielzahl an Betriebssystemen und Desktop-Umgebungen nicht
    sinnvoll.
  - Das Tray-Icon ist nicht optional, da die Desktop-GUI ohne Icon nicht sinnvoll im Hintergrund betrieben werden kann.
  - Damit erhöht sich die Anzahl der Dependencies des FeedCrawlers auf 4.
- **18.0.5** Verwende Locks, um die das geteilte manager.dict() bei parallelen Zugriffen sicher zu verändern (#738).
- **18.0.5** Werte, die verschlüsselt sein sollen, aber es noch nicht sind, werden nun beim Lesen verschlüsselt.
- **18.0.5** Weitere Wording-Verbesserungen im Web-Interface.
- **18.0.4** Hostnamen, Passwörter, Hashes und API-Keys werden nun verschlüsselt in der `FeedCrawler.ini` gespeichert
  - Dadurch kann die `FeedCrawler.ini` nun öffentlich geteilt werden
  - Ab sofort müssen Fehlermeldungen immer die komplette `FeedCrawler.ini` enthalten.
  - Da Key und IV des Verschlüsselungsverfahrens in der `FeedCrawler.db` gespeichert werden, sollte diese Datei nicht
    gemeinsam mit der `FeedCrawler.ini` geteilt werden.
- **18.0.3** Verbessertes Wording
  - Die Titel der Listen für die Feed-Suche im Web-Interface beschreiben nun besser, welchen Inhalt sie berücksichtigen.
  - Folgen werden nun als "Folge" und nicht mehr als "Episode" bezeichnet.
- **18.0.3** Verbesserte Zuordnung von Feed-Einträgen zur Downloadseite bei SF.
- **18.0.3** Fehlerbehebung im Abruf der Serien-API (#732, Danke @9Mad-Max5)
- **18.0.3** Erzwinge erfolgreiche Verbindung zum JDownloader bei jedem Aufruf über My JDownloader (#735, Danke @jankete)
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

Punkte, die den [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper)
betreffen, werden erst nach dessen Update aktiv.

- **9.0.6** InsecurePrivateNetworkRequestsAllowed-Policy aktiviert, um Aufrufe von Links auch in Docker-Subnetzten zuzulassen (#740).
- **9.0.5** Weiterer Bugfix beim Auswählen des Wunschhosters auf FC
- **9.0.4** Bugfix beim Auswählen des Wunschhosters auf FC
- **9.0.3** Update auf Chrome 111
- **9.0.2** Weitergabe des lokalen Proxies für die Verwendung im FeedCrawler
- **9.0.1** Freischaltung benötigter Cloudflare Domains
- **9.0.0** Neue Möglichkeit, Cloudflare-Blockaden zu lösen.
- **9.0.0** Ausführliche Fehlermeldungen bei Fehlern in der Proxy-Prüfung
