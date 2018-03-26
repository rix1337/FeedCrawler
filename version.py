# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

# import python modules
import re
import urllib.request, urllib.error, urllib.parse


def getVersion():
    return "v.4.1.0"

def updateCheck():
    localversion = getVersion()
    try:
        onlineversion = re.search(r'return "(v\.\d{1,2}\.\d{1,2}\.\d{1,2})"', urllib.request.urlopen(
            'https://raw.githubusercontent.com/rix1337/RSScrawler/master/version.py').read()).group(1)
        if localversion == onlineversion:
            return (False, localversion)
        else:
            return (True, onlineversion)
    except:
        return (False, "Error")
