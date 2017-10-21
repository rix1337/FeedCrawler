#!/bin/bash
# RSScrawler
# Projekt von https://github.com/rix1337
# Enthält Code von:
# https://github.com/rix1337/RSScrawler/issues/88#issuecomment-251078409
# https://github.com/rix1337/RSScrawler/issues/7#issuecomment-271187968

VERSION="v.3.0.8"
echo "┌────────────────────────────────────────────────────────┐"
echo "  Programminfo:    RSScrawler $VERSION von RiX"
echo "  Projektseite:    https://github.com/rix1337/RSScrawler"
echo "└────────────────────────────────────────────────────────┘"
echo "Hinweise im Wiki: https://github.com/rix1337/RSScrawler/wiki"
echo "Bitte Plattform wählen:"
OPTIONS="Ubuntu/Debian Synology Update Beenden"
select opt in $OPTIONS; do
   if [ "$opt" = "Beenden" ]; then
    exit
   elif [ "$opt" = "Ubuntu/Debian" ]; then
    apt-get update
    apt-get --yes --force-yes install git python2.7 python-setuptools python-dev
    easy_install pip
    pip install --upgrade pip virtualenv virtualenvwrapper
    pip install bs4 docopt feedparser cherrypy lxml
    clear
    read -rp "Wohin soll RSScrawler installiert werden? Das Verzeichnis RSScrawler wird automatisch erstellt! Pfad ohne / am Ende: " rsspath
    read -rp "Wo ist der JDownloader installiert? Pfad ohne / am Ende: " jdpath
    read -rp "Auf welchem Port soll das Webinterface erreichbar sein? Port: " rssport
    mkdir -p $rsspath/
    cd $rsspath/
    git clone https://github.com/rix1337/RSScrawler.git
    cd RSScrawler
    git remote add rss https://github.com/rix1337/RSScrawler.git
    clear
    python RSScrawler.py --port=$rssport --jd-pfad="$jdpath" &
    exit
   elif [ "$opt" = "Synology" ]; then
    echo "Es müssen Python 2.7, JDownloader 2 und Java 8 installiert sein!"
    read -rsp $'Durch Tastendruck bestätigen...\n' -n 1 key
    cd /volume1/@appstore/PythonModule/usr/lib/python2.7/site-packages/
    python easy_install.py pip
    pip install --upgrade pip virtualenv virtualenvwrapper
    pip install bs4 docopt feedparser requests cherrypy lxml
    cd /volume1/@appstore/
    wget https://github.com/rix1337/RSScrawler/archive/master.zip
    7z x master.zip
    rm /volume1/@appstore/master.zip
    cd /volume1/@appstore/RSScrawler-master
    chmod +x * /volume1/@appstore/RSScrawler-master
    clear
    read -rp "Wo ist der JDownloader installiert? Pfad ohne / am Ende: " jdpath
    read -rp "Auf welchem Port soll das Webinterface erreichbar sein? Port: " rssport
    clear
    python RSScrawler.py --port=$rssport --jd-pfad="$jdpath" &
    exit
   elif [ "$opt" = "Update" ]; then
    read -rp "Wo ist RSScrawler installiert? Pfad ohne / am Ende: " rsspath
    cd $rsspath/
    git fetch --all
    git reset --hard origin/master
    git pull origin master
    exit
   else
    clear
    echo "Fehlauswahl"
    exit
   fi
done
