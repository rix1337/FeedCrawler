### Installation und Update:

`pip install -U feedcrawler`

---

### Changelog FeedCrawler:

- **16.4.2** Proxy-Support für FlareSolverr entfernt. Der Seitenstatus sollte nun wieder korrekt angezeigt werden.
- **16.4.2** Verbessertes Chunking beim `build` des VueJS Frontends
- **16.4.1** Discord-Benachrichtigungen
- **16.4.0** Kompatibilität mit Sponsors Helper v.8.0.0
- **16.3.8** VueJS Depedency Updates [#694](https://github.com/rix1337/FeedCrawler/pull/694)
- **16.3.7** Bugfix: "'NoneType' is not iterable" in myjd_connection.py
- **16.3.6** Erkenne fälschlich als "Fertig" markierte Dateien (Größe 0 Bytes) und setze diese zurück.
- **16.3.6** Verhindere, dass während der SJ/DJ/SF/FF-Wartezeit der Seitenstatus gelöscht wird.
- **16.3.5** Bugfix im Abruf von FF in Verbindung mit FlareSolverr
- **16.3.5** Bugfix im Abruf von SF in Verbindung mit FlareSolverr
- **16.3.4** Integration der NX-Websuche
- **16.3.3** Bugfix im Aufruf der Entschlüsselungsfunktion im [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper)
- **16.3.2** Verbessertes Handling von NX-Links, inklusive Click'n'Load-Script für Sponsoren in der Web-UI.
- **16.3.1** Bugfix im Abruf der Hostnamen
- **16.3.0** NX-Feed-Suche integriert
- **16.2.0** Dark-Mode-Unterstützung für die Web-UI
- **16.2.0** Flaresolverr 3 wird ab sofort unterstützt (verbraucht deutlich weniger CPU/RAM)
  - Derzeit gibt Flaresolverr 3 keine Header zurück.
  - Daher können Weiterleitungen von URLs (bspw. für die Download-Links) noch nicht automatisch aufgelöst werden.
  - Die Implementierung ist darauf vorbereitet, dass in Zukunft Header und Cookies aus der Flaresolverr-Antwort
    genutzt werden, um diese, solange gültig, direkt in Python zu verwenden.
  - Dies sollte für deutlich weniger Aufrufe von Flaresolverr sorgen.
- **16.2.0** Dependency `html5lib` entfernt und durch den schnelleren Python-eigenen `html.parser` ersetzt.
- **16.2.0** Verbesserungen in der IMDb-Suche, wenn die IMDb-ID nicht am Release verfügbar ist.
- **16.2.0** Bugfix: Die BY-Feed-Suche funktioniert wieder.
- **16.2.0** Bugfix: Die FF-Feed-Suche funktioniert wieder.
- **16.1.0** Bugfix: Leite alle Web-Requests ohne Trailing Slash korrekt weiter (Behebt [Organizr#1830](https://github.com/causefx/Organizr/issues/1830)).
- **16.0.3** Verbesserte Validierung der und Hinweise zur Plex-Direct-URL
- **16.0.2** Bugfix in Plex-Serien-Suche
- **16.0.2** Bugfix in Identifikation der IMDb-ID auf Basis eines Suchtitels
- **16.0.1** Integration der [Plex-Watchlist](https://support.plex.tv/articles/universal-watchlist/) als Suchquelle
- **16.0.0** Versionsprüfung für den Sponsors Helper

### Changelog [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper):

Punkte, die den [FeedCrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-FeedCrawler-Sponsors-Helper)
betreffen, werden erst nach dessen Update aktiv.

- **8.0.1** Fehlerbehebung beim Setzen des User-Agents
- **8.0.0** Der Sponsors Helper erkennt bei FC-Links nun, ob laut Release-Titel eine einzelne Staffel oder Episode
  hinzugefügt werden soll. In diesem Fall werden nur die tatsächlich notwendigen Links an JDownloader übergeben. 
- **8.0.0** Update auf Google Chrome 110
