# -*- coding: utf-8 -*-
# RSScrawler
# Projekt von https://github.com/rix1337

from builtins import object
import logging
import re


class Unbuffered(object):
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def writelines(self, datas):
        self.stream.writelines(datas)
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)


class CutLog(logging.Formatter):
    @staticmethod
    def _filter(s):
        return re.sub(r' - <a href.*<\/a>', '', s).replace('<b>', '').replace('</b>', '')

    def format(self, record):
        original = logging.Formatter.format(self, record)
        return self._filter(original)
