#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/9/16 18:47
 @Author  : Kiristingna
 @File    : spell.py
 @Software: PyCharm
"""
from logparser.parser.tree_parser import TreeParser, TreeParserNode
from logparser.utils import LCSUtil, Timer, visualize_spell_gvfile
import gc

class SignatureObject(object):
    '''
    Spell 使用的签名对象结构
    '''
    signature_id = 1  # 全局计数器

    def __init__(self, signature, idx):
        self.signature = signature
        self.sig_id = SignatureObject.signature_id  # 自增字段
        SignatureObject.signature_id += 1
        self.log_ids = [idx]
        self.length = len(signature)


class Spell(TreeParser):
    """
    @author: Min Du, Feifei Li
    @paper: Spell: Streaming Parsing of System Event Logs

    *********************************************
    Spell 解析器过程简述
    # 1) find message type by prefix tree (* will matched every word)
    # 2) if not found apply simple loop lookup in SignatureMap, match subsequence in SignatureMap one by one
    (skip those signature whose length  < 0.5 | log sequence length | )
    # 3) if cant find, find most similar log group and combine them using LCS > 0.5 | signature length |
    (skip those |signature ^ log |/|signature V log | < 0.5)
    # 4) update SignatureMap and delete origin prefix tree(node count > 1 will not be removed only remove those count= 1)
     a nd add new
    # 5) if cant find in above steps this log will be viewed as new log group, just add into SignatureMap and prefix tree
    """
    REPL = '*'  # 通配符

    def __init__(self, reg_file, threshold):
        """
        初始化Spell需要的数据结构 主要包括预处理正则
        :param reg_file: 正则文件
        """
        self.signature_map = {}
        self.current_signature_ids = 0 # 当前已有的signature的个数
        self.threshold = threshold
        super(Spell, self).__init__(reg_file)  # 装在正则表达式

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
        filtered_log = self.pre_process_single(log)

        # 2.查找是否在树上有匹配的模式
        sig_id = self.lookup(filtered_log)
        if sig_id != -1:
            self.signature_map[sig_id].log_ids.append(id)  # 精确的找到
        else:
            # print('cant find in prefix tree, current log:', filtered_log)
            sig_id = self.lookup_template(filtered_log)
            if sig_id != -1:
                self.signature_map[sig_id].log_ids.append(id)  # 模糊查找到
            else:
                # new group
                cur_idx = -1
                max_common_length = -1
                max_common_signature = []

                # 简单遍历查找 查找最相似的那个日志组
                for idj, sig_obj in self.signature_map.items():
                    # pruning skill 2: calc jaccard similarity for them to skip those distance < 1/3
                    if self.jaccard(sig_obj.signature, filtered_log) > 0.5:
                        # calc LCS problem
                        comp = LCSUtil(sig_obj.signature, filtered_log, self.REPL)

                        if comp.c[-1][-1] > max_common_length:
                            cur_idx = idj  # 更新最大值序号
                            max_common_signature = sig_obj.signature  # 更新最大值的签名
                            comp.backtrack()
                            max_common_result = comp.result  # 更新最大值的签名结果
                            max_common_length = comp.c[-1][-1]  # 更新最大值的签名长度
                        elif comp.c[-1][-1] == max_common_length and sig_obj.length < len(max_common_signature):
                            cur_idx = idj
                            comp.backtrack()
                            max_common_result = comp.result
                            max_common_length = len(comp.result)

                # 判断是否合并还是新增
                if float(max_common_length) / len(filtered_log) >= self.threshold:
                    new_template = max_common_result
                    # 3.动态加入到前缀树中
                    self.delete(self.signature_map[cur_idx].signature)

                    self.signature_map[cur_idx].signature = new_template
                    self.signature_map[cur_idx].length = len(new_template)
                    self.signature_map[cur_idx].log_ids.append(id)

                    self.insert(new_template, cur_idx)
                else:
                    # 新建一个sig object
                    n_sig_obj = SignatureObject(filtered_log, id)
                    self.current_signature_ids = n_sig_obj.sig_id
                    # 将sig 直接的插入进去
                    self.signature_map[n_sig_obj.sig_id] = n_sig_obj
                    self.insert(filtered_log, n_sig_obj.sig_id)

        # print('---------information---------')
        # print(self.current_signature_ids)
        # for _, item in self.signature_map.items():
        #     print(item.sig_id, item.signature, item.log_ids)

    def jaccard(self, p, q):
        '''
        计算jaccard相似度
        :param set1:
        :param set2:
        :return:
        '''
        set_p, set_q = set(p), set(q)

        return len(set_p & set_q) / float(len(set_p | set_q))

    def _match(self, str1, str2):
        '''
        模板串与长串的匹配过程 O(max len(str1, str2))
        :param str1: 模板串
        :param str2: 长串
        :return:
        '''
        if str1 == '' and str2 == '':
            return True
        elif str1 == '' or str2 == '':
            return False
        pi = 0
        pt = 0
        while pt < len(str2) and pi < len(str1):
            if str2[pt] == str1[pi]:
                pi += 1
            pt += 1
        if pi == len(str1):
            return True
        else:
            return False

    def lookup(self, log_sequence):
        '''
        在前缀树上查找log(精确地查找) 双指针子串匹配
        :param log_sequence: log str array
        :return:
        '''
        i = 0
        n = len(log_sequence)
        ptr = self.root
        while i < n:
            # print('i:',i, '  ' ,log_sequence[i], ptr.children)
            if log_sequence[i] in ptr.children:
                # print(log_sequence[i])
                ptr = ptr.children[log_sequence[i]]
            elif self.REPL in ptr.children:
                ptr = ptr.children[self.REPL]
            i += 1
        # print('end:', ptr.signature_id)
        return ptr.signature_id  # 失败会返回-1

    def lookup_template(self, log_sequence):
        '''
        在哈希表中查找log 使用双指针子串匹配 O(m n)
        :param log_sequence:
        :return:
        '''
        for idj, lcsobj in self.signature_map.items():
            # pruning skill 1: skip those signature whose length is less than 1/2 log sequence
            if float(len(lcsobj.signature)) / len(log_sequence) >= 0.5:
                if self._match(lcsobj.signature, log_sequence):
                    return idj
        return -1

    def delete(self, log_sequence):
        '''
        删除前缀树上的前缀
        :param log_sequence:
        :return:
        '''
        n = len(log_sequence)
        ptr = self.root
        i = 0

        while i < n:
            if log_sequence[i] not in ptr.children:
                return
            else:
                if ptr.children[log_sequence[i]].count > 1:
                    ptr.children[log_sequence[i]].count -= 1
                    ptr = ptr.children[log_sequence[i]]
                else:
                    next_node = ptr.children[log_sequence[i]]
                    del ptr.children[log_sequence[i]]
                    ptr = next_node
            i += 1

    def insert(self, log_sequence, log_id=None):
        """
        认为当前是新事件，则更新已有集合
        :param log_sequence: log str array
        :return: None, insert the tree Inplace
        """
        if not log_id:
            raise ValueError('Must give log id')

        n = len(log_sequence)
        ptr = self.root
        i = 0
        while i < n:
            if log_sequence[i] not in ptr.children:
                _node = TreeParserNode()
                ptr.children[log_sequence[i]] = _node
                ptr = _node
            else:
                ptr.children[log_sequence[i]].count += 1
                ptr = ptr.children[log_sequence[i]]
            i += 1
        # 将log 的 id 给予叶子节点
        ptr.signature_id = log_id

if __name__ == '__main__':
    spell_parser = Spell(reg_file='./config.reg_exps.txt', threshold=0.5)

    spell_parser._online_train('blk 124219214 asa Receive from node 4', 1)
    # spell_parser._online_train('blk 124219214 asa Receive from node 4', 2)
    spell_parser._online_train('blk 124219214 ffwqwq 1241241 Done to node 4', 2)
    spell_parser._online_train('blk 124219214 ffwqwq Done to node 4', 3)
    spell_parser._online_train('blk 782174184 Instance raer1421MManf142v Receive from node 356', 4)

    spell_parser._online_train('Tcp net down daafa aswf qe 1241', 5)
    spell_parser._online_train('Tcp net down daafa 12 qe 1241', 6)
    spell_parser._online_train('Tcp qws down daafa 214 qe 1241', 7)
    spell_parser._online_train('Tcp qws down daafa 421 qe 1241', 8)
    spell_parser._online_train('Tcp qws down daafa 14 qe 1241', 9)

    spell_parser._online_train('delete block_1', 10)
    spell_parser._online_train('delete block_3 block_4', 11)
    spell_parser._online_train('delete block_6', 12)

    gc.collect()
    # where = visualize_spell_gvfile(spell_parser)
    # spell_parser.dfs_traverse()
    # FP_tree