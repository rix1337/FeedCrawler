# -*- coding: utf-8 -*-
import sqlite3


class RssDb(object):
    def __init__(self, file):
        self._conn = sqlite3.connect(file, check_same_thread=False)
        self._table = 'data'
        if not self._conn.execute("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = '%s';" % self._table).fetchall():
            self._conn.execute('''CREATE TABLE %s (key, value)''' % self._table)
            self._conn.commit()

    def retrieve(self, key):
        res = self._conn.execute("SELECT value FROM %s WHERE key='%s'" % (self._table, key)).fetchone()
        return res[0] if res else None

    def store(self, key, value):
        self._conn.execute("INSERT INTO '%s' VALUES ('%s', '%s')" %('data', key, value))
        self._conn.commit()
