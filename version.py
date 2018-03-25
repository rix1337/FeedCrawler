# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import re
import sys
try:
    # For Python 2.0 and later
    import urllib2
except ImportError:
    # For Python 3.0 and later
    import urllib.request as urllib2


def getVersion():
    return "v.4.0.9"

def updateCheck():
    localversion = getVersion()
    try:
        onlineversion = re.search(r'return "(v\.\d{1,2}\.\d{1,2}\.\d{1,2})"', urllib2.urlopen('https://raw.githubusercontent.com/rix1337/RSScrawler/master/version.py').read()).group(1)
        if localversion == onlineversion:
            return (False, localversion)
        else:
            return (True, onlineversion)
    except:
        return (False, "Error")
