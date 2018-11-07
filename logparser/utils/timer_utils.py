#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/9/16 23:03
 @Author  : Kiristingna
 @File    : timer_utils.py
 @Software: PyCharm
"""
import time
import sys
import functools


def strict_time():
    if sys.platform == "win32":
        return time.clock()
    else:
        return time.time()


def Timer(func):
    '''
    计时器 用于分析算法运行时间
    :param func:
    :return:
    '''
    @functools.wraps(func)
    def fn(*args, **kwargs):
        _start_time = strict_time()
        _func_result = func(*args, **kwargs)
        _end_time = strict_time()
        print('{} cost：{}s seconds'.format(func.__name__, _end_time - _start_time))
        return _func_result
    return fn


def datetime_to_timestamp(dt):
    """
    用于将时间戳转换为unix时间值
    :param dt: string
    :return: Unix time stamp
    """
    if ',' in dt:
        [t1, t2] = dt.split(',')
    elif '.' in dt:
        [t1, t2] = dt.split('.')
    else:
        unix_seconds = int(time.mktime(time.strptime(dt, '%Y-%m-%d %H:%M:%S')))
        return unix_seconds

    micro_seconds = round(float('0.' + t2), 3)
    unix_seconds = int(time.mktime(time.strptime(t1, '%Y-%m-%d %H:%M:%S')))
    return unix_seconds + micro_seconds
