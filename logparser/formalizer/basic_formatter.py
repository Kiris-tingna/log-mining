#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/10/15 15:21
 @Author  : Kiristingna
 @File    : basic_formatter.py
 @Software: PyCharm
"""
import re


class BasicFormatter(object):
    '''
    提取日志时间戳
        =================
        Example:
            2018-06-26 01:12:11.190
    '''

    time_stamp_1 = re.compile("\d{4} \d{2}:\d{2}:\d{2}.\d{6}")
    time_stamp_2 = re.compile("\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}")
    time_stamp_3 = re.compile("\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d{3}")
    time_stamp_4 = re.compile("\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}")
    time_stamp_5 = re.compile("\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}")
    time_stamp_6 = re.compile("\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")
    time_stamp_7 = re.compile("\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},?")

    time_stamps = [
        time_stamp_1, time_stamp_2,
        time_stamp_3, time_stamp_4,
        time_stamp_5, time_stamp_6,
        time_stamp_7
    ]

    '''
    提取日志级别
        =========
        Example: 
            CRIT DEBUG INFO WARNING TRACE WARN ERROR
            FATAL error warning info
        =========
    '''
    log_level = re.compile(
        r'(\bCRIT\b)|(\bDEBUG\b)|(\bINFO\b)|(\bWARNING\b)|(\bTRACE\b)|(\bWARN\b)|(\bERROR\b)|'
        r'(\bFATAL\b)|(\berror\b)|(\bwarning\b)|(\binfo\b)')

    '''
    正则提取PID 和ID ms_id pod_id？？？（what is pid ms_id?）

    =================================================
    Example:
        ms_id : e6aafc85-ab39-41f4-8c07-77754e34c0e5
        pod_id : c56ee986-5de0-44f1-b6bb-f6617056483f-1-kc5wx
    =================================================
    '''
    pid = re.compile("\d{1,}")
    ip = re.compile('\d{1,}\.\d{1,}\.\d{1,}\.\d{1,}')
    ms_id = re.compile('[0-9 a-z A-Z]{8}-[0-9 a-z A-Z]{4}-[0-9 a-z A-Z]{4}-[0-9 a-z A-Z]{4}-[0-9 a-z A-Z]{12}')
    pod_id = re.compile(
        '[0-9 a-z A-Z]{8}-[0-9 a-z A-Z]{4}-[0-9 a-z A-Z]{4}-[0-9 a-z A-Z]{4}-[0-9 a-z A-Z]{12}-[0-9 a-z A-Z]{1}-[0-9 a-z A-Z]{5}'
    )

    '''
    格式化工具基类
    '''
    def __int__(self):
        pass

    def time_origin(self, line):
        '''
        从日志中得到时间
        :param line:
        :return:
        '''
        for t in self.time_stamps:
            r = t.search(line)
            if r:
                return r.group(0)
        return None

    def level_origin(self, line):
        '''
        提取级别
        :param line:
        :return:
        '''
        r = self.log_level.search(line)
        if r:
            return r.group(0)
        else:
            return None

    def ms_origin(self, line):
        '''
        提取ms 号
        :param line:
        :return:
        '''
        r = self.ms_id.search(line)
        if r:
            return r.group(0)
        else:
            return None

    def filter_origin(self, line):
        '''
        从原始日志中去除某些字段
        :param line:
        :param patterns:
        :return:
        '''
        for p in self.RULE_LIST:
            line = re.sub(p, '', line)

        for p in self.time_stamps:
            line = re.sub(p, '', line)
        return line

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
