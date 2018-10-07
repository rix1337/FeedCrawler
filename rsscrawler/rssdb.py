# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

import sqlite3


def get_first(iterable):
    return iterable and list(iterable[:1]).pop() or None


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
        key = key.replace('.', ' ').replace(';', '').replace(',', '').replace(u'Ä',
                                                                                                         'Ae').replace(
            u'ä', 'ae').replace(u'Ö', 'Oe').replace(u'ö', 'oe').replace(u'Ü', 'Ue').replace(u'ü', 'ue').replace(
            u'ß', 'ss').replace('(', '').replace(')', '').replace(u'*', '').replace(u'|', '').replace('\\', '').replace(
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
                    k = k.replace('.', ' ').replace(';', '').replace(',', '').replace(u'Ä', 'Ae').replace(
                        u'ä', 'ae').replace(u'Ö', 'Oe').replace(u'ö', 'oe').replace(u'Ü', 'Ue').replace(u'ü',
                                                                                                        'ue').replace(
                        u'ß', 'ss').replace('(', '').replace(')', '').replace('*', '').replace('|', '').replace('\\',
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
