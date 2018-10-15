#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/9/21 11:16
 @Author  : Kiristingna
 @File    : parser_expriments.py
 @Software: PyCharm
"""
import multiprocessing
from logparser.parser import Spell, Drain
from logparser.utils import visualize_spell_gvfile, visualize_drain_gvfile
import gc

# ================ Ex1. 用于分析和比较各个parser的效果 ===================
# generally idea:
#       将日志解析器的前缀树可视化、构建workflow等
# experiment record:
#   1. spell的树上有路径偏移的情况产生
#   2. drain 能识别异常日志模式（突增的日志长度）， 但是drain算法被noise影响的问题比较严重 （有大量重复的日志signature 在不同的bucket上）

# ---------------- step 1 : construct a parser with domain knowledge ---------------
spell_parser = Spell(reg_file='./config/config.hdfs.txt', threshold=0.5)
drain_parser = Drain(reg_file='./config/config.hdfs.txt', max_child=10, max_depth=4, min_similarity=0.5)


# -------------------- step 2 : train data line step by line  -------------------
with open('./data/hdfs_sample_2k.log', 'r') as f:
    for line in f.readlines():
        data = line.strip().split('\t')
        log_id = int(data[0].strip())
        log_entry = data[1]
        # 输出的是每一次调用online_train所用的时间
        spell_parser.online_train(log_entry, log_id)
        drain_parser.online_train(log_entry, log_id)

# ----------------------------- result debug ------------------------------------
for item in drain_parser.LogClusterMap:
    print(item.cluster_id, item.log_template, item.log_ids)

gc.collect()

# ------------------------ step 3 : 可视化树结构 ---------------------------
visualize_spell_gvfile(spell_parser, path='./data/graphviz_spell_hdfs.gv')
visualize_drain_gvfile(drain_parser, path="./data/graphviz_drain_hdfs.gv")

