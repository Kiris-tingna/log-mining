#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/9/14 10:35
 @Author  : Kiristingna
 @File    : tree_parser.py
 @Software: PyCharm
"""
import re
import shlex


class TreeParserNode(object):
    def __init__(self):
        self.children = {}
        self.signature_id = -1
        self.count = 1


class TreeParser(object):
    '''
    树形解析器基类，执行流程大致为读取对应的正则列表（可配），然后替换匹配的串，消除括号或者引号之间的分隔符号然后输出分割的token序列
    '''
    def __init__(self, reg_file):
        '''
        初始化树形解析器
        :param regs: 预过滤正则表达式字符串
        '''
        self.reg_pattern = []
        regs = self._read_config(reg_file)
        for _r in regs:
            self.reg_pattern.append(_r)

        self.root = TreeParserNode()

    def _read_config(self, file):
        """
        读取正则文件
        :param file:
        :return:
        """
        _reg = [('\s+', ' ')]
        with open(file) as f:
            for line in f.readlines():
                rule = re.split(" ", line.strip())
                _reg.append((rule[0], rule[1]))
        return _reg

    def pre_process_single(self, x):
        """
        预处理正则替换过程
        :param x:
        :return:
        """
        for p in self.reg_pattern:
            # 用正则替换已有的str pattern
            x = re.sub(p[0], p[1], x, flags=re.S)

        # 消去括号之间的空格
        x = re.sub('\(.*\)', lambda str: re.sub('\s+|\\n|\.', '-', str.group(0)), x)

        # ---------------- 消去引号之间的分隔符  (aim is to split with rule) -------------------
        # Example1:
        #       During sync_power_state the instance has a pending task (spawning safas)
        #       'During', 'sync_power_state', 'the', 'instance', 'has', 'a', 'pending', 'task', '(spawning-safas)'
        # Example2:
        #       nova.osapi_compute.wsgi.server  192.168.111.8 ""POST /v2.1/servers HTTP/1.1"" status: 202 len: 796
        #       ['nova', 'osapi_compute', 'wsgi', 'server', '<ip>', '"POST /v2.1/servers HTTP/1.1"', 'status:',
        #           '202', 'len:', '796']

        lex_object = shlex.shlex(x)
        lex_object.whitespace = " |\."
        lex_object.whitespace_split = True

        log_sequence_list = list(lex_object)
        # log_len = len(log_sequence_list)

        # if log_len > 100:
        #     log_sequence_list = ['too', 'long']
        # print(log_sequence_list)
        return log_sequence_list

    def dfs_traverse(self, node=None, depth=0):
        '''
        用于打印解析树上的信息
        ====
        tree.dfs_traverse()
        ====
        :param node: 深度优先遍历的起始节点
        :return: None
        '''
        if not node:
            node = self.root

        template_str = ''
        for i in range(depth):
            template_str += '\t'

        if depth == 0:
            template_str += 'Root <> '
        else:
            template_str = template_str[:-1]+"|--"
        if node.children:
            for _word, _child in node.children.items():
                _len_word = len(_word)
                template_str += _word
                print(template_str)
                self.dfs_traverse(_child, depth+1)
                template_str = template_str[:-_len_word]
        else:
            # print(node.signature_id)
            return

    def bfs_traverse(self, node=None):
        '''
        用于打印解析树上的信息
        ====
        tree.bfs_traverse()
        ====
        :param attr:
        :param node: 广度优先遍历的起始节点
        :return: None
        '''
        if not node:
            node = self.root

        _queue = [node]
        next_queue = []
        print_stack = []

        while _queue:
            _node = _queue.pop(0)

            for _word, _child in _node.children.items():
                print_stack.append(_word)
                next_queue.append(_child)

            if not _queue:
                print(print_stack)
                _queue = next_queue
                next_queue = []
                print_stack = []
        return

    def lookup(self, log):
        """
        在已有的集合中查找log group
        """
        raise NotImplementedError

    def insert(self, log):
        """
        认为当前是新事件，则更新已有集合
        """
        raise NotImplementedError
