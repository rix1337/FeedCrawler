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


def remove_redundant_db_tables(file):
    conn = sqlite3.connect(file)
    cursor = conn.cursor()

    keep_tables = [
        'FeedCrawler',
        'List_ContentAll_Movies',
        'List_ContentAll_Movies_Regex',
        'List_ContentAll_Seasons',
        'List_ContentShows_Seasons_Regex',
        'List_ContentShows_Shows',
        'List_ContentShows_Shows_Regex',
        'List_CustomDD_Feeds',
        'List_CustomDJ_Documentaries',
        'List_CustomDJ_Documentaries_Regex',
        'Ombi',
        'Overseerr',
        'Plex',
        'cdc',
        'crawldog',
        'crawltimes',
        'episode_remover',
        'site_status',
        'flaresolverr',
        'sponsors_helper',
        'secrets',
        'to_decrypt',
        'to_decrypt_disabled'
    ]

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    table_names = [row[0] for row in cursor.fetchall()]

    tables_to_drop = set(table_names) - set(keep_tables)

    for table in tables_to_drop:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
        print(f"Entferne überflüssige Tabelle '{table}' aus der Datenbank.")

    conn.commit()
    cursor.execute("VACUUM")
    conn.close()


class FeedDb(object):
    def __init__(self, table):
        try:
            self._conn = sqlite3.connect(shared_state.values["dbfile"], check_same_thread=False, timeout=5)
            self._table = table
            if not self._conn.execute(
                    f"SELECT sql FROM sqlite_master WHERE type = 'table' AND name = '{self._table}';").fetchall():
                self._conn.execute(f"CREATE TABLE {self._table} (key, value)")
                self._conn.commit()
        except sqlite3.OperationalError as e:
            try:
                shared_state.logger.debug(
                    "Fehler bei Zugriff auf FeedCrawler.db: " + str(e) + " (neuer Versuch in 5 Sekunden).")
                time.sleep(5)
                self._conn = sqlite3.connect(shared_state.values["dbfile"], check_same_thread=False, timeout=10)
                self._table = table
                if not self._conn.execute(
                        f"SELECT sql FROM sqlite_master WHERE type = 'table' AND name = '{self._table}';").fetchall():
                    self._conn.execute(f"CREATE TABLE {self._table} (key, value)")
                    self._conn.commit()
                    shared_state.logger.debug("Zugriff auf FeedCrawler.db nach Wartezeit war erfolgreich.")
            except sqlite3.OperationalError as e:
                print("Fehler bei Zugriff auf FeedCrawler.db: ", str(e))

    def count(self):
        res = self._conn.execute(f"SELECT Count() FROM {self._table}").fetchone()
        return res[0] if res else None

    def retrieve(self, key):
        query = f"SELECT value FROM {self._table} WHERE key=?"
        # using this parameterized query to prevent SQL injection, which requires a tuple as second argument
        res = self._conn.execute(query, (key,)).fetchone()
        return res[0] if res else None

    def retrieve_all(self, key):
        query = f"SELECT distinct value FROM {self._table} WHERE key=? ORDER BY value"
        # using this parameterized query to prevent SQL injection, which requires a tuple as second argument
        res = self._conn.execute(query, (key,))
        items = [str(r[0]) for r in res]
        return items

    def retrieve_all_beginning_with(self, key):
        query = f"SELECT distinct key FROM {self._table} WHERE key LIKE ?"
        # using this parameterized query to prevent SQL injection, which requires a tuple as second argument
        res = self._conn.execute(query, (f"{key}%",))
        items = [str(r[0]) for r in res]
        return items

    def retrieve_all_titles(self):
        query = f"SELECT distinct key, value FROM {self._table} ORDER BY key"
        # using this parameterized query to prevent SQL injection, which requires a tuple as second argument
        res = self._conn.execute(query)
        items = [[str(r[0]), str(r[1])] for r in res]
        return items if items else None

    def retrieve_all_titles_unordered(self):
        query = f"SELECT distinct key, value FROM {self._table}"
        # using this parameterized query to prevent SQL injection, which requires a tuple as second argument
        res = self._conn.execute(query)
        items = [[str(r[0]), str(r[1])] for r in res]
        return items if items else None

    def store(self, key, value):
        query = f"INSERT INTO {self._table} VALUES (?, ?)"
        # using this parameterized query to prevent SQL injection, which requires a tuple as second argument
        self._conn.execute(query, (key, value))
        self._conn.commit()

    def update_store(self, key, value):
        delete_query = f"DELETE FROM {self._table} WHERE key=?"
        # using this parameterized query to prevent SQL injection, which requires a tuple as second argument
        self._conn.execute(delete_query, (key,))
        insert_query = f"INSERT INTO {self._table} VALUES (?, ?)"
        # using this parameterized query to prevent SQL injection, which requires a tuple as second argument
        self._conn.execute(insert_query, (key, value))
        self._conn.commit()

    def delete(self, key):
        query = f"DELETE FROM {self._table} WHERE key=?"
        # using this parameterized query to prevent SQL injection, which requires a tuple as second argument
        self._conn.execute(query, (key,))
        self._conn.commit()

    def reset(self):
        self._conn.execute(f"DROP TABLE IF EXISTS {self._table}")
        self._conn.commit()

    def rename_table(self, new_name):
        self._conn.execute(f"ALTER TABLE '{self._table}' RENAME TO '{new_name}'")
        self._conn.commit()


class ListDb(object):
    def __init__(self, table):
        self._conn = sqlite3.connect(shared_state.values["dbfile"], check_same_thread=False, timeout=10)
        self._table = table
        if not self._conn.execute(
                f"SELECT sql FROM sqlite_master WHERE type = 'table' AND name = '{self._table}';").fetchall():
            self._conn.execute(f"CREATE TABLE {self._table} (key)")
            self._conn.commit()

    def retrieve(self):
        res = self._conn.execute(f"SELECT distinct key FROM {self._table} ORDER BY key")
        items = []
        for r in res:
            items.append(str(r[0]))
        return items if items else None

    def store(self, key):
        key = feedcrawler.providers.common_functions.keep_alphanumeric_with_special_characters(key)
        query = f"INSERT INTO {self._table} VALUES (?)"
        # using this parameterized query to prevent SQL injection, which requires a tuple as second argument
        self._conn.execute(query, (key,))
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
        query = f"DELETE FROM {self._table} WHERE key=?"
        # using this parameterized query to prevent SQL injection, which requires a tuple as second argument
        self._conn.execute(query, (key,))
        self._conn.commit()

    def reset(self):
        self._conn.execute(f"DROP TABLE IF EXISTS {self._table}")
        self._conn.commit()
