### Installation und Update:

`pip install -U feedcrawler`

---

### 🎄🎁 Frohe Weihnachten und ein gesundes neues Jahr! 🌟✨🎉

Für die intensive Arbeit der letzten Wochen freut sich dieses Projekt über jede Unterstützung. Über [diesen Link](https://github.com/sponsors/rix1337?frequency=one-time&sponsor=rix1337) sind einmalige Beiträge möglich. Vielen Dank für die Unterstützung! 🙏

### Changelog FeedCrawler:

- **19.0.5** Security Updates
- **19.0.4** "Erneut automatisch lösen"-Button für deaktivierte Pakete 
- **19.0.4** Lösche deaktivierte Pakete bei manuellem Lösen von CAPTCHAs
- **19.0.3** Deaktiviere Pakete nach Erreichen der maximalen CAPTCHA-Lösungsversuche, statt diese zu löschen.
- **19.0.2** Überprüfe bei SF/FF den Feed von vor 3 Tagen, für die Erkennung von Cloudflare-Blockaden.
  Das verhindert Falsch positive Blockade-Erkennung, wenn der heutige Feed (noch) leer ist.
- **19.0.1** [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper) schließt Chrome automatisch, wenn Links an die GUI übergeben wurden (#755) 
- **19.0.0** Web-basierte GUI für den [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper) entfernt
- **19.0.0** Neue Methode, um aktiven Sponsoren-Status zwischen [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper) und FeedCrawler zu übermitteln.
### Changelog [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper):

Punkte, die den [FeedCrawler Sponsors Helper](https://github.com/rix1337/FeedCrawler/wiki/5.-FeedCrawler-Sponsors-Helper)
betreffen, werden erst nach dessen Update aktiv.

- **14.0.0** Entfernung von Google Chrome, VNC und GUI
  - Alle bekannten CAPTCHA-Typen werden wie gewohnt gelöst.
  - Die Lösung ohne Browser ist effizienter und weniger fehleranfällig.
  - Detaillierte Informationen zu laufenden Lösungsversuchen werden in der Konsole ausgegeben.
  - Das Image ist nun deutlich kleiner und verbraucht weniger Ressourcen.
  - Hinweis: FC/CutCaptcha benötigt meist mehrere Versuche, um ein CAPTCHA zu lösen.
    Entsprechend sollte die maximale Anzahl an Lösungsversuchen hoch genug gesetzt (bspw. auf 5) werden.