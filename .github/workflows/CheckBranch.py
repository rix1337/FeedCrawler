# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Script prüft, ob Versionsnummern und Changelog gegenüber main geändert wurden.

import json
import re
import subprocess
import sys
from urllib.request import urlopen


def semver_to_number(semver):
    number_parts = []
    alpha_parts = []

    parts = semver.split('.')
    for part in parts:
        alpha_string = "".join(filter(str.isalpha, part))
        numeric_string = "".join(filter(str.isdigit, part))

        if numeric_string:
            number_parts.append(int(numeric_string))

        if alpha_string:
            alpha_parts.append(sum(ord(char) for char in alpha_string))
    # Use negative values for alpha paarts to ensure stable versions are prioritized over pre-release versions
    return (number_parts, [-value for value in alpha_parts])


if __name__ == '__main__':
    python_version = ""
    try:
        result = subprocess.run(['python', 'feedcrawler/providers/version.py'], stdout=subprocess.PIPE)
        python_version = str(result.stdout.decode("utf-8")).strip()
    except:
        pass

    if not python_version:
        sys.exit('Version info missing in feedcrawler/providers/version.py')

    vue_version = ""
    try:
        with open('feedcrawler/web_interface/vuejs_frontend/package.json') as fp:
            data = json.load(fp)
            vue_version = str(data['version']).strip()
    except:
        pass

    if not vue_version:
        sys.exit('Version info missing in feedcrawler/web_interface/vuejs_frontend/package.json')

    if not python_version == vue_version:
        sys.exit(
            'Version info mismatch in feedcrawler/providers/version.py and feedcrawler/web_interface/vuejs_frontend/package.json')

    latest = urlopen('https://github.com/rix1337/FeedCrawler/releases/latest').read()
    latest_title = latest.decode("utf-8")
    latest_title_text = re.findall(r'<title>(.+)</title>', latest_title)[0]
    onlineversion = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3})', latest_title_text).group()
    if semver_to_number(python_version) > semver_to_number(onlineversion) and semver_to_number(
            vue_version) > semver_to_number(
        onlineversion):
        print("Proper version increase in branch detected.")
        sys.exit(0)
    else:
        sys.exit('Version not increased on branch')
