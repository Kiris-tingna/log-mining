#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/9/21 11:16
 @Author  : Kiristingna
 @File    : online_parser_expriments.py
 @Software: PyCharm
"""
# import multiprocessing
from logparser.parser import *
from logparser.utils import *
import gc
from logparser.formalizer import STREAMFormatter


# ================ Ex2. 用于在线模式分析和比较各个parser的效果 ===================
# generally idea:
#       在线解析日志的模式 预处理提取（正则） + 二次 正则 分割
# experiment record:
#   1. 需要结解决多行日志的问题
# Solutions:
#   1. 使用正则去掉 所有（）{} [] 之间的换行 判断每一行前30个字符是否能提取出一个时间模式
# =========================================================================
gc.disable()

'''
 ---------------- step 1 : construct a parser with domain knowledge ---------------
 Example: 使用的 paas 日志 对应的解析器生成方法为
          stream.online_parse_one_dir(dir, parser name)
 1. 使用的 paas 日志 对应解析规则在 config.paas.txt 中
'''
spell_parser = Spell(reg_file='../config/config.paas.txt', threshold=0.7)
drain_parser = Drain(reg_file='../config/config.paas.txt', max_child=20, max_depth=4, min_similarity=0.7)
draga_parser = Draga(reg_file='../config/config.paas.txt', max_child=20, merge_threshold=0.7)
bsg_parser = BSG(reg_file='../config/config.paas.txt', global_st=0.7)
bsgi_parser = BSGI(reg_file='../config/config.paas.txt', global_st=0.7)

data_dir = '../../../Paas/54556'
# data_dir = '../data/test'
stream = STREAMFormatter()

'''
 --------------------- step 2 : train data line step by line  ---------------------
 Example: 以下用法适用于dataframe的部分
'''
start = strict_time()
# following part is for call parsers ...
# stream.online_parse_one_dir(data_dir, spell_parser)
# stream.online_parse_one_dir(data_dir, drain_parser)
# stream.online_parse_one_dir(data_dir, draga_parser)
# stream.online_parse_one_dir(data_dir, bsg_parser)
# stream.online_parse_one_dir(data_dir, bsgi_parser)
end = strict_time()
print(end - start)

gc.collect()
'''
----------------------------- step3-1. result debug + 可视化树结构 ------------------------------------
 Example: 
'''
# 1. spell 的模板可视化
# spell_parser.get_final_template()
# visualize_spell_gvfile(spell_parser, path='../data/Ex2/graphviz_spell_paas.gv')

# 2. drain的 模板可视化
# drain_parser.get_final_template()
# visualize_drain_gvfile(drain_parser, path="../data/Ex2/graphviz_drain_paas.gv")

# 3. drage 的模板可视化
# draga_parser.get_final_tempalte()

# 4. bsg 的模板可视化
# bsg_parser.get_final_template()
# visualize_bsg_gvfile(bsg_parser, path='../data/Ex2/graphviz_bsg_paas.gv')

# 5. bsgi 的模板可视化
# bsgi_parser.get_final_template()
# visualize_bsg_gvfile(bsgi_parser, path='../data/Ex2/graphviz_bsgi_paas.gv')


# 部分的手动可视化
# visualize_gv_manually('../data/Ex2/graphviz_spell_paas-2018-11-06.gv', render_mode='twopi')
# visualize_gv_manually('../data/Ex2/graphviz_drain_paas-2018-11-06.gv', render_mode='twopi')
visualize_gv_manually('../data/Ex2/graphviz_bsgi_paas-2018-11-06.gv', render_mode='twopi')
