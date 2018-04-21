#!/bin/bash
# RSScrawler
# Projekt von https://github.com/rix1337
# Enthält Code von:
# https://github.com/rix1337/RSScrawler/issues/88#issuecomment-251078409
# https://github.com/rix1337/RSScrawler/issues/7#issuecomment-271187968

VERSION="v.4.2.5"
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
    apt-get --yes --force-yes install git python2.7 python-setuptools python-dev nodejs libxml2-dev libxslt-dev
    easy_install pip
    pip install --upgrade pip virtualenv virtualenvwrapper
    clear
    read -rp "Wohin soll RSScrawler installiert werden? Das Verzeichnis RSScrawler wird automatisch erstellt! Pfad ohne / am Ende: " rsspath
    read -rp "Wo ist der JDownloader installiert? Pfad ohne / am Ende: " jdpath
    read -rp "Auf welchem Port soll das Webinterface erreichbar sein? Port: " rssport
    mkdir -p $rsspath/
    cd $rsspath/
    git clone https://github.com/rix1337/RSScrawler.git
    cd RSScrawler
    pip install -r requirements.txt
    git remote add rss https://github.com/rix1337/RSScrawler.git
    clear
    echo "Der Webserver sollte nie ohne adequate Absicherung im Internet freigegeben werden. Dazu empfiehlt sich ein Reverse-Proxy bspw. über nginx mit Letsencrypt (automatisches, kostenloses HTTPs-Zertifikat), HTTPauth (Passwortschutz - Nur sicher über HTTPs!) und fail2ban (limitiert falsche Logins pro IP)."
    python RSScrawler.py --port=$rssport --jd-pfad="$jdpath" &
    exit
   elif [ "$opt" = "Synology" ]; then
    echo "Es müssen Git, Python 2.7, JDownloader 2 und Java 8 installiert sein (optional auch node.js)!"
    read -rsp $'Durch Tastendruck bestätigen...\n' -n 1 key
    cd /volume1/@appstore/PythonModule/usr/lib/python2.7/site-packages/
    python easy_install.py pip
    pip install --upgrade pip virtualenv virtualenvwrapper
    cd /volume1/@appstore/
    git clone https://github.com/rix1337/RSScrawler.git
    cd RSScrawler
    chmod +x * /volume1/@appstore/RSScrawler
    pip install -r requirements.txt
    clear
    read -rp "Wo ist der JDownloader installiert? Pfad ohne / am Ende: " jdpath
    read -rp "Auf welchem Port soll das Webinterface erreichbar sein? Port: " rssport
    clear
    echo "Der Webserver sollte nie ohne adequate Absicherung im Internet freigegeben werden. Dazu empfiehlt sich ein Reverse-Proxy bspw. über nginx mit Letsencrypt (automatisches, kostenloses HTTPs-Zertifikat), HTTPauth (Passwortschutz - Nur sicher über HTTPs!) und fail2ban (limitiert falsche Logins pro IP)."
    python RSScrawler.py --port=$rssport --jd-pfad="$jdpath" &
    exit
   elif [ "$opt" = "Update" ]; then
    read -rp "Wo ist RSScrawler installiert? Pfad ohne / am Ende: " rsspath
    cd $rsspath/
    pip install -U -r requirements.txt
    git fetch --all
    git reset --hard origin/master
    git pull origin master
    exit
   else
    clear
    echo "Bitte eine vorhandene Option wählen"
    exit
   fi
done
