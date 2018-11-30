#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/11/15 15:03
 @Author  : Kiristingna
 @File    : prediction_tree.py
 @Software: PyCharm
"""

class PredictionTree():
    item = None
    parent = None
    children = None

    def __init__(self, item_value=None):
        self.item = item_value
        self.children = []
        self.parent = None

    def add_child(self, child):
        new_child = PredictionTree(child)
        new_child.parent = self
        self.children.append(new_child)

    def get_child(self, target):
        for chld in self.children:
            if chld.item == target:
                return chld
        return None

    def get_children(self):
        return self.children

    def has_child(self, target):
        found = self.get_child(target)
        if found is not None:
            return True
        else:
            return False

    def remove_child(self, child):
        for chld in self.children:
            if chld.item == child:
                self.children.remove(chld)
