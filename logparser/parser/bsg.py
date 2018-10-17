#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/10/15 10:23
 @Author  : Tinkle
 @File    : bsg.py
 @Software: PyCharm
"""
from logparser.parser.tree_parser import TreeParser, TreeParserNode
from logparser.utils import LCSUtil, Timer #, visualize_bsg_gvfile
import gc
import re
import math
import collections

# 将字符串转换成TokenPairs
# Example:
# Template: [PATTERN_DATETIME, a, b, *, d]
# TokenPairs: [('a', 'b'), ('a', 'd'), ('b', 'd')]
def Template2TokenPairs(logTemplate):
  clearTemplate = []
  tokenDict = dict()
  for token in logTemplate:
    if token != '*' and 'PATTERN_' not in token:
      if token not in tokenDict:
        clearTemplate.append(token)
        tokenDict[token] = 1
      else:
        clearTemplate.append(token+'_'+str(tokenDict[token]))
        tokenDict[token] += 1
  tokenPair = []
  for i in range(len(clearTemplate)):
    for j in range(i + 1, len(clearTemplate)):
      tokenPair.append((clearTemplate[i],clearTemplate[j]))
  return tokenPair

class LogCluster(object):
    def __init__(self, logTemplate, idx, st = 0.5):
        self.logTemplate = logTemplate
        self.st = st
        self.nc = len(logTemplate)
        self.log_ids = [idx]
        self.token_dict = [collections.defaultdict(int) for i in range(self.nc)]
        for i, token in enumerate(logTemplate):
            self.token_dict[i][token] = 1

    def update(self, nc, logTemplate, seq, idx):
        self.nc = nc
        self.logTemplate = logTemplate
        for i, token in enumerate(seq):
            self.token_dict[i][token] += 1
        self.log_ids.append(idx)

class BSG(TreeParser):
    """
    @Author: Tinkle Guo

    ********************************************
    BSG 解析器过程简述
    基于原始论文BSG 和 DRAGA算法框架 改进

    1) 日志预处理
    2）Length Layer: 每条日志根据长度将日志划分到相应子树上
    3) keyValue Layer: 以日志的第一个词、最后一个词 和 *通配符 作为keyValue
    4) Token Layer: 在同个Keyword Layer下的所有cluster中查找满足大于阈值且熵变最小的cluster结构体， 如果没有找到就新建一个输出曾
    5）get_final_template 来呈现
    """
    REPL = '*' # 通配符

    # 特殊字符
    SPECIAL_CHARS = set(
        "#$&'*+,/<=>@^_`|~)"
    )
    SPECIAL_CHARS_IN_WORD = '^[\w]+[#$&\'*+,\/<=>@^_`|~.]+$'

    def __init__(self, reg_file, global_st = 1.0):
        self.maxlength = 300
        self.global_st = global_st
        self.bucket = [collections.defaultdict(list) for i in range(self.maxlength * 3)]
        super(BSG, self).__init__(reg_file)  # 装载正则表达式

    @Timer
    def _online_train(self, log, id):
        return self.online_train(log=log, id=id)

    def online_train(self, log, id):
        """
        处理某一条日志的插入的逻辑
        :param log:
        :return:
        """
        # 1.首先预处理某一条日志 并且拆分成数组
        log_filter = self.pre_process_single(log)
        log_length = len(log_filter)

        # 2.查找KeyValue
        keyValue = ''
        if (not self.has_numbers(log_filter[0]) and not self.has_special(log_filter[0])):
            pos = log_length * 3
            keyValue = log_filter[0]
        elif (not self.has_numbers(log_filter[-1]) and not self.has_special(log_filter[-1])):
            pos = log_length * 3 + 1
            keyValue = log_filter[-1]
        else:
            pos = log_length * 3 + 2

        # 3.Token Layer匹配
        if keyValue not in self.bucket[pos]:
            # new cluster
            new_cluster = self.newCluster(log_filter, log_length, id)
            self.bucket[pos][keyValue].append(new_cluster)
        else:
            TokenLayer = self.bucket[pos][keyValue]
            sim, new_nc, new_template, idx, entropy = -1, -1, -1, -1, 100000

            for i, cluster in enumerate(TokenLayer):
                sim_, new_nc_, new_template_, entropy_ = self.calDistance(log_filter, cluster)
                if sim_ > -1 and entropy_ < entropy:
                    sim, new_nc, new_template, entropy = sim_, new_nc_, new_template_, entropy_
                    idx = i
            if sim > -1:
                # Update
                TokenLayer[idx].update(new_nc, new_template, log_filter, id)
            else:
                # new cluster
                new_cluster = self.newCluster(log_filter, log_length, id)
                self.bucket[pos][keyValue].append(new_cluster)

    def newCluster(self, log_filter, log_length, idx):
        digit_len = 0
        for token in log_filter:
            if self.has_numbers(token):
                digit_len += 1
        st_init = self.global_st  - self.global_st * (digit_len / log_length)
        new_cluster = LogCluster(log_filter, idx, st_init)
        return new_cluster

    def calDistance(self, seq, cluster):
        logTemplate = cluster.logTemplate
        token_dict = cluster.token_dict
        newTemplate = []
        st = cluster.st
        nc = cluster.nc
        threshold = math.ceil((1 - st) * nc)
        diff = 0
        entropy = 0
        for i in range(len(seq)):
            s1 = seq[i]
            s2 = logTemplate[i]
            if s1 != s2:
                diff += 1
                old_cnt, old_entropy, new_entropy = 0, 0, 0
                for token in token_dict[i]:
                    old_cnt += token_dict[i][token]
                    old_entropy += token_dict[i][token] * math.log(token_dict[i][token])
                    if s1 == token:
                        new_entropy += (token_dict[i][token] + 1) * math.log((token_dict[i][token] + 1))
                    else:
                        new_entropy += token_dict[i][token] * math.log(token_dict[i][token])
                old_entropy = - (1.0 / old_cnt * old_entropy - math.log(old_cnt))
                new_entropy = - (1.0 / (old_cnt + 1) * new_entropy - math.log(old_cnt + 1))
                entropy += abs(old_entropy - new_entropy)
                if diff > threshold:
                    return -1, -1, [], -1
                newTemplate.append('*')
            else:
                newTemplate.append(s1)
        return 1 - float(diff) / nc, len(seq) - diff, newTemplate, entropy

    # Check if there is number
    def has_numbers(self, s):
        return any(c.isdigit() for c in s)

    # Check if there is special character
    def has_special(self, s):
        return any(c in self.SPECIAL_CHARS for c in s)

    def has_special_tail(self, s):
        '''
        检查单词或者sequence中是否存在特殊字符
        :param s:
        :return:
        '''
        # CASE1 : ....word1 special_char word2 ....
        if not self.has_special(s):
            return False
        # CASE2 : word1(char123+special_char) ...
        if re.match(self.SPECIAL_CHARS_IN_WORD, s):
            return False
        return True

    def get_final_template(self):
        ans = collections.defaultdict(list)
        for pos in self.bucket:
            for key in pos:
                for cluster in pos[key]:
                    ans[' '.join(cluster.logTemplate)] += cluster.log_ids
        for signature in ans:
            print(signature, ans[signature])

    def quality(self):
        ans = []
        Compactness = []
        for pos in self.bucket:
            for key in pos:
                for cluster in pos[key]:
                    logTemplate = cluster.logTemplate
                    Compactness += [cluster.nc / len(cluster.logTemplate)]
                    tp = tuple(Template2TokenPairs(logTemplate))
                    ans.append(tp)
        sum_ = 0
        for i in range(len(ans)):
            tmp = 1
            for j in range(len(ans)):
                if i != j:
                    ix = ans[i]
                    iy = ans[j]
                    tmp = min(tmp, 1 - len(set(ix) & set(iy)) * 1.0 / len(set(ix) | set(iy)))
            sum_ += tmp
        return (sum(Compactness)/len(Compactness) * (sum_ / len(ans)))

if __name__ == '__main__':
    # where = visualize_spell_gvfile(spell_parser)
    # spell_parser.dfs_traverse()
    # FP_tree
    for i in range(10,11):
        st = i * 0.1

        bsg_parser = BSG(reg_file='../config/config.reg_exps.txt', global_st=st)
        bsg_parser._online_train('blk 124219214 asa Receive from node 4', 1)
        bsg_parser._online_train('blk 124219214 ffwqwq 1241241 Done to node 4', 2)
        bsg_parser._online_train('blk 124219214 ffwqwq Done to node 4', 3)
        bsg_parser._online_train('blk 782174184 Instance raer1421MManf142v Receive from node 356', 4)

        bsg_parser._online_train('Tcp net down daafa aswf qe 1241', 5)
        bsg_parser._online_train('Tcp net down daafa 12 qe 1241', 6)
        bsg_parser._online_train('Tcp qws down daafa 214 qe 1241', 7)
        bsg_parser._online_train('Tcp qws down daafa 421 qe 1241', 8)
        bsg_parser._online_train('Tcp qws down daafa 14 qe 1241', 9)

        bsg_parser._online_train('delete block_1', 10)
        bsg_parser._online_train('delete block_3 block_4', 11)
        bsg_parser._online_train('delete block_6', 12)
        bsg_parser.get_final_template()
        print(bsg_parser.quality())
    # where = visualize_bsg_gvfile(bsg_parser)

    gc.collect()


