# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul stellt die SQlite-Datenbank für den FeedCrawler bereit.

import sqlite3
import time

import feedcrawler.providers.common_functions
from feedcrawler.providers import shared_state


def get_first(iterable):
    return iterable and list(iterable[:1]).pop() or None


class FeedDb(object):
    def __init__(self, table):
        try:
            self._conn = sqlite3.connect(shared_state.dbfile, check_same_thread=False, timeout=5)
            self._table = table
            if not self._conn.execute(
                    "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = '%s';" % self._table).fetchall():
                self._conn.execute("CREATE TABLE %s (key, value)" % self._table)
                self._conn.commit()
        except sqlite3.OperationalError as e:
            try:
                shared_state.logger.debug(
                    "Fehler bei Zugriff auf FeedCrawler.db: " + str(e) + " (neuer Versuch in 5 Sekunden).")
                time.sleep(5)
                self._conn = sqlite3.connect(shared_state.dbfile, check_same_thread=False, timeout=10)
                self._table = table
                if not self._conn.execute(
                        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = '%s';" % self._table).fetchall():
                    self._conn.execute("CREATE TABLE %s (key, value)" % self._table)
                    self._conn.commit()
                    shared_state.logger.debug("Zugriff auf FeedCrawler.db nach Wartezeit war erfolgreich.")
            except sqlite3.OperationalError as e:
                print("Fehler bei Zugriff auf FeedCrawler.db: ", str(e))

    def cleanup(self):
        self._conn.execute("VACUUM")
        return

    def count(self):
        res = self._conn.execute("SELECT Count() FROM %s" % self._table).fetchone()
        return res[0] if res else None

    def retrieve(self, key):
        res = self._conn.execute(
            "SELECT value FROM %s WHERE key='%s'" % (self._table, key)).fetchone()
        return res[0] if res else None

    def retrieve_all(self, key):
        res = self._conn.execute(
            "SELECT distinct value FROM %s WHERE key='%s' ORDER BY value" % (self._table, key))
        items = []
        for r in res:
            items.append(str(r[0]))
        return items

    def retrieve_all_beginning_with(self, key):
        res = self._conn.execute(
            "SELECT distinct key FROM " + self._table + " WHERE key LIKE '" + key + "%'")
        items = []
        for r in res:
            items.append(str(r[0]))
        return items

    def retrieve_all_titles(self):
        res = self._conn.execute(
            "SELECT distinct key, value FROM %s ORDER BY key" % self._table)
        items = []
        for r in res:
            items.append([str(r[0]), str(r[1])])
        return items if items else None

    def retrieve_all_titles_unordered(self):
        res = self._conn.execute(
            "SELECT distinct key, value FROM %s" % self._table)
        items = []
        for r in res:
            items.append([str(r[0]), str(r[1])])
        return items if items else None

    def store(self, key, value):
        self._conn.execute("INSERT INTO '%s' VALUES ('%s', '%s')" %
                           (self._table, key, value))
        self._conn.commit()

    def update_store(self, key, value):
        self._conn.execute("DELETE FROM %s WHERE key='%s'" %
                           (self._table, key))
        self._conn.execute("INSERT INTO '%s' VALUES ('%s', '%s')" %
                           (self._table, key, value))
        self._conn.commit()

    def delete(self, key):
        self._conn.execute("DELETE FROM %s WHERE key='%s'" %
                           (self._table, key))
        self._conn.commit()

    def reset(self):
        self._conn.execute("DROP TABLE IF EXISTS %s" % self._table)
        self._conn.commit()

    def rename_table(self, new_name):
        self._conn.execute("ALTER TABLE '%s' RENAME TO '%s'" %
                           (self._table, new_name))
        self._conn.commit()


class ListDb(object):
    def __init__(self, table):
        self._conn = sqlite3.connect(shared_state.dbfile, check_same_thread=False, timeout=10)
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
        key = feedcrawler.providers.common_functions.keep_alphanumeric_with_special_characters(key)
        self._conn.execute("INSERT INTO '%s' VALUES ('%s')" %
                           (self._table, key))
        self._conn.commit()

    def store_list(self, keys):
        items = []
        if "_Regex" not in self._table:
            for k in keys:
                if k:
                    key = ()
                    k = feedcrawler.providers.common_functions.keep_alphanumeric_with_special_characters(k)
                    key = key + (k,)
                    items.append(key)
        else:
            for k in keys:
                if k:
                    key = ()
                    k = feedcrawler.providers.common_functions.keep_alphanumeric_with_regex_characters(k)
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

    def reset(self):
        self._conn.execute("DROP TABLE IF EXISTS %s" % self._table)
        self._conn.commit()
