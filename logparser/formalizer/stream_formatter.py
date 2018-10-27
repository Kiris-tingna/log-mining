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


class STREAMFormatter(BasicFormatter):
    '''
    ZTE 输入数据格式化
    注意 必须使用csv 文件
    '''

    def __init__(self):
        # id 号
        self.current_id_accumulate = 0

        # 过滤的条件
        self.RULE_LIST = [
            '\sINFO|\sWARNING|\sWARN|\sCRIT|\sDEBUG|\sTRACE|\sFATAL|\sERROR|\serror|\swarning|\sinfo',
            '(req-)?[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12}'
        ]

    def filter_origin(self, line):
        '''
        从原始日志中去除某些字段
        :param line:
        :param patterns:
        :return:
        '''

        for p in self.time_stamps:
            line = re.sub(p, '', line)

        for p in self.RULE_LIST:
            line = re.sub(p, '', line)

        return line

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

    def online_parse_one_file(self, file, parser):
        '''
        对一个文件的在线处理
        :param file:
        :param parser:
        :return:
        '''
        i =0
        with open(file, 'r', encoding='utf-8') as f:
            need_to_read = True
            while True:
                if need_to_read:
                    line = f.readline()
                else:
                    line = line_next
                    need_to_read = True

                i +=1
                if i > 100:
                    return

                if not line:
                    break

                log_message = self.filter_origin(line).strip('\n')
                log_id = self.current_id_accumulate

                # 多行日志问题
                if '(' in log_message or '{' in log_message:
                    line_next = f.readline()
                    # need to contact
                    if not self.time_origin(line_next[:26]):
                        while True:
                            log_message += line_next
                            line_next = f.readline()
                            print(log_message)
                            if self.time_origin(line_next[:26]) or not line_next:
                                break

                        need_to_read = False

                    # no need to contact
                    else:
                        need_to_read = False





                print(log_id, log_message)
                self.current_id_accumulate += 1

                 # log_id, log_message


        # 超长截断处理
        #
        # if line != '\n':
        #     log_id, _, _, _ = self.transform(line)
        #
        #     parser.online_train(log_message, log_id)

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
