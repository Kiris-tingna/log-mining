#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/10/15 15:21
 @Author  : Kiristingna
 @File    : basic_formatter.py
 @Software: PyCharm
"""


class BasicFormatter(object):
    '''
    格式化工具基类
    '''
    def __int__(self):
        pass

    def reader(self, file):
        '''
        读取数据
        :return:
        '''
        raise NotImplementedError

    def writer(self, file):
        '''
        输出数据
        :return:
        '''
        raise NotImplementedError
