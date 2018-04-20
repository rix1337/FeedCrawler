# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import re
import urllib2


def getVersion():
    return "v.4.2.4"


def updateCheck():
    localversion = getVersion()
    try:
        onlineversion = re.search(r'Release (v\.\d{1,2}\.\d{1,2}\.\d{1,2})', urllib2.urlopen(
            'https://github.com/rix1337/RSScrawler/releases/latest').read()).group(1)
        if localversion == onlineversion:
            return (False, localversion)
        else:
            return (True, onlineversion)
    except:
        return (False, "Error")
