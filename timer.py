# -*- coding: utf-8 -*-
# RSScrawler - Version 1.9.2
# Projekt von https://github.com/rix1337
# Enthält Code von:
# https://github.com/dmitryint (im Auftrag von https://github.com/rix1337)

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