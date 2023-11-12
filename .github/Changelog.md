### Installation und Update:

`pip install -U feedcrawler`

---

### Changelog FeedCrawler:

- **19.0.2** Überprüfe bei SF/FF den Feed von vor 3 Tagen, für die Erkennung von Cloudflare-Blockaden.
  Das verhindert Falsch positive Blockade-Erkennung, wenn der heutige Feed (noch) leer ist.
- **19.0.1** [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper) schließt Chrome automatisch, wenn Links an die GUI übergeben wurden (#755) 
- **19.0.0** Web-basierte GUI für den [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper) entfernt
- **19.0.0** Neue Methode, um aktiven Sponsoren-Status zwischen [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper) und FeedCrawler zu übermitteln.
### Changelog [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper):

Punkte, die den [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper)
betreffen, werden erst nach dessen Update aktiv.

- **12.0.0** Native GUI für die Verwaltung zu lösender CAPTCHas
    - Die neue GUI ist nicht hübsch, spart dadurch allerdings Ressourcen gegenüber der Web-basierten GUI.
    - Bisher unterstützte CAPTCHA-Typen werden wie zuvor gelöst.
    - Nur für CAPTCHAs, die einen Browser voraussetzen wird temporär Google Chrome gestartet.
    - Alle anderen CAPTCHA-Typen werden im Hintergrund gelöst.
    - Der Status der gelösten CAPTCHAs wird in der GUI angezeigt.
    - Detailierte Informationen zu laufenden Lösungsversuchen werden in der Konsole ausgegeben.