# -*- coding: utf-8 -*-
# RSScrawler - Version 1.9.0
# Projekt von https://github.com/rix1337
# Enthält Code von:
# https://github.com/dmitryint (im Auftrag von https://github.com/rix1337)

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
