# -*- coding: utf-8 -*-
# RSScrawler - Version 2.0.0
# Projekt von https://github.com/rix1337

import cherrypy
import os, sys
import StringIO
from rssconfig import RssConfig
from RSScrawler import checkFiles

class Server:
  # Zeige Konfigurationsseite
  @cherrypy.expose
  def index(self):
    # importiere Einstellungen
    main = RssConfig('RSScrawler')
    jdownloader = main.get("jdownloader")
    port = main.get("port")
    prefix = main.get("prefix")
    interval = main.get("interval")
    hoster = main.get("hoster")
    pushbulletapi = main.get("pushbulletapi")
    # MB-Bereich
    mb = RssConfig('MB')
    mbquality = mb.get("quality")
    ignore = mb.get("ignore")
    historical = str(mb.get("historical"))
    crawl3d = str(mb.get("crawl3d"))
    enforcedl = str(mb.get("enforcedl"))
    crawlseasons = str(mb.get("crawlseasons"))
    seasonsquality = mb.get("seasonsquality")
    seasonssource = mb.get("seasonssource")
    # SJ-Bereich
    sj = RssConfig('SJ')
    sjquality = sj.get("quality")
    rejectlist = sj.get("rejectlist")
    regex = str(sj.get("regex"))

    return '''<!DOCTYPE html>
<html>
  <head>
    <style>
      @import url(https://fonts.googleapis.com/css?family=Roboto:400,300,600,400italic);.copyright,[hinweis]:before,div,h1,h2,h3,input{text-align:center}*{margin:0;padding:0;box-sizing:border-box;-webkit-box-sizing:border-box;-moz-box-sizing:border-box;-webkit-font-smoothing:antialiased;-moz-font-smoothing:antialiased;-o-font-smoothing:antialiased;font-smoothing:antialiased;text-rendering:optimizeLegibility}body{font-family:Roboto,Helvetica,Arial,sans-serif;font-weight:100;font-size:14px;line-height:30px;color:#000;background:#d3d3d3}.container{max-width:800px;width:100%;margin:0 auto;position:relative}[hinweis]:after,[hinweis]:before{position:absolute;bottom:150%;left:50%}#rsscrawler button[type=submit],#rsscrawler iframe,#rsscrawler input[type=text],#rsscrawler textarea{font:400 12px/16px Roboto,Helvetica,Arial,sans-serif}#rsscrawler{background:#F9F9F9;padding:25px;margin:50px 0;box-shadow:0 0 20px 0 rgba(0,0,0,.2),0 5px 5px 0 rgba(0,0,0,.24)}#rsscrawler h1{display:block;font-size:30px;font-weight:300;margin-bottom:10px}#rsscrawler h4{margin:5px 0 15px;display:block;font-size:13px;font-weight:400}fieldset{border:none!important;margin:0 0 10px;min-width:100%;padding:0;width:100%}#rsscrawler iframe,#rsscrawler input[type=text],#rsscrawler textarea{width:100%;border:1px solid #ccc;background:#FFF;margin:0 0 5px;padding:10px}#rsscrawler iframe,#rsscrawler input[type=text]:hover,#rsscrawler textarea:hover{-webkit-transition:border-color .3s ease-in-out;-moz-transition:border-color .3s ease-in-out;transition:border-color .3s ease-in-out;border:1px solid #aaa}#rsscrawler textarea{height:100px;max-width:100%;resize:none}#rsscrawler button[type=submit]{cursor:pointer;width:100%;border:none;background:#333;color:#FFF;margin:0 0 5px;padding:10px;font-size:15px}#rsscrawler button[type=submit]:hover{background:#43A047;-webkit-transition:background .3s ease-in-out;-moz-transition:background .3s ease-in-out;transition:background-color .3s ease-in-out}#rsscrawler button[type=submit]:active{box-shadow:inset 0 1px 3px rgba(0,0,0,.5)}#rsscrawler input:focus,#rsscrawler textarea:focus{outline:0;border:1px solid #aaa}::-webkit-input-placeholder{color:#888}:-moz-placeholder{color:#888}::-moz-placeholder{color:#888}:-ms-input-placeholder{color:#888}[hinweis]{position:relative;z-index:2;cursor:pointer}[hinweis]:after,[hinweis]:before{visibility:hidden;-ms-filter:"progid:DXImageTransform.Microsoft.Alpha(Opacity=0)";filter:progid: DXImageTransform.Microsoft.Alpha(Opacity=0);opacity:0;pointer-events:none}[hinweis]:before{margin-bottom:5px;margin-left:-400px;padding:9px;width:782px;-webkit-border-radius:3px;-moz-border-radius:3px;border-radius:0;background-color:#000;background-color:hsla(0,0%,20%,.9);color:#fff;content:attr(hinweis);font-size:14px;line-height:1.2}[hinweis]:after{margin-left:-5px;width:0;border-top:5px solid #000;border-top:5px solid hsla(0,0%,20%,.9);border-right:5px solid transparent;border-left:5px solid transparent;content:" ";font-size:0;line-height:0}[hinweis]:hover:after,[hinweis]:hover:before{visibility:visible;-ms-filter:"progid:DXImageTransform.Microsoft.Alpha(Opacity=100)";filter:progid: DXImageTransform.Microsoft.Alpha(Opacity=100);opacity:1}
    </style>
  </head>
  <body>
  <div class="container">
    <form id="rsscrawler" action="https://github.com/rix1337/thanks">
          <h1>RSScrawler v.2.0.0</h1>
          <button type="submit">Bedanken</button>
    </form>
    <form id="rsscrawler">
          <h1>Log</h1>
            <iframe src="./log" width="100%" height="200" frameborder="1">
            Dieser Browser unterstützt keine iFrames. Stattdessen <a href = "/log">/log</a> aufrufen.
          </iframe>
    </form>
    <form id="rsscrawler" action="https://www.9kw.eu/register_87296.html">
          <h1>Captchas</h1>
          <button type="submit">Captchas automatisch lösen lassen</button>
    </form>
    <form id="rsscrawler" enctype="multipart/form-data" method="post" action="speichern">
          <div hinweis="Hier werden s&auml;mtliche Einstellungen von RSScrawler hinterlegt.Dieses Script funktioniert nur sinnvoll, wenn Ordner&uuml;berwachung im JDownloader aktiviert ist.Es muss weiterhin unten der richtige JDownloader Pfad gesetzt werden!"><h1>Einstellungen</h1></div>
          <div hinweis="Diese allgemeinen Einstellungen m&uuml;ssen korrekt sein"><h3>Allgemein</div>
          Pfad des JDownloaders:<div hinweis="Dieser Pfad muss das exakte Verzeichnis des JDownloaders sein, sonst funktioniert das Script nicht!"><input type="text" value="''' + jdownloader +'''" name="jdownloader"/></div>
          Port:<div hinweis="Hier den Port des Webservers f&uuml;r Einstellungen und Log w&auml;hlen"><input type="text" name="port" value="''' + port +'''"></div>
          Prefix:<div hinweis="Hier den Prefx des Webservers f&uuml;r Einstellungen und Log w&auml;hlen. Nützlich für Proxys"><input type="text" name="prefix" value="''' + prefix +'''"></div>
          Suchintervall:<div hinweis="Das Suchintervall in Minuten sollte nicht zu niedrig angesetzt werden um keinen Ban zu riskieren"><input type="text" name="interval" value="''' + interval +'''"></div>
          Pushbullet API-Schlüssel:<div hinweis="Um &uuml;ber hinzugef&uuml;gte Releases informiert zu werden hier den Pushbullet API-Key eintragen"><input type="text" name="pushbulletapi" value="''' + pushbulletapi +'''"></div>
          Hoster:<div hinweis="Hier den gew&uuml;nschten Hoster eintragen (Uploaded oder Share-Online). Möglich sind auch beide (durch Kommata getrennt)"><input type="text" name="hoster" value="''' + hoster +'''"></div>
          <div hinweis="Dieser Bereich ist f&uuml;r die Suche auf Movie-Blog.org zust&auml;ndig"><h3>Movie-Blog</h3></div>
          Auflösung:<div hinweis="Die Qualit&auml;t, nach der Gesucht wird (1080p, 720p oder 480p)"><input type="text" name="mbquality" value="''' + mbquality +'''"></div>
          Filterliste:<div hinweis="Releases mit diesen Begriffen werden nicht hinzugef&uuml;gt (durch Kommata getrennt)"><input type="text" name="ignore" value="''' + ignore +'''"></div>
          Suchfunktion statt Feed nutzen:<div hinweis="Wenn aktiviert wird die MB-Suchfunktion genutzt (langsamer), da der Feed nur wenige Stunden abbildet"><input type="text" name="historical" value="''' + historical +'''"></div>
          3D-Releases suchen:<div hinweis="Wenn aktiviert sucht das Script nach 3D Releases (in 1080p), unabh&auml;ngig von der oben gesetzten Qualit&auml;t"><input type="text" name="crawl3d" value="''' + crawl3d +'''"></div>
          Zweisprachige Releases suchen:<div hinweis="Wenn aktiviert sucht das Script zu jedem nicht-zweisprachigen Release (kein DL-Tag im Titel) ein passendes Release in 1080p mit DL Tag. Findet das Script kein Release wird dies im Log vermerkt. Bei der n&auml;chsten Ausf&uuml;hrung versucht das Script dann erneut ein passendes Release zu finden. Diese Funktion ist n&uuml;tzlich um (durch sp&auml;teres Remuxen) eine zweisprachige Bibliothek in 720p zu halten."><input type="text" name="enforcedl" value="''' + enforcedl +'''"><br /></div>
          Staffeln suchen:<div hinweis="Komplette Staffeln von Serien landen zuverl&auml;ssiger auf MB als auf SJ. Diese Option erlaubt die entsprechende Suche"><input type="text" name="crawlseasons" value="''' + crawlseasons +'''" ></div>
          Auflösung der Staffeln:<div hinweis="Die Qualit&auml;t, nach der Staffeln gesucht werden (1080p, 720p oder 480p)"><input type="text" name="seasonsquality" value="''' + seasonsquality +'''"></div>
          Quellart der Staffeln:<div hinweis="Der Staffel-Releasetyp nach dem gesucht wird"><input type="text" name="seasonssource" value="''' + seasonssource +'''"></div>
          <div hinweis="Dieser Bereich ist f&uuml;r die Suche auf Serienjunkies.org zust&auml;ndig"><h3>SerienJunkies</h1></div>
          <p>Auflösung:<div hinweis="Die Qualit&auml;t, nach der Gesucht wird (1080p, 720p oder 480p)"><input type="text" name="sjquality" value="''' + sjquality +'''"></div>
          Filterliste:<div hinweis="Releases mit diesen Begriffen werden nicht hinzugef&uuml;gt (durch Kommata getrennt)"><input type="text" name="rejectlist" value="''' + rejectlist +'''"></div>
          Auch per RegEx-Funktion suchen:<div hinweis="Wenn aktiviert werden in einer zweiten Suchdatei Serien nach Regex-Regeln gesucht"><input type="text" name="regex" value="''' + regex +'''"></div>
          <button type="submit">Speichern</button>
    </form>
    <form id="rsscrawler" enctype="multipart/form-data" method="post" action="listenspeichern">
          <h1>Suchlisten</h1>
          <div hinweis="Pro Zeile ein Filmtitel"><h3>Filme</h3></div>
          <textarea name="mbfilme">''' + self.getListe('MB_Filme') + '''</textarea>
          <div hinweis="Pro Zeile ein Serientitel für ganze Staffeln"><h3>Staffeln</h3></div>
          <textarea name="mbstaffeln">''' + self.getListe('MB_Staffeln') + '''</textarea>
          <div hinweis="Pro Zeile ein Serientitel"><h3>Serien</h3></div>
          <textarea name="sjserien">''' + self.getListe('SJ_Serien') + '''</textarea>
          <div hinweis="Pro Zeile ein Serientitel im RegEx-Format. Filter werden ignoriert! <DEUTSCH.*Serien.Titel.*.S01.*.720p.*-GROUP> sucht nach Releases der Gruppe GROUP von Staffel 1 der Serien Titel in 720p auf Deutsch. <Serien.Titel.*> sucht nach allen Releases von Serien Titel (nützlich, wenn man sonst HDTV aussortiert). <Serien.Titel.*.DL.*.720p.*> sucht nach zweisprachigen Releases in 720p von Serien Titel. <ENGLISCH.*Serien.Titel.*.1080p.*> sucht nach englischen Releases in Full-HD von Serien Titel. <(?!(Diese|Andere)).*Serie.*.DL.*.720p.*-(GROUP|ANDEREGROUP)> sucht nach Serie (aber nicht Diese Serie oder Andere Serie), zweisprachig und in 720p und ausschließlich nach Releases von GROUP oder ANDEREGROUP."><h3>Serien (RegEx)</h3></div>
          <textarea name="sjregex">''' + self.getListe('SJ_Serien_Regex') + '''</textarea>
          <button type="submit">Speichern</button>
    </form>
    <form id="rsscrawler" enctype="multipart/form-data" method="post" action="neustart?wert=1">
          <button type="submit">Neu starten</button>
    </form>
  </div>
  </body>
</html>'''

  # /log zeigt den Inhalt des RSScrawler.log
  @cherrypy.expose
  def log(self):
    # Wenn Log (noch) nicht vorhanden, Zeige Meldung
    if not os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'RSScrawler.log')):
      return "Kein Log vorhanden!"
    else:
      # Deklariere Pfad der Logdatei (relativ)
      logfile = open(os.path.join(os.path.dirname(sys.argv[0]), 'RSScrawler.log'))
      # Nutze String um Log in HTML anzuzeigen
      output = StringIO.StringIO()
      #Füge Meta-Tag hinzu, damit Log regelmäßig neu geladen wird
      output.write("<meta http-equiv='refresh' content='5'>")
      # Jede Zeile der RSScrawler.log wird eingelesen. Letzter Eintrag zuerst, zwecks Übersicht
      for lines in reversed(logfile.readlines()):
        # Der Newline-Charakter \n wird um den HTML Newline-Tag <br> ergänzt
        output.write(lines.replace("\n", "<br>\n"))
      return output.getvalue()

  @cherrypy.expose
  def speichern(self, jdownloader, port, prefix, interval, pushbulletapi, hoster, mbquality, ignore, historical, crawl3d, enforcedl, crawlseasons, seasonsquality, seasonssource, sjquality, rejectlist, regex):
    with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/RSScrawler.ini'), 'wb') as f:
      # RSScrawler Section:
      f.write("[RSScrawler]\n")
      f.write("jdownloader = " + jdownloader.encode('utf-8') + "\n")
      f.write("port = " + port + "\n")
      f.write("prefix = " + prefix.encode('utf-8') + "\n")
      f.write("interval = " + interval.encode('utf-8') + "\n")
      f.write("pushbulletapi = " + pushbulletapi.encode('utf-8') + "\n")
      f.write("hoster = " + hoster.encode('utf-8') + "\n")
      # MB Section:
      f.write("[MB]\n")
      f.write("quality = " + mbquality.encode('utf-8') + "\n")
      f.write("ignore = " + ignore.encode('utf-8') + "\n")
      f.write("historical = " + historical.encode('utf-8') + "\n")
      f.write("crawl3d = " + crawl3d.encode('utf-8') + "\n")
      f.write("enforcedl = " + enforcedl.encode('utf-8') + "\n")
      f.write("crawlseasons = " + crawlseasons.encode('utf-8') + "\n")
      f.write("seasonsquality = " + seasonsquality.encode('utf-8') + "\n")
      f.write("seasonssource = " + seasonssource.encode('utf-8') + "\n")
      # SJ Section:
      f.write("[SJ]\n")
      f.write("quality = " + sjquality.encode('utf-8') + "\n")
      f.write("rejectlist = " + rejectlist.encode('utf-8') + "\n")
      f.write("regex = " + regex.encode('utf-8') + "\n")
      checkFiles()
      return '''<!DOCTYPE html>
<html>
  <head>
    <style>
      @import url(https://fonts.googleapis.com/css?family=Roboto:400,300,600,400italic);.copyright,[hinweis]:before,div,h1,h2,h3,input{text-align:center}*{margin:0;padding:0;box-sizing:border-box;-webkit-box-sizing:border-box;-moz-box-sizing:border-box;-webkit-font-smoothing:antialiased;-moz-font-smoothing:antialiased;-o-font-smoothing:antialiased;font-smoothing:antialiased;text-rendering:optimizeLegibility}body{font-family:Roboto,Helvetica,Arial,sans-serif;font-weight:100;font-size:14px;line-height:30px;color:#000;background:#d3d3d3}.container{max-width:800px;width:100%;margin:0 auto;position:relative}[hinweis]:after,[hinweis]:before{position:absolute;bottom:150%;left:50%}#rsscrawler button[type=submit],#rsscrawler iframe,#rsscrawler input[type=text],#rsscrawler textarea{font:400 12px/16px Roboto,Helvetica,Arial,sans-serif}#rsscrawler{background:#F9F9F9;padding:25px;margin:50px 0;box-shadow:0 0 20px 0 rgba(0,0,0,.2),0 5px 5px 0 rgba(0,0,0,.24)}#rsscrawler h1{display:block;font-size:30px;font-weight:300;margin-bottom:10px}#rsscrawler h4{margin:5px 0 15px;display:block;font-size:13px;font-weight:400}fieldset{border:none!important;margin:0 0 10px;min-width:100%;padding:0;width:100%}#rsscrawler iframe,#rsscrawler input[type=text],#rsscrawler textarea{width:100%;border:1px solid #ccc;background:#FFF;margin:0 0 5px;padding:10px}#rsscrawler iframe,#rsscrawler input[type=text]:hover,#rsscrawler textarea:hover{-webkit-transition:border-color .3s ease-in-out;-moz-transition:border-color .3s ease-in-out;transition:border-color .3s ease-in-out;border:1px solid #aaa}#rsscrawler textarea{height:100px;max-width:100%;resize:none}#rsscrawler button[type=submit]{cursor:pointer;width:100%;border:none;background:#333;color:#FFF;margin:0 0 5px;padding:10px;font-size:15px}#rsscrawler button[type=submit]:hover{background:#43A047;-webkit-transition:background .3s ease-in-out;-moz-transition:background .3s ease-in-out;transition:background-color .3s ease-in-out}#rsscrawler button[type=submit]:active{box-shadow:inset 0 1px 3px rgba(0,0,0,.5)}#rsscrawler input:focus,#rsscrawler textarea:focus{outline:0;border:1px solid #aaa}::-webkit-input-placeholder{color:#888}:-moz-placeholder{color:#888}::-moz-placeholder{color:#888}:-ms-input-placeholder{color:#888}[hinweis]{position:relative;z-index:2;cursor:pointer}[hinweis]:after,[hinweis]:before{visibility:hidden;-ms-filter:"progid:DXImageTransform.Microsoft.Alpha(Opacity=0)";filter:progid: DXImageTransform.Microsoft.Alpha(Opacity=0);opacity:0;pointer-events:none}[hinweis]:before{margin-bottom:5px;margin-left:-400px;padding:9px;width:782px;-webkit-border-radius:3px;-moz-border-radius:3px;border-radius:0;background-color:#000;background-color:hsla(0,0%,20%,.9);color:#fff;content:attr(hinweis);font-size:14px;line-height:1.2}[hinweis]:after{margin-left:-5px;width:0;border-top:5px solid #000;border-top:5px solid hsla(0,0%,20%,.9);border-right:5px solid transparent;border-left:5px solid transparent;content:" ";font-size:0;line-height:0}[hinweis]:hover:after,[hinweis]:hover:before{visibility:visible;-ms-filter:"progid:DXImageTransform.Microsoft.Alpha(Opacity=100)";filter:progid: DXImageTransform.Microsoft.Alpha(Opacity=100);opacity:1}
    </style>
  </head>
  <body>
  <div class="container">
    <form id="rsscrawler" enctype="multipart/form-data" method="post" action="../''' + prefix.encode('utf-8') + '''">
          <h1>Gespeichert!</h1>
          Die Einstellungen wurden gespeichert.
          <button type="submit">Zurück</button>
    </form>
    <form id="rsscrawler" enctype="multipart/form-data" method="post" action="neustart?wert=1">
          <h1>Hinweis</h1>
          Um einige Änderungen anzunehmen muss RSScrawler neu gestartet werden!
          <button type="submit">Neu starten</button>
    </form>
  </div>
  </body>
</html>'''

  @cherrypy.expose
  def listenspeichern(self, mbfilme, mbstaffeln, sjserien, sjregex):
    main = RssConfig('RSScrawler')
    prefix = main.get("prefix")
    with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/MB_Filme.txt'), 'wb') as f:
      f.write(mbfilme.encode('utf-8'))
    with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/MB_Staffeln.txt'), 'wb') as f:
      f.write(mbstaffeln.encode('utf-8'))
    with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/SJ_Serien.txt'), 'wb') as f:
      f.write(sjserien.encode('utf-8'))
    with open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/SJ_Serien_Regex.txt'), 'wb') as f:
      f.write(sjregex.encode('utf-8'))
    checkFiles()
    return '''<!DOCTYPE html>
<html>
  <head>
    <style>
      @import url(https://fonts.googleapis.com/css?family=Roboto:400,300,600,400italic);.copyright,[hinweis]:before,div,h1,h2,h3,input{text-align:center}*{margin:0;padding:0;box-sizing:border-box;-webkit-box-sizing:border-box;-moz-box-sizing:border-box;-webkit-font-smoothing:antialiased;-moz-font-smoothing:antialiased;-o-font-smoothing:antialiased;font-smoothing:antialiased;text-rendering:optimizeLegibility}body{font-family:Roboto,Helvetica,Arial,sans-serif;font-weight:100;font-size:14px;line-height:30px;color:#000;background:#d3d3d3}.container{max-width:800px;width:100%;margin:0 auto;position:relative}[hinweis]:after,[hinweis]:before{position:absolute;bottom:150%;left:50%}#rsscrawler button[type=submit],#rsscrawler iframe,#rsscrawler input[type=text],#rsscrawler textarea{font:400 12px/16px Roboto,Helvetica,Arial,sans-serif}#rsscrawler{background:#F9F9F9;padding:25px;margin:50px 0;box-shadow:0 0 20px 0 rgba(0,0,0,.2),0 5px 5px 0 rgba(0,0,0,.24)}#rsscrawler h1{display:block;font-size:30px;font-weight:300;margin-bottom:10px}#rsscrawler h4{margin:5px 0 15px;display:block;font-size:13px;font-weight:400}fieldset{border:none!important;margin:0 0 10px;min-width:100%;padding:0;width:100%}#rsscrawler iframe,#rsscrawler input[type=text],#rsscrawler textarea{width:100%;border:1px solid #ccc;background:#FFF;margin:0 0 5px;padding:10px}#rsscrawler iframe,#rsscrawler input[type=text]:hover,#rsscrawler textarea:hover{-webkit-transition:border-color .3s ease-in-out;-moz-transition:border-color .3s ease-in-out;transition:border-color .3s ease-in-out;border:1px solid #aaa}#rsscrawler textarea{height:100px;max-width:100%;resize:none}#rsscrawler button[type=submit]{cursor:pointer;width:100%;border:none;background:#333;color:#FFF;margin:0 0 5px;padding:10px;font-size:15px}#rsscrawler button[type=submit]:hover{background:#43A047;-webkit-transition:background .3s ease-in-out;-moz-transition:background .3s ease-in-out;transition:background-color .3s ease-in-out}#rsscrawler button[type=submit]:active{box-shadow:inset 0 1px 3px rgba(0,0,0,.5)}#rsscrawler input:focus,#rsscrawler textarea:focus{outline:0;border:1px solid #aaa}::-webkit-input-placeholder{color:#888}:-moz-placeholder{color:#888}::-moz-placeholder{color:#888}:-ms-input-placeholder{color:#888}[hinweis]{position:relative;z-index:2;cursor:pointer}[hinweis]:after,[hinweis]:before{visibility:hidden;-ms-filter:"progid:DXImageTransform.Microsoft.Alpha(Opacity=0)";filter:progid: DXImageTransform.Microsoft.Alpha(Opacity=0);opacity:0;pointer-events:none}[hinweis]:before{margin-bottom:5px;margin-left:-400px;padding:9px;width:782px;-webkit-border-radius:3px;-moz-border-radius:3px;border-radius:0;background-color:#000;background-color:hsla(0,0%,20%,.9);color:#fff;content:attr(hinweis);font-size:14px;line-height:1.2}[hinweis]:after{margin-left:-5px;width:0;border-top:5px solid #000;border-top:5px solid hsla(0,0%,20%,.9);border-right:5px solid transparent;border-left:5px solid transparent;content:" ";font-size:0;line-height:0}[hinweis]:hover:after,[hinweis]:hover:before{visibility:visible;-ms-filter:"progid:DXImageTransform.Microsoft.Alpha(Opacity=100)";filter:progid: DXImageTransform.Microsoft.Alpha(Opacity=100);opacity:1}
    </style>
  </head>
  <body>
  <div class="container">
    <form id="rsscrawler" enctype="multipart/form-data" method="post" action="../''' + prefix.encode('utf-8') + '''">
          <h1>Gespeichert!</h1>
          <button type="submit">Zurück</button>
    </form>
    <form id="rsscrawler" enctype="multipart/form-data" method="post" action="neustart?wert=1">
          <h1>Hinweis</h1>
          Um direkt nach den neuen Listeneinträgen zu suchen muss neu gestartet werden
          <button type="submit">Neu starten</button>
    </form>
  </div>
  </body>
</html>'''
      
  @cherrypy.expose
  def neustart(self, wert):
    if wert == '1':
      os.execl(sys.executable, sys.executable, *sys.argv)
      return "Neustart Ausgeführt"
    else:
      return "Kein Neustart ohne Bestätigung"
      
  def getListe(self, liste):
    if not os.path.isfile(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/' + liste + '.txt')):
      return "Liste nicht gefunden"
    else:
      file = open(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Listen/' + liste + '.txt'))
      output = StringIO.StringIO()
      for line in file.readlines():
        output.write(line)
      return output.getvalue()

  @classmethod
  def run(cls, prefix):
    cherrypy.quickstart(cls(), '/' + prefix, 'cherry.conf')
    
  def start(self, port, prefix):
    # Deaktiviere Cherrypy Log
    cherrypy.log.error_log.propagate = False
    cherrypy.log.access_log.propagate = False
    # Setze das Port entsprechend des Aufrufs
    cherrypy.config.update({'server.socket_port': port})
    # Setzte den Pfad der Webanwendung entsprechend des Aufrufs
    self.run(prefix)