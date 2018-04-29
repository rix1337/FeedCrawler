# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import re
import urllib2


def getVersion():
    return "v.4.2.6"


def updateCheck():
    localversion = getVersion().replace("v.", "").split(".")
    try:
        onlineversion = re.search(r'Release (v\.\d{1,2}\.\d{1,2}\.\d{1,2})', urllib2.urlopen(
            'https://github.com/rix1337/RSScrawler/releases/latest').read()).group(1).replace("v.", "").split(".")
        if localversion == onlineversion:
            update = False
        else:
            if localversion[2] < onlineversion[2]:
                update = True
            elif localversion[1] < onlineversion[1]:
                update = True
            elif localversion[0] < onlineversion[0]:
                update = True
        if update:
            return (True, "v." + ".".join(onlineversion))
        else:
            return (False, "v." + ".".join(localversion))
    except:
        return (False, "Error")
