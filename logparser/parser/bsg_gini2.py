#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/11/06 14:41
 @Author  : Tinkle
 @File    : bsg_gini.py
 @Software: PyCharm
"""
import collections, itertools
from logparser.parser.tree_parser import TreeParser
from logparser.utils import Timer, visualize_bsg_gvfile
import math
import gc


class LogCluster(object):
    def __init__(self, log_template, idx, similarity_threshold=0.5):
        '''
        日志模板结构体
        :param log_template:
        :param idx:  日志id 集合
        :param similarity_threshold: 相似度初始阈值
        '''
        self.log_template = log_template
        self.st = similarity_threshold
        self.nc = len(log_template)
        self.log_ids = [idx]
        self.cnt = 1
        self.token_square_sum = [0 for _ in range(self.nc)]
        # token_dict=[
        #     模板上词的相应位置: {替换的参数列表}
        # ]
        self.token_dict = [collections.defaultdict(list) for _ in range(self.nc)]
        # 统计参数情况
        for i, token in enumerate(log_template):
            self.token_dict[i][token].append(idx)

    def update(self, nc, new_log_template, new_log_seq, idx):
        '''
        Example：
            new_log_template: [a, b, * , d]
            new_log_seq: [a, b, f , d]

            token_dict: [
                ...
                3: { c: 1, f: 0 }  -> 3:  { c: 1, f: 1 }
            ]
        :param nc:
        :param new_log_template:
        :param log_seq:
        :param idx:
        :return:
        '''
        # 当前常量字符的长度
        self.nc = nc
        self.log_template = new_log_template
        self.cnt += 1
        # log_seq 为新的日志序列
        for i, token in enumerate(new_log_seq):
            self.token_dict[i][token].append(idx)
        #  当前日志组日志id的增加
        self.log_ids.append(idx)


class BasicSignatureGrenGini(TreeParser):
    """
    @author: Shuting Guo
    @paper: Event Extraction from Streaming System Logs

    ********************************************
    BSG-gini 解析器过程简述
    基于原始论文BSG 和 DRAGA算法框架 改进

    1) 日志预处理
    2）Length Layer: 每条日志根据长度将日志划分到相应子树上
    3) keyValue Layer: 以日志的第一个词、最后一个词 和 中间字符 作为keyValue (取模方式计算三种索引情况)
    4) Token Layer: 在同个Keyword Layer下的所有cluster中查找满足大于阈值且Gini值最小的cluster结构体， 如果没有找到就新建一个输出层
    5）输出层使用函数 get_final_template 来呈现

    =================================================
    todo 2018 10 30:
    add gini explanation
    keyword split procession
    cache mechanism
    """
    REPL = '*'  # 通配符

    # 特殊字符
    SPECIAL_CHARS = set(
        "#$&'*+,/<=>@^_`|~)"
    )
    SPECIAL_CHARS_IN_WORD = '^[\w]+[#$&\'*+,\/<=>@^_`|~.]+$'

    def __init__(self, reg_file, global_st=1.0, max_length=300):
        self.max_length = max_length  # 日志最大长度阈值
        self.global_st = global_st
        # bucket 的形式:
        # bucket = [   ...
        #       该长度日志 起始字符位置可以用作分桶情况: { 首token: [对应的模板] ....}
        #       该长度日志 终止字符位置可以用作分桶情况: { 尾token: [对应的模板] ....}
        #       该长度日志 中间字符位置可以用作分桶情况: { 中间token: [对应的模板] ....}
        # ]
        self.bucket = dict()
        super(BasicSignatureGrenGini, self).__init__(reg_file)  # 装载正则表达式

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
        # 首字符有效的情况 放在0位置
        if not self.has_numbers(log_filter[0]) and not self.has_special(log_filter[0]):
            pos = log_length * 3
            keyValue = log_filter[0]
        # 尾字符有效的情况 放在1位置
        elif not self.has_numbers(log_filter[-1]) and not self.has_special(log_filter[-1]):
            pos = log_length * 3 + 1
            keyValue = log_filter[-1]
        # 中间字符 放在2位置 key 为空
        else:
            pos = log_length * 3 + 2

        # 3.Token Layer匹配
        if pos not in self.bucket:
            self.bucket[pos] = collections.defaultdict(list)

        if keyValue not in self.bucket[pos]:
            # 在bucket中尚未存在当前的模板则新建一个新的模板 并放在相应位置的字典中
            new_cluster = self.create_cluster(log_filter, log_length, id)
            self.bucket[pos][keyValue].append(new_cluster)
        else:
            # 存在就从template列表中找出最合适（熵变最小的情况）的插入
            token_layer = self.bucket[pos][keyValue]
            sim, new_nc, new_template, idx = -1, -1, -1, -1

            for i, cluster in enumerate(token_layer):
                # sim: 相似度 new_nc: 常量字符的长度 entropy: 熵
                sim_, new_nc_, new_template_ = self.edit_distance(log_filter, cluster)
                if sim_ > sim:
                    sim, new_nc, new_template = sim_, new_nc_, new_template_
                    idx = i
            if sim > -1:
                # token layer 更新
                token_layer[idx].update(new_nc, new_template, log_filter, id)
            else:
                # new cluster 的创建
                new_cluster = self.create_cluster(log_filter, log_length, id)
                self.bucket[pos][keyValue].append(new_cluster)

    # Check if there is number
    def has_numbers(self, s):
        return any(c.isdigit() for c in s)

    # Check if there is special character
    def has_special(self, s):
        return any(c in self.SPECIAL_CHARS for c in s)

    def create_cluster(self, log_filter, log_length, idx):
        '''
        创建一个新的日志组
        :param log_filter:
        :param log_length:
        :param idx:
        :return:
        '''
        digit_len = 0
        for token in log_filter:
            if self.has_numbers(token):
                digit_len += 1
        # 计算初始的相似度下界
        st_init = self.global_st - self.global_st * (digit_len / log_length)
        new_cluster = LogCluster(log_filter, idx, st_init)
        return new_cluster

    def edit_distance(self, seq, cluster):
        '''
        计算seq 和 template 的编辑距离
        :param seq:
        :param cluster:
        :return:
        '''
        log_template = cluster.log_template

        new_template = []
        st = cluster.st
        nc = cluster.nc
        threshold = math.ceil((1 - st) * nc)

        # 与模板不同的个数
        diff = 0
        for i in range(len(seq)):
            s1 = seq[i]
            s2 = log_template[i]
            if s1 != s2:
                diff += 1
                if diff > threshold:
                    return -1, -1, []
                new_template.append('*')
            else:
                new_template.append(s1)

        return 1 - float(diff) / nc, len(seq) - diff, new_template

    def template_to_token_pairs(self, log_template):
        """
        将字符串转换成TokenPairs
            Example:
               模板token 集合为: [PATTERN_DATETIME, a, b, *, d]
               对应的Token Pairs: [('a', 'b'), ('a', 'd'), ('b', 'd')]
        :param log_template:
        :return:
        """
        token_set = [token for token in log_template if token != '*' and 'PATTERN_' not in token]

        token_pair = itertools.combinations(token_set, 2)
        return set(token_pair)

    def quality(self):
        '''
        评价生成的 模板的质量
        使用聚类的内聚程度 类间的距离
        :return:
        '''
        term_pairs = []
        # 类内紧密程度： sum (常量 / 长度)
        compactness = []
        for pos in self.bucket:
            for key in self.bucket[pos]:
                for cluster in self.bucket[pos][key]:
                    log_template = cluster.log_template
                    compactness += [cluster.nc / len(cluster.log_template)]
                    terms = (self.template_to_token_pairs(log_template))
                    term_pairs.append(terms)
        n = len(term_pairs)
        total_similarity = 0
        for i in range(n):
            similarity = 1
            for j in range(n):
                if i != j:
                    ix = term_pairs[i]
                    iy = term_pairs[j]
                    similarity = min(similarity, 1 - len(ix & iy) * 1.0 / len (ix | iy))
            total_similarity += similarity
        #  平均类内紧密程度 * 平均类见距离
        average_compactness = sum(compactness) / len(compactness)
        average_similarity = total_similarity / n
        # Todo: x ????
        return average_compactness * average_similarity

    def cluster_refinement(self, cluster):
        '''
        将keyword 从* 中提取出来
        :param cluster:
        :return:
        '''
        cnt = cluster.cnt
        log_template = cluster.log_template
        split_pos, split_gini = -1, 1

        for c_pos, token in enumerate(log_template):
            if token == '*':
                square_sum = 0
                for word in cluster.token_dict[c_pos]:
                    num = len(cluster.token_dict[c_pos][word])
                    square_sum += float(num) ** 2
                gini = 1 - square_sum / (cnt ** 2)
                if gini <= 0.5 and gini < split_gini:
                    split_pos, split_gini = c_pos, split_gini
        return split_pos

    def get_final_template(self):
        '''
        输出所有模板
        :return:
        '''
        ret = []
        ans = collections.defaultdict(list)
        for pos in self.bucket:
            for key in self.bucket[pos]:
                for cluster in self.bucket[pos][key]:
                    c_pos = self.cluster_refinement(cluster)
                    if c_pos != -1:
                        for word in cluster.token_dict[c_pos]:
                            cluster.log_template[c_pos] = word
                            ans[' '.join(cluster.log_template)] += cluster.token_dict[c_pos][word]
                        cluster.log_template[c_pos] = '*'
                    else:
                        ans[' '.join(cluster.log_template)] += cluster.log_ids

        for sid, signature in enumerate(ans):
            print('template {} has {} logs: {}'.format(sid, len(ans[signature]), signature))
            ret.append((signature, ans[signature]))
        return ret


if __name__ == '__main__':
    # 0.7 是最好的阈值
    for i in range(7, 8):
        st = i * 0.1

        bsg_parser = BasicSignatureGrenGini(reg_file='../config/config.reg_exps.txt', global_st=st)
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
