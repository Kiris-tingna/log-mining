#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/9/21 11:16
 @Author  : Kiristingna
 @File    : parser_expriments.py
 @Software: PyCharm
"""
import multiprocessing
from logparser.parser import Spell, Drain, Draga
from logparser.utils import visualize_spell_gvfile, visualize_drain_gvfile, strict_time
import gc
import pandas as pd


# ================ Ex1. 用于分析和比较各个parser的效果 ===================
# generally idea:
#       将日志解析器的前缀树可视化、构建workflow等
# experiment record:
#   1. spell的树上有路径偏移的情况产生
#   2. drain 能识别异常日志模式（突增的日志长度）， 但是drain算法被noise影响的问题比较严重 （有大量重复的日志signature 在不同的bucket上）
#   3. Spell 的事件个数会比其他算法多（可能这是Spell 本省的特性）


# Solutions:
#   1. ADD 加入日志对于一些特殊规则的分割
#   2. 这个问题在drage里已经被修正了 原理就是加入输出层进行合并



# ---------------- step 1 : construct a parser with domain knowledge ---------------
# spell_parser = Spell(reg_file='./config/config.hdfs.txt', threshold=0.5)
# drain_parser = Drain(reg_file='./config/config.hdfs.txt', max_child=10, max_depth=4, min_similarity=0.5)


spell_parser = Spell(reg_file='./config/config.nova.txt', threshold=0.5)
drain_parser = Drain(reg_file='./config/config.nova.txt', max_child=10, max_depth=4, min_similarity=0.5)
draga_parser = Draga(reg_file='./config/config.nova.txt', max_child=10, merge_threshold=0.9)

# -------------------- step 2 : train data line step by line  -------------------
# with open('./data/hdfs_sample_2k.log', 'r') as f:
#     for line in f.readlines():
#         data = line.strip().split('\t')
#         log_id = int(data[0].strip())
#         log_entry = data[1]
#         # 输出的是每一次调用online_train所用的时间
#         spell_parser.online_train(log_entry, log_id)
#         drain_parser.online_train(log_entry, log_id)


# ----------------- 适用于dataframe的部分 ----------------
file = './data/zte_tongbu_filtered.csv'
# file = './data/zte_delete_filtered.csv'
# file = './data/zte_failed_filtered.csv'

start = strict_time()
df = pd.read_csv(file)
for idx, row in df.iterrows():
    spell_parser.online_train(row.message, row.log_id)
    # drain_parser.online_train(row.message, row.log_id)
    # draga_parser.online_train(row.message, row.log_id)

end = strict_time()

print(end - start)

# ----------------------------- result debug ------------------------------------
# for item in drain_parser.LogClusterMap:
#     print(item.cluster_id, item.log_template, item.log_ids)

gc.collect()

# ------------------------ step 3 : 可视化树结构 ---------------------------
visualize_spell_gvfile(spell_parser, path='./data/graphviz_spell_hdfs.gv')
# visualize_drain_gvfile(drain_parser, path="./data/graphviz_drain_hdfs.gv")

# draga_parser.get_final_tempalte()
