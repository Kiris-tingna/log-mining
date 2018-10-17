#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/10/15 15:21
 @Author  : Kiristingna
 @File    : zte_formatter.py
 @Software: PyCharm
"""
import pandas as pd
from os import listdir
from logparser.formalizer.basic_formatter import BasicFormatter
import re


class ZTEFormatter(BasicFormatter):
    '''
    ZTE 输入数据格式化
    注意 必须使用csv 文件
    '''
    def __init__(self, rm ,om):
        '''
        提取日志时间戳
        =================
        Example:
            2018-06-26 01:12:11.190
        '''
        self.time_stamp_1 = re.compile("\d{4} \d{2}:\d{2}:\d{2}.\d{6}")
        self.time_stamp_2 = re.compile("\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}")
        self.time_stamp_3 = re.compile("\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d{3}")
        self.time_stamp_4 = re.compile("\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}")
        self.time_stamp_5 = re.compile("\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}")
        self.time_stamp_6 = re.compile("\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")

        '''
        提取日志级别
        =========
        Example: 
        CRIT DEBUG INFO WARNING TRACE WARN ERROR
        FATAL error warning info
        =========
        '''
        self.log_level = re.compile(
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
        self.pid = re.compile("\d{1,}")
        self.ip = re.compile('\d{1,}\.\d{1,}\.\d{1,}\.\d{1,}')
        self.ms_id = re.compile('[0-9 a-z A-Z]{8}-[0-9 a-z A-Z]{4}-[0-9 a-z A-Z]{4}-[0-9 a-z A-Z]{4}-[0-9 a-z A-Z]{12}')
        self.pod_id = re.compile(
            '[0-9 a-z A-Z]{8}-[0-9 a-z A-Z]{4}-[0-9 a-z A-Z]{4}-[0-9 a-z A-Z]{4}-[0-9 a-z A-Z]{12}-[0-9 a-z A-Z]{1}-[0-9 a-z A-Z]{5}'
        )

        # _LOG_LEVEL_POS = 0
        # _REQID_LEN = 40
        # _INSTACEID_LEN = 32
        # _UUID_LEN = 36
        # _MSID_LEN = 32

        # 文件映射表
        self.rmappings = rm
        self.omappings = om

        # 读取的数据
        self.read_data_frame = None

    def transform(self):
        # 转换所有文件 并合并到一个大文件中
        for k, v in self.rmappings.items():
            self.reader(v)
            if k in self.omappings:
                self.writer(self.omappings[k])
            self.read_data_frame = None

    def filter_origin(self, line, patterns):
        '''
        从原始日志中去除某些字段
        :param line:
        :param patterns:
        :return:
        '''
        for p in patterns:
            line = re.sub(p, '', line)
        return line

    def reader(self, file_address):
        '''
        读取数据 （在mapping中所有的）
        :return:
        '''

        log_dataset = []

        # 装在所有的日志文件到一个数组中
        for file in listdir(file_address):
            abs_path = file_address + '/' + file
            # print(abs_path)

            with open(abs_path, 'r', encoding='utf-8') as f:
                line_dataset = []
                while True:
                    line = f.readline()
                    if line:
                        if line != '\n':
                            line_dataset.append(line.strip('\n'))
                    else:
                        break
                # 合并到同一个文件中
                log_dataset.extend(line_dataset)

        # 数组转dataset
        df = pd.DataFrame(log_dataset, columns=['origin'])
        '(\bCRIT\b)|(\bDEBUG\b)|(\bINFO\b)|(\bWARNING\b)|(\bTRACE\b)|(\bWARN\b)|(\bERROR\b)|'
        r'(\bFATAL\b)|(\berror\b)|(\bwarning\b)|(\binfo\b)'
        RULE_LIST = [
            '\[.*?\]',
            '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d{3} \d+',
            '\sINFO|\sWARNING|\sWARN|\sCRIT|\sDEBUG|\sTRACE|\sFATAL|\sERROR|\serror|\swarning|\sinfo',
            '[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12}',
        ]
        df['time'] = df['origin'].apply(lambda x: self.time_stamp_3.search(x).group(0))
        df['level'] = df['origin'].apply(lambda x: self.log_level.search(x).group(0))
        # 只是3个ms id里的第一个
        df['ms_id'] = df['origin'].apply(lambda x: self.ms_id.search(x).group(0))
        df['message'] = df['origin'].apply(lambda x: self.filter_origin(x, RULE_LIST))

        df.drop(['origin'], axis=1, inplace=True)

        #  返回样例 14095 nova.osapi_compute.wsgi.server  19...
        self.read_data_frame = df

    def writer(self, file_address):
        '''
        输出数据
        :return:
        '''

        self.read_data_frame.to_csv(file_address, header=True, index=True, index_label="log_id")


if __name__ == '__main__':
    read_mapping = {
        # 'VM_SYN_ERROR': '../data/zte_data_2018_10_15/pod11_tongbu_sort'
        # 'VM_DELETE_SAMPLE': '../data/zte_data_2018_10_15/instance_delete0802'
        'VM_FAILED': '../data/zte_data_2018_10_15/pod11_failed'
    }
    output_mapping = {
        # 'VM_SYN_ERROR': '../data/zte_tongbu_filtered.csv'
        # 'VM_DELETE_SAMPLE': '../data/zte_delete_filtered.csv'
        'VM_FAILED': '../data/zte_failed_filtered.csv'
    }

    zte = ZTEFormatter(rm=read_mapping, om=output_mapping)
    zte.transform()
