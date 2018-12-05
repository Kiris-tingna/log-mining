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


def bupt_metic(merged_df):
    '''
    北邮的衡量方式
    :param merged_df:
    :return:
    '''
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

    return p


def njupt_metic(merged_df):
    s = 0
    for idx, row in merged_df.iterrows():
        # 经过我们的方法得到的id
        g_i = row['event_x']
        # 标准的id
        f_i = row['event_y']

        c1 = len(G[g_i] & F[f_i]) / len(G[g_i])
        c2 = len(G[g_i] & F[f_i]) / len(F[f_i])

        s += c1 + c2

    p = s / (2 * len(merged_df))

    return p


# --------------------------- 开始比对 ----------------------------------
data_to_compare = {
    'BSG_GINI': '../data/准确率待测试数据/BasicSignatureGrenGini.csv',
    'BSG': '../data/准确率待测试数据/BasicSignatureGren.csv',
    'Spell': '../data/准确率待测试数据/Spell.csv',
    'Draga': '../data/准确率待测试数据/Draga.csv',
    'Drain': '../data/准确率待测试数据/Drain.csv'
}

data_standard = '../data/准确率待测试数据/standard.csv'
df2 = pd.read_csv(data_standard, engine='python')
F = exact_mapping_and_ids(df2)

for p, file in data_to_compare.items():
    df1 = pd.read_csv(file, engine='python')
    G = exact_mapping_and_ids(df1)
    df = pd.merge(df1, df2, how='left', on='log_id')

    merged_df = df[['log_id', 'event_x', 'event_y']].sort_values(by='log_id')
    merged_df.set_index('log_id', inplace=True)

    r1 = bupt_metic(merged_df)
    r2 = njupt_metic(merged_df)

    print("parser name: {}, bupt evalution: {}, njupt evalution: {}".format(p, r1, r2))
