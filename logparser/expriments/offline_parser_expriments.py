#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/9/21 11:16
 @Author  : Kiristingna
 @File    : offline_parser_expriments.py
 @Software: PyCharm
"""
# import multiprocessing
from logparser.parser import Spell, Drain, Draga, BasicSignatureGren
from logparser.utils import visualize_spell_gvfile, visualize_drain_gvfile, strict_time
import gc
import pandas as pd

# ================ Ex1. 用于离线分析和比较各个parser的效果 ===================
# generally idea:
#       将日志解析器的前缀树可视化、构建workflow等
# experiment record:
#   1. spell的树上有路径偏移的情况产生
#   2. drain 能识别异常日志模式（突增的日志长度）， 但是drain算法被noise影响的问题比较严重 （有大量重复的日志signature 在不同的bucket上）
#   3. Spell 的事件个数会比其他算法多（可能这是Spell 本省的特性）
# Solutions:
#   1. ADD 加入日志对于一些特殊规则的分割
#   2. 这个问题在drage里已经被修正了 原理就是加入输出层进行合并 (add 2018/10/22 这个似乎不是drain的问题)
#   3. Spell 的事件会分的更细
# =========================================================================

gc.disable()

'''
 ---------------- step 1 : construct a parser with domain knowledge ---------------
 Example: 使用的 hdfs 日志 对应的解析器生成方法为
          spell_parser = Spell(reg_file='../config/config.hdfs.txt', threshold=0.5)
          drain_parser = Drain(reg_file='../config/config.hdfs.txt', max_child=10, max_depth=4, min_similarity=0.5)
 1. 使用的 iaas nova 日志 对应解析规则在 config.iaas.txt 中
'''
spell_parser = Spell(reg_file='../config/config.iaas.txt', threshold=0.7)
drain_parser = Drain(reg_file='../config/config.iaas.txt', max_child=10, max_depth=4, min_similarity=0.5)
draga_parser = Draga(reg_file='../config/config.iaas.txt', max_child=10, merge_threshold=0.9)
bsg_parser = BasicSignatureGren(reg_file='../config/config.iaas.txt', global_st=0.7)

'''
 -------------------- step 2 : train data line step by line  -------------------
 Example: 以下用法适用于dataframe的部分
'''

file = '../data/zte_tongbu_filtered.csv'
# file = '../data/zte_delete_filtered.csv'
# file = '../data/zte_failed_filtered.csv'


df = pd.read_csv(file)
start = strict_time()
for idx, row in df.iterrows():
    # spell_parser.online_train(row.message, row.log_id)
    drain_parser.online_train(row.message, row.log_id)
    # draga_parser.online_train(row.message, row.log_id)
    # bsg_parser.online_train(row.message, row.log_id)

end = strict_time()
print(end - start)


gc.collect()

'''
----------------------------- step3-1. result debug + 可视化树结构 ------------------------------------
 Example: 
'''
# 1. spell 的模板可视化
# spell_parser.get_final_template()
# visualize_spell_gvfile(spell_parser, path='../data/Ex1/graphviz_spell_iaas.gv')

# 2. drain的 模板可视化
drain_parser.get_final_template()
visualize_drain_gvfile(drain_parser, path="../data/Ex1/graphviz_drain_iaas.gv")

# 3. drage 的模板可视化
# draga_parser.get_final_tempalte()

# 4. bsg 的模板可视化
# bsg_parser.get_final_template()
