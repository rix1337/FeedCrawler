# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import sqlite3
import os
import sys


def get_first(iterable):
    return iterable and list(iterable[:1]).pop() or None


def merge_old():
    def connect(file):
        return sqlite3.connect(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Downloads/' + file + '.db'), check_same_thread=False)

    def read(connection):
        return connection.execute("SELECT key, value FROM 'data'")

    conn_old1 = connect('MB_Downloads')
    conn_old2 = connect('SJ_Downloads')
    conn_old3 = connect('YT_Downloads')
    conn_new = connect('Downloads')

    if not conn_new.execute("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'rsscrawler';").fetchall():
        conn_new.execute("CREATE TABLE 'rsscrawler' (key, value)")
        conn_new.commit()

    res_old = []
    res_old.append(read(conn_old1))
    res_old.append(read(conn_old2))
    res_old.append(read(conn_old3))

    for res in res_old:
        for key, value in res:
            conn_new.execute("INSERT INTO '%s' VALUES ('%s', '%s')" % (
                'rsscrawler', key, value.lower().replace('downloaded', 'added')))
            conn_new.commit()

    return True


class RssDb(object):
    def __init__(self, file, table):
        self._conn = sqlite3.connect(file, check_same_thread=False)
        self._table = table
        if not self._conn.execute("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = '%s';" % self._table).fetchall():
            self._conn.execute(
                '''CREATE TABLE %s (key, value)''' % self._table)
            self._conn.commit()

    def retrieve(self, key):
        res = self._conn.execute(
            "SELECT value FROM %s WHERE key='%s'" % (self._table, key)).fetchone()
        return res[0] if res else None

    def store(self, key, value):
        self._conn.execute("INSERT INTO '%s' VALUES ('%s', '%s')" %
                           (self._table, key, value))
        self._conn.commit()

    def delete(self, key):
        self._conn.execute("DELETE FROM %s WHERE key='%s'" %
                           (self._table, key))
        self._conn.commit()
