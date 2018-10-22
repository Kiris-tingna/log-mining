#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/9/21 11:16
 @Author  : Kiristingna
 @File    : online_parser_expriments.py
 @Software: PyCharm
"""
# import multiprocessing
from logparser.parser import Spell, Drain, Draga
from logparser.utils import visualize_spell_gvfile, visualize_drain_gvfile, strict_time
import gc
from logparser.formalizer import STREAMFormatter


# ================ Ex2. 用于在线模式分析和比较各个parser的效果 ===================
# generally idea:
#       在线解析日志的模式 预处理提取（正则） + 二次 正则 分割
# experiment record:
#   1. 需要结解决多行日志的问题
# Solutions:
#   1. 使用正则去掉 所有（）{} [] 之间的换行
# =========================================================================
gc.disable()

'''
 ---------------- step 1 : construct a parser with domain knowledge ---------------
 Example: 使用的 paas 日志 对应的解析器生成方法为
          stream.online_parse_one_dir(dir, parser name)
 1. 使用的 paas 日志 对应解析规则在 config.paas.txt 中
'''
spell_parser = Spell(reg_file='../config/config.paas.txt', threshold=0.7)
drain_parser = Drain(reg_file='../config/config.paas.txt', max_child=10, max_depth=4, min_similarity=0.5)
draga_parser = Draga(reg_file='../config/config.paas.txt', max_child=10, merge_threshold=0.9)

data_dir = '../../../Paas/54534/192.169.8.230'
stream = STREAMFormatter()

'''
 --------------------- step 2 : train data line step by line  ---------------------
 Example: 以下用法适用于dataframe的部分
'''
start = strict_time()
stream.online_parse_one_dir(data_dir, spell_parser)
end = strict_time()
print(end - start)

gc.collect()

'''
----------------------------- step3-1. result debug + 可视化树结构 ------------------------------------
 Example: 
'''
# 1. spell 的模板可视化
spell_parser.get_final_template()
visualize_spell_gvfile(spell_parser, path='../data/Ex2/graphviz_spell_paas.gv')

# 2. drain的 模板可视化
# drain_parser.get_final_template()
# visualize_drain_gvfile(drain_parser, path="./data/Ex2/graphviz_drain_paas.gv")

# 3. drage 的模板可视化
# draga_parser.get_final_tempalte()
