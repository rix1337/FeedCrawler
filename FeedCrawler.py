# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337
# Dieses Modul startet den FeedCrawler.

import multiprocessing

from feedcrawler import main

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main.main()
