### Installation und Update:

`pip install -U feedcrawler`

- Leert unbedingt nach jedem Update den Browser-Cache!

- Punkte, die den [FeedCrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-FeedCrawler-Sponsors-Helper) betreffen, werden erst nach dessen Update aktiv.

---

### Changelog:
- **11.0.11** Fix: Exception in IMDb-Suche
- **11.0.10** Fix: Exception in IMDb-Suche
- **11.0.10** Update auf Bootstrap 5.1.1
- **11.0.9** Update auf aktuelle [IMDbPY](https://imdbpy.github.io/) um lokalisierte Titel in Ombi zu laden / Fix #526
- **11.0.9** Automatisierter Releaseprozess
  über [Github Actions](https://github.com/rix1337/FeedCrawler/actions/workflows/CreateRelease.yml)
- **11.0.8** Integration von [IMDbPY](https://imdbpy.github.io/) um IMDb deutlich stabiler zu parsen
- **11.0.7** Fix #523 Danke @9Mad-Max5
- **11.0.6** Fehlerbehebung im Handling von Episodenpaketen
  - Nicht benötigte Episoden werden wieder korrekt entfernt
  - Das hinzugefügte Paket enthält die verbliebenen Episoden im Namen
- **11.0.5** Update auf Bootstrap 5.0.2
- **11.0.5** Fix beim Abruf von Filmtiteln durch Ombi
- **11.0.5** Fix der doppelten Logeinträge #519 Danke @jankete
- **11.0.4** Fix #518 Danke @jankete
- **11.0.3** Bugfixes #517
- **11.0.2** Bugfixes #516
- **11.0.1** Bugfixes #515
- **11.0.0**  Update des [FeedCrawler Sponsors Helpers](https://github.com/rix1337/RSScrawler/wiki/5.-FeedCrawler-Sponsors-Helper) auf Version 1.0.4
  - Verbessertes Laden neuer Releases
  - Update des Anti-Captcha-Addons auf v.0.56 (mit verbesserter hCaptcha-Erkennung)
- **11.0.0** **Großes Refactoring**: Verwendung globaler Variablen für wesentliche Informationen (erhöht die Pflegbarkeit des Codes deutlich)
- **11.0.0** **[FlareSolverr](https://github.com/FlareSolverr/FlareSolverr)-Integration** zur Umgehung von Cloudflare-Blockaden
  - Aufgrund der erhöhten Komplexität entfällt damit die direkte Integration von Proxys im FeedCrawler. [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) soll in Zukunft HTTP-Proxies unterstützen.
  - [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) muss lokal verfügbar sein
  - [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) wird nur verwendet, sofern eine CloudFlare-Blockade erkannt wurde
  - [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) ist nicht immer in der Lage, die Blockade zu umgehen. Ggf. muss ein Captcha-Löser im FlareSolverr konfiguriert werden um die Umgehung zu verbessern.
- **11.0.0** Update von Bootstrap auf stabile v.5.0.1 / Bootstrap Icons auf stabile v.1.5.0
- **11.0.0** Dependencies entfernt: cloudscraper, feedparser
- **11.0.0** DD-Feedsuche entfernt
<details>
  <summary>ältere Einträge</summary>
- **10.0.3** Redesign im Webinterface auf Basis der Bootstrap 5 "Offcanvas"-Funktion
- **10.0.2** Bugfixes im Webinterface und bei der erstmaligen Nutzung des FeedCrawlers
- **10.0.1** Im offiziellen Image, [docker-feedcrawler](https://github.com/rix1337/docker-feedcrawler), kann ab sofort per "VERSION"-Parameter die gewünschte Programmversion festgelegt werden.
- **10.0.1** Fix: Die Kontroll-Buttons für den JDownloader haben wieder die gewünschte Größe.
- **10.0.1** Fix: Listen und Einstellungen für nicht gesetzte Hostnamen werden wieder wie zuvor ausgeblendet. Danke @jankete
- **10.0.1** Fix: Verbesserte Blockade-Erkennung für DW funktioniert nun auch wieder ohne Proxy. Danke @jankete
- **10.0.0** Umbenennung des Projektes in **FeedCrawler**: RSS-Feeds sterben aus, und keine der relevanten Seiten bietet überhaupt noch solche an. Da die letzten großen Refactorings den Code deutlich weiter entwickelt haben, gerade was die Integration neuer Seiten in die Feedsuche angeht, war das die optimale Chance um auch die interne Datenbank und die Einstellungs-Datei zu überarbeiten.
  - Die Einstellungen und die Datenbank werden automatisch migriert
  - Bei manuellen Installationen muss erneut der Pfad für Einstellungen und Datenbank angegeben werden
  - Das Logo enthält nicht mehr die RSS-typischen zwei Balken vor einem Kreis, sondern reflektiert die Evolution des Projektes über vier gerade Balken
  - Das Update betrifft 10.241 Codezeilen (#508)
- **10.0.0** Umbenennung der Partnerprojekte
  - docker-rsscrawler heißt jetzt [docker-feedcrawler](https://github.com/rix1337/docker-feedcrawler)
  - RSScrawler Sponsors Helper heißt jetzt [FeedCrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-FeedCrawler-Sponsors-Helper)
     - Die Bereitstellung erfolgt ab sofort über ein neues privates Github Docker Repository `docker.pkg.github.com/rix1337-sponsors/docker/helper`
     - Die Freischaltung für Sponsoren ist bereits erfolgt
  - Click'n'Load2RSScrawler heißt jetzt [Click'n'Load2FeedCrawler](https://github.com/rix1337/ClickNLoad2FeedCrawler)
- **10.0.0** Frontend-Refactoring zu Bootstrap 5
  - Alle Accordions wurden gegen den Bootstrap-Standard getauscht
  - Die Custom-Slider wurden durch Bootstrap-Slider ersetzt
  - Die Tooltips wurden dem Bootstrap-Standard angeglichen
- **10.0.0** Die veralteten Fontawesome-Icons wurden durch Bootstrap-Icons ersetzt
- **10.0.0** Alle relevanten Warnungen in HTML, JS, CSS wurden behoben
- **10.0.0** Verbesserte Blockade-Erkennung für DW
- **9.2.8** Fix: #506 Der MyJDownloader-Tab ist wieder manuell auf-/zuklappbar. Danke @jankete
- **9.2.8** Der aktive Sponsorenstatus wird nun auch erkannt, ohne den [RSScrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) neustarten zu müssen.
- **9.2.7** Detailanpassungen im Webinterface
- **9.2.6** Update der Web-Frameworks auf deren aktuelle stabile Version: AngularJS v1.8.2, Bootstrap v.4.6.0, jQuery v.3.6.0
- **9.2.5** Bugfixes im Laden der Feedsuche-Laufzeiten im Webinterface
- **9.2.4** Bugfixes in "DW-Mirror bevorzugen"-Option
- **9.2.4** Verbessertes Fehlerhandling im Webinterface
- **9.2.3** Update des [RSScrawler Sponsors Helpers](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) auf stabile Version 1.0.3
  - Für DW sind ab sofort die notwendigen Popup-Berechtigungen korrekt gesetzt. Danke @jankete
- **9.2.3** Paketnamen die Whitespace (auch URL-encoded als %20) enthalten werden können jetzt über das Webinterface gelöscht werden. #498 Danke @jankete
- **9.2.2** Paketnamen die Whitespace (auch URL-encoded als %20) enthalten werden vom [RSScrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) korrekt gehandhabt. #498 Danke @jankete
- **9.2.2** Fehlerbehebung in der CDC-Funktion. Folgesuchläufe werden jetzt wieder korrekt abgebrochen, wenn eine bereits durchsuchte Feedposition erkannt wird.
- **9.2.2** Update des [RSScrawler Sponsors Helpers](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) auf stabile Version 1.0.2
  - Die darin enthaltene Version von [Click'n'Load2RSScrawler](https://github.com/rix1337/ClickNLoad2RSScrawler) wurde auf das stabile Release 1.0.2 angehoben.
- **9.2.2** Die "Suchlauf direkt starten"-Funktion erkennt ab sofort eine gelockte Datenbank korrekt als Fehler. #499 Danke @jankete
- **9.2.2** Der _Connection-Timeout_ für die _RSScrawler.db_ wurde auf 10 Sekunden erhöht.
- **9.2.1** DW wird ab sofort in der Feedsuche für Episoden verwendet #491 Danke @9Mad-Max5
  - Ab sofort genügt dieser Hostname um den vollen Funktionsumfang des RSScrawlers zu nutzen
  - Damit ist "DW-Mirror bevorzugen" ab sofort eine globale Option die für alle Listenarten berücksichtigt wird
  - Der [RSScrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) ist mit DW mit Abstand am schnellsten.
- **9.2.0** Ab sofort wird für die Dauer eines Suchlaufs ein Cache für alle HTTP-Requests, die der RSScrawler durchführt, aufgebaut. Dadurch wird die Performance verbessert, wenn die Feedsuche die gleiche Seite für verschiedene Listen mehrfach aufrufen muss (Details siehe: #496).
  - Durch das Caching wird die _RSScrawler.db_ während der laufenden Feedsuche auf mehrere hundert Megabyte Größe wachsen - und mit dem nächsten Suchlauf wieder geleert und erneut befüllt.
  - Ein In-Memory-Cache wurde bewusst verworfen, da der Arbeitsspeicherbedarf ungleich höher ausgefallen wäre.
- **9.1.1** Update des [RSScrawler Sponsors Helpers](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper)-Scriptes für SJ. Dieses wählt wieder wie gewünscht einen Hoster aus und funktioniert ab sofort auch auf DJ.
- **9.1.1** Update des [RSScrawler Sponsors Helpers](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) auf stabile Version 1.0.1
  - Im Start-Log des Docker-Containers steht ab sofort eine Versionsnummer. Ist diese nicht aktuell, muss das Docker-Image des [RSScrawler Sponsors Helpers](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) geupdatet bzw. gelöscht und neu heruntergeladen werden. 
  - Dieses Update behebt Probleme im SJ-Script. Dieses funktioniert nun ebenfalls für DJ!
- **9.1.0** Vollständiges Refactoring der Feedsuche von SJ, DJ und SF - bereitet bspw. #491 vor
- **9.0.6** Hotfix für SEGFAULT beim Start des Webservers
  - der interner Webserver `gevent` wurde durch `waitress` ersetzt
- **9.0.4** "Suchlauf direkt starten"-Funktion im Webinterface #489 Danke @jankete
- **9.0.3** Sofern ein Paket per [RSScrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) oder [Click'n'Load2RSScrawler](https://github.com/rix1337/ClickNLoad2RSScrawler) übergeben wird, das noch nicht als "hinzugefügt" markiert wurde, so wird dieses im RSScrawler als "hinzugefügt" markiert.
- **9.0.3** Ersetze, wo möglich, HTTP durch HTTPs in den zu entschlüsselnden Links
- **9.0.3** Update des [RSScrawler Sponsors Helpers](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) auf stabile Version 1.0.0
  - Im Start-Log steht ab sofort eine Versionsnummer. Ist diese nicht aktuell, muss das Docker-Image des [RSScrawler Sponsors Helpers](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) geupdatet bzw. gelöscht und neu heruntergeladen werden. 
  - Der Click'n'Load auf FC wird jetzt auch ausgelöst, wenn die Seite per HTTP aufgerufen wird.
- **9.0.3** Update des im [RSScrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) inkludierten [Click'n'Load2RSScrawler](https://github.com/rix1337/ClickNLoad2RSScrawler) auf stabile Version 1.0.0
  - Verbesserte Paketnamenerkennung (Name der Ursprungsseite wird entfernt).
  - Whitespace wird aus Paketnamen entfernt.
- **9.0.2** Fix: Bug in der Feedsuche
- **9.0.1** Fix: DW Feedsuche reaktiviert
- **9.0.0** Da der [RSScrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) die Links (inkl. Captchas) von SJ, DJ und DW vollautomatisch selbst entschlüsselt ist dies ab sofort die empfohlene Kombination aus Hostnamen.
- **9.0.0** Neue Option "DW-Mirror bevorzugen" integriert. Damit wird für jedes Release aus der Feedsuche geprüft, ob dieses auf DW verfügbar ist, um möglichst immer automatisch per [RSScrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) lösbare Links zu erhalten. Nützlich, wenn man grundsätzlich auch weitere Hostnamen in der Feedsuche berücksichtigen möchte.
- **9.0.0** Neue Seite DW wurde auch in die Websuche integriert.
- **9.0.0** Beim Programmstart werden jetzt immer alle gesetzten Hostnamen aufgelistet.
- **9.0.0** Option "1080p-HEVC bevorzugen" funktioniert wieder
- **9.0.0** Option "Zweisprachige Releases erzwingen" funktioniert wieder
- **9.0.0** FC wird nicht mehr als Hostname benötigt (die Suche klappt auch ohne)
- **8.6.7** Neue Seite DW wurde in die Feedsuche integriert. Vorteil: Der [RSScrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) löst deren Captchas komplett selbstständig - dafür bitte auf das aktuelle Image updaten.
- **8.6.6** MW wurden vollständig entfernt
- **8.6.6** XXX-Ergebnisse aus der BY-Suche werden in der Websuche (also auch Ombi) ignoriert
- **8.6.6** Fix: #481 Danke @postboy99
- **8.6.6** Fix: #480 Danke @9Mad-Max5
- **8.6.5** Verbesserter Aufbau des Webinterfaces, wenn wenige Hostnamen gesetzt sind
- **8.6.5** Fix: #478 Danke @DKeppi
- **8.6.4** Unterordner wird nicht mehr nach Medientyp getrennt (Rollback der Änderung aus 8.6.0)
- **8.6.3** Neue Seite WW wurde in die Feedsuche integriert (nicht die Websuche)
- **8.6.3** Performance der BY-Feedsuche erhöht
- **8.6.3** IMDB-Abruf in Feedsuche verbessert
- **8.6.2** Neue Seite MW wurde in Feed- und Websuche integriert.
- **8.6.2** HS wurden vollständig entfernt
- **8.6.2** 3D-Suche wurde entfernt (stattdessen ggf. die Regex-Liste nutzen)
- **8.6.2** Redirect-Links (BY/MW/SF) werden vor dem Download demaskiert
- **8.6.1** Neue Seite BY wurde in Feed- und Websuche integriert.
- **8.6.0** ❗ **Großes Refactoring im Gesamtprojekt**: MB/HW wurden vollständig entfernt. Die neue Struktur ermöglicht schnellere Integration von neuen Blogs. Weiterhin wurde die Integration von BY und MW vorbereitet. ❗ 
- **8.6.0** ~Die Option "Unterordner bei Download" erstellt nun nach Medientyp Unterordner im "RSScrawler"-Ordner. Danke @postboy99 für die Idee.~
- **8.5.1** Bereitstellung des Tampermonkey-Scriptes für Sponsoren als stabilere Alternative zur Click'n'Load-Automatik
- **8.5.0** Aktualisierte Bereitstellung der Tampermonkey-Scripte für SJ (inkl. des Scripts für Sponsoren als stabilere Alternative zur Click'n'Load-Automatik)
- **8.4.4** Fix: In der Websuche werden Staffeln wieder korrekt erkannt und hinzugefügt. Dabei werden Staffelpakete höher priorisiert als einzelne Episoden. Danke @9Mad-Max5 für den Hinweis! #469
- **8.4.4** Fix: In der Websuche werden alle verfügbaren Episoden gefunden, statt ausschließlich die letzte.
- **8.4.3** Fix: Falls deren IMDb-ID in Ombi veraltet ist, klappt der Abruf von Serien dennoch. Danke @postboy99 für den Hinweis! #467
- **8.4.2** Fix: Ombi Hinweis erscheint nun tatsächlich nur einmalig nach Programmstart
- **8.4.1** Verbesserte gleichzeitige Erkennung von bereits hinzugefügten Episoden und Staffeln
- **8.4.0** Ab sofort werden einzelne Episoden ignoriert, sofern bereits eine gleichwertige oder höherwertige Staffel hinzugefügt wurde.
- **8.4.0**  Verbesserter Consolen-Output bei Ombi.
  - Die Erfolgreiche Verbindung wird nur einmalig, beim Start des RSScrawlers aufgelistet
  - Im Folgenden enthält der Consolen-Eintrag zum abgeschlossenen Suchlauf eine Information, sofern Ombi-Anfragen bearbeitet wurden.
- **8.4.0** Bugfix: Kein Abbruch, wenn die SJ-API "None" als verfügbaren Hoster listet
- **8.4.0** Titel werden bei fehlendem Hoster nicht mehr im INFO-Log aufgelistet. Stattdessen erfolgt nach wie vor die Benachrichtigung und ein Consolen-Eintrag.
- **8.4.0** Verbesserung in Click'n'Load2RSScrawler, das im [RSScrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) inkludiert ist.
  - Ab sofort funktionieren auch Anfragen an _/jdcheck.js_ die zusätzliche Parameter enthalten (damit funktioniert beispielsweise jetzt der Click'n'Load auf AL).
  - Außerdem werden `/` in Titeln automatisch ersetzt, sodass RSScrawler die betroffenen Pakete automatisch starten kann.
- **8.3.6** Fehlerbehebung für FX (Feedsuche funktioniert wieder, Workaround für fehlerhaftes HTTPs-Zertifikat entfernt)
- **8.3.6** Erweitertes Logging für Ombi (zeigt beim Start die Anzahl angefragter Serien/Filme bei erfolgreicher Verbindung) #460 
- **8.3.5** Die `CUSTOM_HOSTER`-Option im [RSScrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) funktioniert ab sofort auch auf FC.
- **8.3.5** Der [RSScrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) schließt ab sofort alle Tabs von Drittseiten nach 15 Minuten um den stündlichen Neustart sicherzustellen.
- **8.3.5** Der [RSScrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) nutzt ab sofort ausschließlich Click'n'Load (da der DLC-Download nicht mehr wie gewohnt funktioniert)
- **8.3.5** Durch den [RSScrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) kann zur Laufzeit jeder Paketname nur einmalig **innerhalb von 30 Sekunden** hinzugefügt werden (verhindert unbeabsichtigten Mehrfachdownload).
- **8.3.4** Der [RSScrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) startet ab sofort alle 60 Minuten neu um den RAM-Verbrauch zu senken.
- **8.3.4** Die Ombi Filmsuche sucht neben dem Titel auch nach dessen Erscheinungsjahr #448 , Danke @postboy99
- **8.3.4** Die Ombi Seriensuche erkennt nun Titel und Episoden robuster #449, Danke @postboy99
- **8.3.4** Durch den [RSScrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) hinzugefügte Pakete werden nun auch in Edge-Cases wirklich aus der "Zu entschlüsseln"-Liste entfernt.
- **8.3.4** Durch den [RSScrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) kann zur Laufzeit jeder Paketname nur einmalig hinzugefügt werden (verhindert unbeabsichtigten Mehrfachdownload).
- **8.3.3** Verbesserte Erkennung von Episodenpaketen auf SF
- **8.3.3** Verbesserte Platzierung des "Neu Laden"-Buttons im Helper UI
- **8.3.2** Der [RSScrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) öffnet nun sämtliche Popups in einem neuen Tab, statt im Vollbild (hierzu ist ein Update von dessen Docker Image erforderlich)
- **8.3.2** Bugfix für #445 Danke @jankete
- **8.3.1** Windows Exe wird nun in Python 3.9 (x64) gebaut.
- **8.3.1** Bugfix für #441 Danke @jankete
- **8.3.0** Ombi ist ab sofort unabhängig von MDB/TVDB:
  - die MDB API wurde vollständig durch IMDb ersetzt
  - die TVDB API wurde vollständig durch IMDb ersetzt
  - die Suchfunktion für Filme/Serien per Ombi ist nun genauer
- **8.3.0** Der [RSScrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) schließt das Click'n'Load-Popup selbstständig nach 30 Sekunden (hierzu ist ein Update von dessen Docker Image erforderlich)
- **8.3.0** Der [RSScrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) hat nun einen "Neu laden"-Button im Webinterface (hierzu ist ein Update von dessen Docker Image erforderlich)
- **8.2.1** Der Paketstatus wurde um "Warte auf Download", "Warte auf Entpacken" und "Entpacken" (inkl. Restzeit) erweitert
- **8.2.1** Ermögliche Umgehung der Click'n'Load-Automatik, wenn Click'n'Load des [RSScrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) verfügbar ist (hierzu ist ein Update von dessen Docker Image erforderlich)
- **8.2.1** Erkenne DLC/Click'n'Load auf FC wieder im [RSScrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) (hierzu ist ein Update von dessen Docker Image erforderlich)
- **8.2.1** [RSScrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) Linkerkennung verbessert (Funktion löscht wirklich nur unerwünschte Episoden)
- **8.2.1** Verbesserte Linkerkennung für SF
- **8.2.1** Verbesserte Seitenerkennung wenn Hostnamen nicht gesetzt wurden
- **8.2.0** NGINX-Config für die externe Erreichbarkeit des [RSScrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper#externe-erreichbarkeit) ergänzt. Darüber lassen sich Captchas manuell von unterwegs lösen.
- **8.2.0** Verbesserte Webinterfaces von RSScrawler und [RSScrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper)
- **8.2.0** Verschiebe nicht entschlüsselte Links aus dem JDownloader in die RSScrawler-Datenbank
- **8.2.0** Refactoring (PEP-Guideline Fixes, Code Inspection, Code Cleanup, Renaming)
- **8.1.2** Zeige im Webinterface, ob derzeit ein [RSScrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) aktiv ist
- **8.1.2** Bugfix für [RSScrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper): Entferne Pakete immer wenn ein Paket entschlüsselt wurde.
- **8.1.1** Ab sofort empfängt der [RSScrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) auf dem Port `9666` Click'n'Load-Links
  * Click'n'Load auf Windows umleiten:
   `netsh interface portproxy add v4tov4 listenport=9666 connectaddress=<Docker Host> connectport=9666 listenaddress=127.0.0.1`
- **8.1.1** Entferne überflüssige Episoden bei durch [Click'n'Load2RSScrawler](https://github.com/rix1337/ClickNLoad2RSScrawler) hinzugefügten Links
- **8.1.1** Verbesserte Paket-Erkennung bei durch [Click'n'Load2RSScrawler](https://github.com/rix1337/ClickNLoad2RSScrawler) hinzugefügten Links
- **8.1.0** Unterstützung von [Click'n'Load2RSScrawler](https://github.com/rix1337/ClickNLoad2RSScrawler)
  * Wenn FC keinen DLC anbietet, nutzt der RSSCrawler ab sofort  [Click'n'Load2RSScrawler](https://github.com/rix1337/ClickNLoad2RSScrawler) um die Links intern zu entschlüsseln.
  * Der [RSScrawler Sponsors Helper](https://github.com/rix1337/RSScrawler/wiki/5.-RSScrawler-Sponsors-Helper) erkennt automatisch welche Methode verfügbar ist.
  * Verschlüsselte Links werden automatisch durch die entschlüsselten ersetzt.
  * Die Standardpasswörter von FC und FX werden automatisch eingegeben.
  * Einziges offenes Problem bei FC sind nach wie vor die Captchas. Diese müssen weiter per VNC gelöst werden.
  * **Wie immer gilt: das alte Docker-Image löschen und danach das neue mit eurem Docker-Login herunterladen!**
- **8.1.0** Deutlich robustere Link-Erkennung für FX
- **8.0.4** FX wieder verfügbar (Workaround solange dort das Intermediate Certificate von letsencrypt fehlt)
- **8.0.3** Bugfix für SF - Danke @jankete für den Hinweis! #431
- **8.0.1** Ab sofort wird SF unterstützt! Danke @Slomo17 für den Hinweis! #427
- **8.0.0** **Hostnamen sind ab sofort nicht mehr Teil des Codes! (Umfangreiche Codeanpassung, siehe: #428)**
  Ausschließlich der Anwender entscheidet, welche Seiten durchsucht werden sollen. Diese Entscheidung trifft der Anwender selbstständig, indem er die _RSScrawler.ini_ in der Kategorie _[Hostnames]_ manuell befüllt (_ab = xyz.com_). Eingetragen werden dort reine Hostnamen (ohne _https://_).
 
  **Dabei gilt**
  *   Welcher Hostname aufgerufen wird entscheidet allein der Anwender.
  *    Ist nicht mindestens ein Hostname gesetzt, wird der RSScrawler nicht starten.
  *    Passt die aufgerufene Seite hinter dem jeweiligen Hostnamen nicht zum Suchmuster des RSScrawlers, kann es zu Fehlern kommen.
  *    Weder RSScrawler noch der Autor benennen oder befürworten spezifische Hostnamen. Fragen hierzu werden ignoriert!

- **8.0.0** DJ wurde auf die neue Seite (analog zu SJ) angepasst und funktioniert wieder. Genres werden nicht mehr geprüft.
- **8.0.0** YT wurde entfernt.
- **8.0.0** Alle Hostnamen werden vor dem Start jedes Suchlaufs geprüft (ob die Seite verfügbar ist).
- **8.0.0** Windows Exe wird nun in Python 3.8 gebaut.
</details>
