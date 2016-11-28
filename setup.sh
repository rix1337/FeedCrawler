#!/bin/bash
# RSScrawler - Version 2.3.0
# Projekt von https://github.com/rix1337
# Enthält Code von:
# https://github.com/rix1337/RSScrawler/issues/88#issuecomment-251078409

# Setup
apt-get update
apt-get --yes --force-yes install git python2.7 python-setuptools python-beautifulsoup libxml2-dev libxslt-dev python-dev lib32z1-dev git
easy_install pip
pip install --upgrade pip virtualenv virtualenvwrapper
pip install docopt feedparser lxml requests cherrypy

# Konsole zur Übersicht leeren
clear

# Abfrage nach Einstellungswünschen
read -rp "Wohin soll RSScrawler installiert werden? Das Verzeichnis RSScrawler wird automatisch erstellt! Pfad ohne / am Ende: " rsspath
read -rp "Wo ist der JDownloader installiert? Pfad ohne / am Ende: " jdpath
read -rp "Auf welchem Port soll das Webinterface erreichbar sein? Port: " rssport

# Lade aktuellen RSScrawler
mkdir -p $rsspath/
cd $rsspath/
git clone https://github.com/rix1337/RSScrawler.git
cd RSScrawler
git remote add rss https://github.com/rix1337/RSScrawler.git

# Konsole zur Übersicht leeren
clear

# Starte RSSCrawler
python RSScrawler.py --port=$rssport --jd-pfad="$jdpath" &
