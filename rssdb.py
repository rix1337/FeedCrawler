# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

from builtins import str
from builtins import object
import os
import sqlite3
import sys


def get_first(iterable):
    return iterable and list(iterable[:1]).pop() or None


# Merge Pre-v.4.1.x-Databases into v.4.1.x-Database
def merge_old():
    def connect(file):
        return sqlite3.connect(os.path.join(os.path.dirname(sys.argv[0]), 'Einstellungen/Downloads/' + file + '.db'),
                               check_same_thread=False)

    def read(connection):
        return connection.execute("SELECT key, value FROM 'data'")

    conn_old1 = connect('MB_Downloads')
    conn_old2 = connect('SJ_Downloads')
    conn_old3 = connect('YT_Downloads')
    conn_new = connect('Downloads')

    if not conn_new.execute("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'rsscrawler';").fetchall():
        conn_new.execute("CREATE TABLE 'rsscrawler' (key, value)")
        conn_new.commit()

    res_old = [read(conn_old1), read(conn_old2), read(conn_old3)]

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
        if not self._conn.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = '%s';" % self._table).fetchall():
            self._conn.execute("CREATE TABLE %s (key, value)" % self._table)
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

    def reset(self):
        self._conn.execute("DROP TABLE %s" % self._table)
        self._conn.commit()


class ListDb(object):
    def __init__(self, file, table):
        self._conn = sqlite3.connect(file, check_same_thread=False)
        self._table = table
        if not self._conn.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = '%s';" % self._table).fetchall():
            self._conn.execute(
                '''CREATE TABLE %s (key)''' % self._table)
            self._conn.commit()

    def retrieve(self):
        res = self._conn.execute(
            "SELECT distinct key FROM %s ORDER BY key" % self._table)
        items = []
        for r in res:
            items.append(str(r[0]))
        return items if items else None

    def store(self, key):
        key = key.encode('ascii', 'replace').replace('.', ' ').replace(';', '').replace(',', '').replace('Ä',
                                                                                                         'Ae').replace(
            'ä', 'ae').replace('Ö', 'Oe').replace('ö', 'oe').replace('Ü', 'Ue').replace('ü', 'ue').replace(
            'ß', 'ss').replace('(', '').replace(')', '').replace('*', '').replace('|', '').replace('\\', '').replace(
            '/', '').replace('?', '').replace('!', '').replace(':', '').replace('  ', ' ').replace("'", '')
        self._conn.execute("INSERT INTO '%s' VALUES ('%s')" %
                           (self._table, key))
        self._conn.commit()

    def store_list(self, keys):
        items = []
        if not "_Regex" in self._table:
            for k in keys:
                if k:
                    key = ()
                    k = k.encode('ascii', 'replace').replace('.', ' ').replace(';', '').replace(',', '').replace('Ä',
                                                                                                                 'Ae').replace(
                        'ä', 'ae').replace('Ö', 'Oe').replace('ö', 'oe').replace('Ü', 'Ue').replace('ü', 'ue').replace(
                        'ß', 'ss').replace('(', '').replace(')', '').replace('*', '').replace('|', '').replace('\\',
                                                                                                               '').replace(
                        '/', '').replace('?', '').replace('!', '').replace(':', '').replace('  ', ' ').replace("'", '')
                    key = key + (k,)
                    items.append(key)
        else:
            for k in keys:
                if k:
                    key = ()
                    key = key + (k,)
                    items.append(key)
        self._conn.execute("DELETE FROM %s" % self._table)
        self._conn.executemany(
            "INSERT INTO '%s' (key) VALUES (?)" % self._table, items)
        self._conn.commit()

    def delete(self, key):
        self._conn.execute("DELETE FROM %s WHERE key='%s'" %
                           (self._table, key))
        self._conn.commit()
