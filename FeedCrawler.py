# -*- coding: utf-8 -*-
# FeedCrawler
# Projekt von https://github.com/rix1337

import multiprocessing

from feedcrawler import crawler

if __name__ == '__main__':
    multiprocessing.freeze_support()
    crawler.main()
