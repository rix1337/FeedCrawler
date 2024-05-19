# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul startet den FeedCrawler.

import multiprocessing

from feedcrawler import run

if __name__ == '__main__':
    multiprocessing.freeze_support()
    run.main()
