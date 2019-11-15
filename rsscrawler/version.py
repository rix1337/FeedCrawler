# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import re
from distutils.version import StrictVersion as version

from bs4 import BeautifulSoup
from urllib.request import urlopen


def get_version():
    return "v.6.0.11"


def update_check():
    localversion = get_version().replace("v.", "")
    try:
        latest = urlopen('https://github.com/rix1337/RSScrawler/releases/latest').read()
        latest_title = BeautifulSoup(latest, 'lxml').find("title").text
        onlineversion = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3})', latest_title).group()
        if version(localversion) < version(onlineversion):
            update = True
        else:
            update = False
        if update:
            return True, "v." + "".join(onlineversion)
        else:
            return False, "v." + "".join(localversion)
    except:
        return False, "Error"
