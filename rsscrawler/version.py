# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import re

from six.moves.urllib.request import urlopen


def get_version():
    return "v.5.2.6"


def update_check():
    localversion = get_version().replace("v.", "").split(".")
    try:
        onlineversion = re.search(r'Release (v\.\d{1,2}\.\d{1,2}\.\d{1,2})', urlopen(
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
            else:
                update = False
        if update:
            return True, "v." + ".".join(onlineversion)
        else:
            return False, "v." + ".".join(localversion)
    except:
        return False, "Error"
