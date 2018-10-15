#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/9/14 10:30
 @Author  : Kiristingna
 @File    : drain.py
 @Software: PyCharm
"""
from logparser.parser.tree_parser import TreeParser, TreeParserNode
from logparser.utils import Timer, visualize_drain_gvfile
import gc


class LogClusterObject:
    cluster_id = 1

    def __init__(self, log_template='', log_ids=[]):
        self.log_template = log_template
        self.cluster_id = LogClusterObject.cluster_id
        LogClusterObject.cluster_id += 1
        self.log_ids = log_ids


class DrainParserNode(TreeParserNode):
    def __init__(self, depth, digit_or_token):
        self.children = {}
        self.depth = depth
        # digit_or_token 对于数字是 '*' 对于token 是 单个word
        self.digit_or_token = digit_or_token


class Drain(TreeParser):
    '''
    @author: Pinjia He
    @paper: Drain: An Online Log Parsing Approach with Fixed Depth Tree

    *********************************************
    Drain 解析算法简述
    1）Preprocess by Domain Knowledge
    2) construct prefix tree and search using the length layer to accelerate match parse
        where log messages with the same log event will probably have the same log message length
    3) Search by Preceding Tokens in prefix tree
    4）to leaf node where store a list of log groups and we search by Token Similarity using threshold to decide which group
        should be most suitable(max similarity) or add to a new group
    5) Update the Parse Tree
    6) At the last output layer we do an overall merge log groups

    '''
    REPL = '*'  # 通配符 wildcards

    def __init__(self, max_depth, reg_file, min_similarity, max_child=10):
        self.max_child = max_child  # maxChild : 孩子节点最大个数
        self.max_depth = max_depth
        self.min_similarity = min_similarity
        # 正则表达式
        super(Drain, self).__init__(reg_file)

        # 修正root的类型
        self.root = DrainParserNode(depth=0, digit_or_token="*")
        # 用于存储所有的log cluster
        self.LogClusterMap = []

    @Timer
    def _online_train(self, log, id):
        return self.online_train(log=log, id=id)

    def online_train(self, log, id):
        '''
        处理某一条日志的插入的逻辑
        :param log:
        :param id:
        :return:
        '''
        filtered_log = self.pre_process_single(log)
        matched_cluster = self.lookup(filtered_log)

        # Match no existing log cluster
        if matched_cluster is None:
            # 插入前缀树 LogClusterObject每new一次 其id自增1
            new_cluster = LogClusterObject(log_template=filtered_log, log_ids=[id])
            self.LogClusterMap.append(new_cluster)
            self.insert(new_cluster)
        # Add the new log message to the existing cluster
        else:
            # 这里的template 就是signature 这一步是combine的过程 由于长度相同不再需要找最长公共子序列了
            new_template = self.marge_template(filtered_log, matched_cluster.log_template)
            matched_cluster.log_ids.append(id)
            if ' '.join(new_template) != ' '.join(matched_cluster.log_template):
                matched_cluster.log_template = new_template

        # @debug on
        # print('---------information---------')
        # for item in self.LogClusterMap:
        #     print(item.log_template, item.log_ids)

    def has_numbers(self, s):
        return any(c.isdigit() for c in s)

    def lookup(self, log_sequence):
        '''
        在前缀树的查找过程
        先利用长度分桶计算
        :param root:
        :param log_sequence:
        :return:
        '''
        is_log_found = None

        n = len(log_sequence)
        # 第一层长度的匹配
        if n not in self.root.children:
            return is_log_found  # 当前长度的日志不存在

        prefix_tree_parent = self.root.children[n]  # 前缀树上的根节点
        current_depth = 1  # 在第二层

        for word in log_sequence:
            # 超长则不再匹配 实际上只匹配日志的前 max_depth 个 token
            if current_depth >= self.max_depth or current_depth > n:
                break

            if word in prefix_tree_parent.children:
                prefix_tree_parent = prefix_tree_parent.children[word]
            elif '*' in prefix_tree_parent.children:
                prefix_tree_parent = prefix_tree_parent.children['*']
            else:
                return is_log_found
            current_depth += 1

        # 得到叶子节点上的cluster children 是一个[]
        log_cluster_group = prefix_tree_parent.children
        # 进行cluster group 的快速匹配
        is_log_found = self.fast_match(log_cluster_group, log_sequence)

        return is_log_found

    def pattern_dist(self, seq_1, seq_2):
        '''
        计算两个序列的相似度 （快速）
        :param seq_1:
        :param seq_2:
        :return:
        '''
        if not len(seq_1) == len(seq_2):
            raise AssertionError("two sequence must have same length")

        similar_tokens = 0  # 相似token的个数
        number_of_parameters = 0  # * 的个数

        for token_1, token_2 in zip(seq_1, seq_2):
            if token_1 == '*':
                number_of_parameters += 1
            elif token_1 == token_2:
                similar_tokens += 1

        similarity = float(similar_tokens) / len(seq_1)

        return similarity, number_of_parameters

    def fast_match(self, log_cluster_group, log_sequence):
        '''
        快速匹配过程（逐个比较）
        :param log_cluster_group: [cluster_1, cluster_2] cluster_i is an object
        cluster:
            :log_template
        :param log_sequence:
        :return:
        '''
        max_similarity = -1
        max_parameter = -1
        max_cluster_group = None  # 最相似的那个group组对象

        for log_cluster in log_cluster_group:
            similarity, n_parameter = self.pattern_dist(log_cluster.log_template, log_sequence)
            # 相同相似度的情况下 取参数个数多的
            if similarity > max_similarity or (similarity == max_similarity and n_parameter > max_parameter):
                max_similarity = similarity
                max_parameter = n_parameter
                max_cluster_group = log_cluster
        if max_similarity >= self.min_similarity:
            return max_cluster_group
        else:
            return None  # 没有最相似的日志组

    def marge_template(self, seq_1, seq_2):
        '''
        合并签名 template = signature
        :param seq_1:
        :param seq_2:
        :return:
        '''
        if not len(seq_1) == len(seq_2):
            raise AssertionError("two sequence must have same length")

        merged_template = []
        n = len(seq_1)

        for i in range(n):
            if seq_1[i] == seq_2[i]:
                merged_template.append(seq_1[i])
            else:
                merged_template.append(self.REPL)
        return merged_template

    def insert(self, log_cluster):
        '''
        在前缀树上插入log
        :param log_cluster:
        :return:
        '''
        n = len(log_cluster.log_template)
        # first_layer_node 比较特殊 是匹配的开始比较点
        if n not in self.root.children:
            first_layer_node = DrainParserNode(depth=1, digit_or_token=n)
            self.root.children[n] = first_layer_node
        else:
            first_layer_node = self.root.children[n]

        # 开始点
        prefix_tree_parent = first_layer_node
        current_depth = 1

        for token in log_cluster.log_template:
            # Add current log cluster to the leaf node
            if current_depth >= self.max_depth or current_depth > n:
                # 叶子节点的children 是一个列表[]
                if len(prefix_tree_parent.children) == 0:
                    prefix_tree_parent.children = [log_cluster]
                else:
                    prefix_tree_parent.children.append(log_cluster)
                # 结束插入
                break

            # If token not matched in this layer of existing tree.
            if token not in prefix_tree_parent.children:
                # token 中不含有数字 ！！！！！！！！！！！！！
                if not self.has_numbers(token):
                    # 当前位置可能是通配符
                    if '*' in prefix_tree_parent.children:
                            # S1: * 节点的同胞还可以插入 没有超过最大分至的限制
                        if len(prefix_tree_parent.children) < self.max_child:
                            new_insert_node = DrainParserNode(depth=current_depth + 1, digit_or_token=token)
                            prefix_tree_parent.children[token] = new_insert_node
                            prefix_tree_parent = new_insert_node
                        else:
                            # S2: * 节点的同胞以用完 只能插入 * 下
                            prefix_tree_parent = prefix_tree_parent.children[self.REPL]
                    # token中含有数字
                    else:
                        # 仍有空位， 将token插入
                        if len(prefix_tree_parent.children) + 1 < self.max_child:
                            new_insert_node = DrainParserNode(depth=current_depth + 1, digit_or_token=token)
                            prefix_tree_parent.children[token] = new_insert_node
                            prefix_tree_parent = new_insert_node
                        # 没有空位，只能插入 * 下
                        elif len(prefix_tree_parent.children) + 1 == self.max_child:
                            new_insert_node = DrainParserNode(depth=current_depth + 1, digit_or_token=self.REPL)
                            prefix_tree_parent.children['*'] = new_insert_node
                            prefix_tree_parent = new_insert_node
                        # 不插入当前节点
                        else:
                            prefix_tree_parent = prefix_tree_parent.children['*']
                # token 含有数字
                else:
                    # 插入到 * 节点下
                    if '*' not in prefix_tree_parent.children:
                        new_insert_node = DrainParserNode(depth=current_depth + 1, digit_or_token=self.REPL)
                        prefix_tree_parent.children['*'] = new_insert_node
                        prefix_tree_parent = new_insert_node
                    else:
                        prefix_tree_parent = prefix_tree_parent.children[self.REPL]

            # If the token is matched
            else:
                prefix_tree_parent = prefix_tree_parent.children[token]

            current_depth += 1

if __name__ == '__main__':
    drain_parser = Drain(max_child=10, max_depth=3, min_similarity=0.5, reg_file='../config/config.reg_exps.txt')

    drain_parser._online_train('blk 124219214 asa Receive from node 4', 1)
    # drain_parser._online_train('blk 124219214 asa Receive from node 4', 2)
    drain_parser._online_train('blk 124219214 ffwqwq 1241241 Done to node 4', 2)
    drain_parser._online_train('blk 124219214 ffwqwq Done to node 4', 3)
    drain_parser._online_train('blk 782174184 Instance raer1421MManf142v Receive from node 356', 4)

    drain_parser._online_train('Tcp net down daafa aswf qe 1241', 5)
    drain_parser._online_train('Tcp net down daafa 12 qe 1241', 6)
    drain_parser._online_train('Tcp qws down daafa 214 qe 1241', 7)
    drain_parser._online_train('Tcp qws down daafa 421 qe 1241', 8)
    drain_parser._online_train('Tcp qws down daafa 14 qe 1241', 9)

    drain_parser._online_train('delete block_1', 10)
    drain_parser._online_train('delete block_3 block_4', 11)
    drain_parser._online_train('delete block_6', 12)

    gc.collect()
    where = visualize_drain_gvfile(drain_parser)
