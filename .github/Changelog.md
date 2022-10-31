### Installation und Update:

`pip install -U feedcrawler`

---

### Changelog FeedCrawler:

- **15.0.6** Hinweis auf langsame Seiten in Websuche ist nun weniger prominent.
- **15.0.6** DW-Websuche ignoriert nun Release-Titel, die nicht mit dem Suchbegriff übereinstimmen.
- **15.0.5** Beim Hinzufügen einzelner Episoden wird deren Titel wieder korrekt gesetzt
- **15.0.5** Über die Click'n'Load-Automatik hinzugefügte Releases werden korrekt um unerwünschte Episoden bereinigt.
- **15.0.5** Updates in den GitHub-Actions
- **15.0.4** Dependency-Updates
- **15.0.4** Erkenne Fehler in der Verbindung zur FeedCrawler.db (#655)
- **15.0.3** Verbesserung im Zuordnen von Staffelpaketen.
- **15.0.3** Korrektur in Hoster-Identifikation auf DW
- **15.0.2** Verhindert das Überspringen von kurz hintereinander hinzugefügten Episoden einer Staffel.
- **15.0.2** Die SF-Suche beachtet wieder die korrekte Suchtiefe (in Tagen).
- **15.0.1** Bugfix #649 (Fehler in automatischer Web-Suche)
- **15.0.1** Verbesserter Verbindungsaufbau zum JDownloader nach Nichtverfügbarkeit.
- **15.0.0** DW Web-Suche hinzugefügt.
- **15.0.0** **Hinweis:** Das Passwort für das Web-Interface muss in der _FeedCrawler.ini_ neu gesetzt werden.
- **15.0.0** Neue Funktion zum automatischen Ausblenden des JDownloader-Spendenbanners für Sponsoren implementiert.
- **15.0.0** Hinterlege Deaktivierte Pakete grau
- **15.0.0** Korrektur beim Löschen von Paketen mit Sonderzeichen im Titel.
- **15.0.0** Korrektur in der Auswertung der Filterlisten
- **15.0.0** Korrektur in der Prüfung der Verbindung zu My JDownloader beim Start
- **15.0.0** Interne Paketstruktur erneut überarbeitet.
- **15.0.0** Der interne Request Handler unterstützt nun auch HTTP-Authentifizierung per URL und Proxies
  (derzeit ungenutzt).

### Changelog [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper):

Punkte, die den [FeedCrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-FeedCrawler-Sponsors-Helper)
betreffen, werden erst nach dessen Update aktiv.

- **6.0.0** Der Helper nutzt analog zum FeedCrawler weniger externe Python-Dependencies
  (`docopt`, `flask` und `waitress` wurden entfernt).
