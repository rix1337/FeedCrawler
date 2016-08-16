# -*- coding: utf-8 -*-
# RSScrawler - Version 1.6.7
# Projekt von https://github.com/rix1337
# Enthaltener Code
# https://github.com/dmitryint (im Auftrag von https://github.com/rix1337)
# https://github.com/zapp-brannigan/own-pyload-plugins/blob/master/hooks/MovieblogFeed.py
# https://github.com/Gutz-Pilz/pyLoad-stuff/blob/master/SJ.py
# https://github.com/bharnett/Infringer/blob/master/LinkRetrieve.py
# Beschreibung:
# RSScrawler durchsucht MB/SJ nach in .txt Listen hinterlegten Titeln und reicht diese im .crawljob Format an JDownloader weiter.

from threading import Timer
import time


class RepeatableTimer(object):
    def __init__(self, interval, function, args=(), kwargs={}):
        self._interval = interval
        self._function = function
        self._args = args
        self._kwargs = kwargs
        self._START_TIME = None
        self._TIMER_STARTED = False

    def start(self):
        if not self._TIMER_STARTED:
            self._timer = Timer(self._interval, self._function, args=self._args, kwargs=self._kwargs)
            self._timer.start()
            self._START_TIME = time.time()
            self._TIMER_STARTED = True

    def cancel(self):
        if self._TIMER_STARTED:
            self._timer.cancel()
            self._TIMER_STARTED = False

    def running(self):
        return self._TIMER_STARTED

    def elapsed(self):
        return time.time() - self._START_TIME if self._TIMER_STARTED else None

    def remain(self):
        return self._interval - (time.time() - self._START_TIME) if self._TIMER_STARTED else None