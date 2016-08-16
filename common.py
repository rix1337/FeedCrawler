# -*- coding: utf-8 -*-
# RSScrawler - Version 1.6.7
# Projekt von https://github.com/rix1337
# Enthaltener Code
# https://github.com/dmitryint (im Auftrag von https://github.com/rix1337)
# https://github.com/zapp-brannigan/own-pyload-plugins/blob/master/hooks/MovieblogFeed.py
# https://github.com/Gutz-Pilz/pyLoad-stuff/blob/master/SJ.py
# https://github.com/bharnett/Infringer/blob/master/LinkRetrieve.py
# Beschreibung:
# RSScrawler durchsucht MB/SJ nach in .txt Listen hinterlegten Titeln und reicht diese im .crawljob Format an JDownloader weiter.

def get_first(iterable):
    return iterable and list(iterable[:1]).pop() or None
