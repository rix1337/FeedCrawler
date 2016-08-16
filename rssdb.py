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

import common
import sqlite3


class RssDb(object):
    def __init__(self, file):
        self._conn = sqlite3.connect(file, check_same_thread=False)
        self._table = 'data'
        if not self._conn.execute("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = '%s';" % self._table).fetchall():
            self._conn.execute('''CREATE TABLE %s (key, value, pattern)''' % self._table)
            self._conn.commit()

    def retrieve(self, key):
        res = self._conn.execute("SELECT value FROM %s WHERE key='%s'" % (self._table, key)).fetchone()
        return res[0] if res else None

    def store(self, key, value, pattern=''):
        self._conn.execute("INSERT INTO '%s' VALUES ('%s', '%s', '%s')" %('data', key, value, pattern))
        self._conn.commit()

    def get_patterns(self, f):
        return [common.get_first(el) for el in self._conn.execute(
            "SELECT pattern FROM data WHERE value='%s'" % f).fetchall()]
