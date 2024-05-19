# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt notwendige Funktionen zur aktuellen Version und Update-Prüfung des FeedCrawlers bereit.

import re
from distutils.version import StrictVersion
from urllib.request import urlopen


def get_version():
    return "19.2.0"


def create_version_file():
    version = get_version()
    version_clean = re.sub('[^\d\.]', '', version)
    if "a" in version:
        suffix = version.split("a")[1]
    else:
        suffix = 0
    version_split = version_clean.split(".")
    version_info = [
        "VSVersionInfo(",
        "  ffi=FixedFileInfo(",
        "    filevers=(" + str(int(version_split[0])) + ", " + str(int(version_split[1])) + ", " + str(
            int(version_split[2])) + ", " + str(int(suffix)) + "),",
        "    prodvers=(" + str(int(version_split[0])) + ", " + str(int(version_split[1])) + ", " + str(
            int(version_split[2])) + ", " + str(int(suffix)) + "),",
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
        "        StringStruct(u'FileVersion', u'" + str(int(version_split[0])) + "." + str(
            int(version_split[1])) + "." + str(int(version_split[2])) + "." + str(int(suffix)) + "'),",
        "        StringStruct(u'InternalName', u'FeedCrawler'),",
        "        StringStruct(u'LegalCopyright', u'Copyright © RiX'),",
        "        StringStruct(u'OriginalFilename', u'FeedCrawler.exe'),",
        "        StringStruct(u'ProductName', u'FeedCrawler'),",
        "        StringStruct(u'ProductVersion', u'" + str(int(version_split[0])) + "." + str(
            int(version_split[1])) + "." + str(int(version_split[2])) + "." + str(int(suffix)) + "')])",
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
        latest_title = latest.decode("utf-8")
        latest_title_text = re.findall(r'<title>(.+)</title>', latest_title)[0]
        onlineversion = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3})', latest_title_text).group()
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
