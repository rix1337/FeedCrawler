# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337
import re
import urllib2
from BeautifulSoup import BeautifulSoup

def getVersion():
    return "v.2.7.0"

def updateCheck():
    # Prüfe, ob lokale Version der aktuellen Entspricht
    localversion = getVersion()
    try:
        # Einzeiler, der die aktuelle Version von GitHub ausliest:
        onlineversion = str(re.search('return "(.+?)"', BeautifulSoup(urllib2.urlopen('https://raw.githubusercontent.com/rix1337/RSScrawler/master/version.py').read()).findAll(text=re.compile('return "(v\.\d\.\d\.\d)"'))[0]).group(1))
        if localversion == onlineversion:
            return (False, localversion)
        else:
            return (True, onlineversion)
    except:
        return (False, "Error")
