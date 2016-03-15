# -*- coding: utf-8 -*-


class RssConfig(object):
    __config__ = []

    def __init__(self, config):
        self.__config__ = config

    def get(self, key):
        return reduce(
            lambda x,y: x,
            [param[3] for param in self.__config__ if param[0] == key]
        )
