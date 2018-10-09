#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/9/15 16:23
 @Author  : Kiristingna
 @File    : lcs_utils.py
 @Software: PyCharm
"""


class LCSUtil(object):
    # 静态变量段
    LEFT = 1
    UP = 2
    EQUAL = 3

    def __init__(self, a, b, repl):
        self.a = a
        self.b = b
        self.repl = repl
        self.result = []
        self.len_a = len(a)
        self.len_b = len(b)
        self.c = None
        self.path = None
        self.result = []
        self.lcs()

    def lcs(self):
        self.c = [[0] * (self.len_b + 1) for _ in range(self.len_a + 1)]
        self.path = [[0] * (self.len_b + 1) for _ in range(self.len_a + 1)]
        for i in range(self.len_a):
            for j in range(self.len_b):
                if self.a[i] == self.b[j]:
                    self.c[i + 1][j + 1] = self.c[i][j] + 1
                    self.path[i + 1][j + 1] = LCSUtil.EQUAL
                elif self.c[i + 1][j] > self.c[i][j + 1]:
                    self.c[i + 1][j + 1] = self.c[i + 1][j]
                    self.path[i + 1][j + 1] = LCSUtil.LEFT
                else:
                    self.c[i + 1][j + 1] = self.c[i][j + 1]
                    self.path[i + 1][j + 1] = LCSUtil.UP

    def backtrack(self, i=-1, j=-1):
        if i == -1 and j == -1:
            i = self.len_a
            j = self.len_b
        if i == 0 or j == 0:
            return
        if self.path[i][j] == LCSUtil.EQUAL:
            self.backtrack(i - 1, j - 1)
            self.result.append(self.a[i - 1])

        elif self.path[i][j] == LCSUtil.LEFT:
            self.backtrack(i, j - 1)

        elif self.path[i][j] == LCSUtil.UP:
            self.backtrack(i - 1, j)

            if self.result and self.result[-1] != self.repl:
                self.result.append(self.repl)


