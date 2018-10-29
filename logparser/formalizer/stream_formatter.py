#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/10/15 15:21
 @Author  : Kiristingna
 @File    : stream_formatter.py
 @Software: PyCharm
"""
import os
from logparser.formalizer.basic_formatter import BasicFormatter
import re
import datetime


class STREAMFormatter(BasicFormatter):
    '''
    ZTE 输入数据格式化
    注意 必须使用csv 文件
    '''

    def __init__(self):
        # id 号
        self.current_id_accumulate = 0
        self.this_year = str(datetime.datetime.now().year)
        # 过滤的条件
        self.RULE_LIST = [
            '\[.*?\]',
            '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d{3} \d+',
            '\sINFO|\sWARNING|\sWARN|\sCRIT|\sDEBUG|\sTRACE|\sFATAL|\sERROR|\serror|\swarning|\sinfo',
            '(req-)?[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12}'
        ]

    def online_parse_one_file(self, file, parser):
        '''
        对一个文件的在线处理
        :param file:
        :param parser:
        :return:
        '''
        with open(file, 'r', encoding='utf-8') as f:
            prev_line = f.readline()
            next_line = f.readline()
            while True:
                if not next_line:
                    break
                # 判断改行是否有效
                elif 0 < len(next_line) < 20:
                    prev_line += next_line
                    next_line = f.readline()
                else:
                    # 行起始特征不满足
                    if next_line[:4] != self.this_year:
                        prev_line += next_line
                        next_line = f.readline()
                    # 行起始特征满足
                    elif next_line[:4] == self.this_year:
                        # 超长截断处理
                        if len(prev_line) > 1000:
                            prev_line = prev_line[:1000]

                        parse_line = re.sub(r'\n', '', prev_line)
                        log_message = self.filter_origin(parse_line)
                        log_id = self.current_id_accumulate

                        # core: 处理一行日志
                        parser.online_train(log_message, log_id)

                        # 为新行做准备
                        prev_line = next_line
                        next_line = f.readline()
                        self.current_id_accumulate += 1

    def list_all_file(self, path, file_list):
        '''
        得到所有的文件路径
        :param path:
        :return:
        '''
        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            if os.path.isdir(file_path):
                self.list_all_file(file_path, file_list)
            else:
                file_list.append(file_path)
        return

    def online_parse_one_dir(self, dir, parser):
        '''
        对一个目录的处理
        :param file:
        :param parser:
        :return:
        '''
        file_list = []
        self.list_all_file(dir, file_list)

        for f in file_list:
            self.online_parse_one_file(f, parser)


if __name__ == '__main__':
    line = ['fasfas asfasfs'] * 100
    stream = STREAMFormatter()
