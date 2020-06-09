# -*- coding: utf-8 -*-


"""
Simple read-only implementation of a classproperty decorator as suggested
on StackOverflow: https://stackoverflow.com/a/13624858
"""


class classproperty(object):

    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)
