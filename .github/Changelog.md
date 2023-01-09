### Installation und Update:

`pip install -U feedcrawler`

---

### Changelog FeedCrawler:

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

- **7.1.0** Update auf neue noVNC Version
- **7.0.4** Das Chrome-Profil wird jetzt vor jedem Start bereinigt, um Caching-Probleme bei Updates zu vermeiden. 
- **7.0.4** Fehlerbehebung in der Proxy-Prüfung beim Start
- **7.0.4** Nutze den aktuellen Bootstrap 5 Standard für das Webinterface
- **7.0.3** Freischaltung der neuen Domain von Anti-Captcha im Proxy
- **7.0.2** Bugfix für Ausführung ohne `privileged`-Flag
- **7.0.1** Redundante Prüfung, ob der Proxy erfolgreich erstellt wurde (falls ident.me oder ipify.org down sind)
- **7.0.0** Der Sponsors Helper prüft nun, ob er mit der aktuellen FeedCrawler-Version kompatibel ist.
- **7.0.0** Update auf Google Chrome 108
