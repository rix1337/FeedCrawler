# -*- coding: utf-8 -*-


def get_first(iterable):
    return iterable and list(iterable[:1]).pop() or None
