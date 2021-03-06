#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/10/15 15:21
 @Author  : Kiristingna
 @File    : zte_formatter.py
 @Software: PyCharm
"""
import pandas as pd
import os
from logparser.formalizer.basic_formatter import BasicFormatter
import re
import gzip

class ZTEFormatter(BasicFormatter):
    '''
    ZTE 输入数据格式化
    注意 必须使用csv 文件
    '''
    def __init__(self, rm, om):
        # 文件映射表
        self.rmappings = rm
        self.omappings = om

        # 读取的数据
        self.read_data_frame = None
        self.files = []

        self.RULE_LIST = [
            '\[.*?\]',
            '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d{3} \d+',
            '\sINFO|\sWARNING|\sWARN|\sCRIT|\sDEBUG|\sTRACE|\sFATAL|\sERROR|\serror|\swarning|\sinfo',
            '(req-)?[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12}',
        ]

    def list_all_file(self, path):
        '''
        得到所有的文件路径
        :param path:
        :return:
        '''
        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            if os.path.isdir(file_path):
                self.list_all_file(file_path)
            else:
                self.files.append(file_path)
        return

    def transform(self):
        # 转换所有文件 并合并到一个大文件中
        for k, v in self.rmappings.items():
            self.reader(v)
            if k in self.omappings:
                self.writer(self.omappings[k])
            self.read_data_frame = None

    def reader(self, file_address):
        '''
        读取数据 （在mapping中所有的）
        :return:
        '''

        log_dataset = []

        # 装在所有的日志文件到一个数组中
        self.list_all_file(file_address)

        for file in self.files:
            abs_path = file
            if '.DS_Store' in abs_path:
                continue
            # print(abs_path)
            if 'gz' not in abs_path:
                with open(abs_path, 'r', encoding='utf-8') as f:
                    line_dataset = []
                    while True:
                        line = f.readline()
                        if line:
                            if line[0] == '2':
                                line_dataset.append(line.strip('\n'))
                            else:
                                line_dataset[-1] += ' ' + line.strip('\n')
                        else:
                            break
                    # 合并到同一个文件中
                    log_dataset.extend(line_dataset)
            else:
                with gzip.open(abs_path, 'rt', encoding='utf-8') as f:
                    line_dataset = []
                    while True:
                        line = f.readline()
                        if line:
                            if line != '\n':
                                if line[0] == '2':
                                    line_dataset.append(line.strip('\n'))
                                else:
                                    line_dataset[-1]+=' '+ line.strip('\n')
                        else:
                            break
                    # 合并到同一个文件中
                    log_dataset.extend(line_dataset)

        # 数组转dataset
        df = pd.DataFrame(log_dataset, columns=['origin'])

        df['time'] = df['origin'].apply(lambda x: self.time_origin(x))
        df['level'] = df['origin'].apply(lambda x: self.level_origin(x))
        # 只是3个ms id里的第一个

        df['ms_id'] = df['origin'].apply(lambda x: self.ms_origin(x))
        df['message'] = df['origin'].apply(lambda x: self.filter_origin(x))

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
        # 'VM_FAILED': '../data/slot1',
        'IAAS': '../data/zte_iaas'
    }
    output_mapping = {
        # 'VM_SYN_ERROR': '../data/zte_tongbu_filtered.csv'
        # 'VM_DELETE_SAMPLE': '../data/zte_delete_filtered.csv'
        # 'VM_FAILED': '../data/zte_failed_filtered.csv',
        'IAAS': '../data/iaas_filtered.csv'
    }

    zte = ZTEFormatter(rm=read_mapping, om=output_mapping)
    zte.transform()
