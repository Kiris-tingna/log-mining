#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/9/14 10:35
 @Author  : Kiristingna
 @File    : tree_parser.py
 @Software: PyCharm
"""
import re


class TreeParserNode(object):
    def __init__(self):
        self.children = {}
        self.signature_id = -1
        self.count = 1


class TreeParser(object):
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
        log_sequence_list = re.split(" |\.", x)
        log_len = len(log_sequence_list)
        # 删除空格与多余的*
        i = 1
        while i < log_len:
            if not log_sequence_list[i].strip():
                log_sequence_list.pop(i)
                log_len -= 1
            else:
                i += 1
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
