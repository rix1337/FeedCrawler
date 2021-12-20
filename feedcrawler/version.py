# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337

import re
from distutils.version import StrictVersion
from urllib.request import urlopen

from bs4 import BeautifulSoup


def get_version():
    return "12.0.5"


def create_version_file():
    version_clean = re.sub('[^\d\.]', '', get_version())
    version_split = version_clean.split(".")
    version_info = [
        "VSVersionInfo(",
        "  ffi=FixedFileInfo(",
        "    filevers=(" + version_split[0] + ", " + version_split[1] + ", " + version_split[2] + ", 0),",
        "    prodvers=(" + version_split[0] + ", " + version_split[1] + ", " + version_split[2] + ", 0),",
        "    mask=0x3f,",
        "    flags=0x0,",
        "    OS=0x4,",
        "    fileType=0x1,",
        "    subtype=0x0,",
        "    date=(0, 0)",
        "    ),",
        "  kids=[",
        "    StringFileInfo(",
        "      [",
        "      StringTable(",
        "        u'040704b0',",
        "        [StringStruct(u'CompanyName', u'RiX'),",
        "        StringStruct(u'FileDescription', u'FeedCrawler'),",
        "        StringStruct(u'FileVersion', u'" + version_clean + ".0'),",
        "        StringStruct(u'InternalName', u'FeedCrawler'),",
        "        StringStruct(u'LegalCopyright', u'Copyright © RiX'),",
        "        StringStruct(u'OriginalFilename', u'FeedCrawler.exe'),",
        "        StringStruct(u'ProductName', u'FeedCrawler'),",
        "        StringStruct(u'ProductVersion', u'" + version_clean + ".0')])",
        "      ]),",
        "    VarFileInfo([VarStruct(u'Translation', [1031, 1200])])",
        "  ]",
        ")"
    ]
    print("\n".join(version_info), file=open('file_version_info.txt', 'w', encoding='utf-8'))


def update_check():
    localversion = get_version()
    try:
        latest = urlopen('https://github.com/rix1337/FeedCrawler/releases/latest').read()
        latest_title = BeautifulSoup(latest, 'lxml').find("title").text
        onlineversion = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3})', latest_title).group()
        if StrictVersion(localversion) < StrictVersion(onlineversion):
            update = True
        else:
            update = False
        if update:
            return True, "v." + "".join(onlineversion)
        else:
            return False, "v." + "".join(localversion)
    except:
        return False, "Error"


if __name__ == '__main__':
    print(get_version())
    create_version_file()
