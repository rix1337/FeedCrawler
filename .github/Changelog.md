### Installation und Update:

`pip install -U feedcrawler`

---

### Changelog FeedCrawler:

- **19.0.3** Deaktiviere Pakete nach Erreichen der maximalen CAPTCHA-Lösungsversuche, statt diese zu löschen.
- **19.0.2** Überprüfe bei SF/FF den Feed von vor 3 Tagen, für die Erkennung von Cloudflare-Blockaden.
  Das verhindert Falsch positive Blockade-Erkennung, wenn der heutige Feed (noch) leer ist.
- **19.0.1** [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper) schließt Chrome automatisch, wenn Links an die GUI übergeben wurden (#755) 
- **19.0.0** Web-basierte GUI für den [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper) entfernt
- **19.0.0** Neue Methode, um aktiven Sponsoren-Status zwischen [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper) und FeedCrawler zu übermitteln.
### Changelog [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper):

Punkte, die den [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper)
betreffen, werden erst nach dessen Update aktiv.

- **12.0.4** Deaktiviere Pakete, die nicht gelöst werden konnten nach Erreichen der maximalen CAPTCHA-Lösungsversuche.
- **12.0.4** Fehlerbehebung im Zählend der Anzahl CAPTCHA-Lösungsversuche pro Paket
- **12.0.3** Überarbeitung von GUI und Log
- **12.0.2** Folge Redirects beim Lösen von CAPTCHAs
- **12.0.1** Fehlerbehebung beim Lösen von CAPTCHAs
- **12.0.0** Native GUI für die Verwaltung zu lösender CAPTCHas
    - Die neue GUI ist nicht hübsch, spart dadurch allerdings Ressourcen gegenüber der Web-basierten GUI.
    - Bisher unterstützte CAPTCHA-Typen werden wie zuvor gelöst.
    - Nur für CAPTCHAs, die einen Browser voraussetzen wird temporär Google Chrome gestartet.
    - Alle anderen CAPTCHA-Typen werden im Hintergrund gelöst.
    - Der Status der gelösten CAPTCHAs wird in der GUI angezeigt.
    - Detailierte Informationen zu laufenden Lösungsversuchen werden in der Konsole ausgegeben.