#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/12/4 14:08
 @Author  : Kiristingna
 @File    : parser_classfication_expriments.py
 @Software: PyCharm
"""
import pandas as pd
import math

# ================ Ex6. 用于分析parser的结果准确率 ===================
# 比对和标准模板之间的差距
# 公式
#              北邮公式
# ==================================================================

'''
格式  event -> log id (行号)
'''
# with open('../data/standard_event_id.txt') as f:
#     events = [int(line) for line in f.readlines()]
#     log_ids = [i for i in range(len(events))]
#
#     df = pd.DataFrame({'event': events, 'log_id': log_ids, 'time_stamp': 0})
#     df.to_csv('../data/准确率待测试数据/standard.csv', index=False)


# --------------------------- 开始比对 ----------------------------------
data_to_compare = '../data/准确率待测试数据/Spell.csv'
data_standard = '../data/准确率待测试数据/standard.csv'

df1 = pd.read_csv(data_to_compare, engine='python')
df2 = pd.read_csv(data_standard, engine='python')

def exact_mapping_and_ids(df):
    '''
    抽取每一个事件的id集合
    :param df:
    :return:
    '''
    set_mapping = {}
    events = df['event'].unique()
    for ev in events:
        ev_log_ids = df[df['event'] == ev]['log_id'].values
        set_mapping[ev] = set(ev_log_ids)

    return set_mapping


G = exact_mapping_and_ids(df1)
F = exact_mapping_and_ids(df2)

df = pd.merge(df1, df2, how='left', on='log_id')
merged_df = df[['log_id', 'event_x', 'event_y']].sort_values(by='log_id')
merged_df.set_index('log_id', inplace=True)

s = 0
for idx, row in merged_df.iterrows():
    # 经过我们的方法得到的id
    g_i = row['event_x']
    # 标准的id
    f_i = row['event_y']

    c1 = len(G[g_i] & F[f_i]) / len(G[g_i])
    c2 = len(G[g_i] & F[f_i]) / len(F[f_i])

    s += c1 ** 2 + math.sqrt(c2)

p = s / (2 * len(merged_df))

print(p)
