#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/10/27 22:37
 @Author  : Kiristingna
 @File    : construct_tflow_by_prediction.py
 @Software: PyCharm
"""
from loggraph.eventchain import CompactPredictionTree as CPT
import numpy as np
from collections import defaultdict, OrderedDict
import matplotlib.pyplot as plt
import pandas as pd


# --------------------- step1. 针对单个事务确定训练输入数据  --------------------
event_sequences = {}
with open('../data/deploy_event_id.csv') as f:
    for line in f.readlines():
        deploy = line.strip('\n').strip('[').strip(']').split(',')
        deploy_id = deploy[0]
        sequences = [int(event.strip(' ')) for event in deploy[1:]]
        event_sequences[deploy_id] = sequences


def stat_window_observation(es, verbose = False):
    '''
    分窗口统计观察
    :param start:
    :param end:
    :param es:
    :return:
    '''
    event_frequency = defaultdict(int)
    window = {}
    hist = {}
    for d, s in es.items():
        sequences = s
        for e in set(sequences):
            event_frequency[e] += 1
        window[d] = sequences

    for k, v in event_frequency.items():
        if v in hist:
            hist[v].append(k)
        else:
            hist[v] = [k]

    hist_sequence = OrderedDict(sorted(hist.items(), key=lambda x: x[0], reverse=True))
    if verbose:
        c1 = 0
        c2 = 0
        for k, v in hist_sequence.items():
            if k ==154 or k ==153:
                c1 += len(v)
            c2 +=len(v)
            print("occur {} times : {}".format(k, v))
        print(c1 / c2)
    return window, event_frequency


def thresold_window_alignment(window, frequency, thresold=100, verbose=False):
    slice_window = []
    for d, w in window.items():
        appear = set()
        major_event = []
        for e in w:
            if not e in appear and (frequency[e] == 154 or frequency[e] == 153):
                appear.add(e)
                major_event.append(e)

        if verbose:
            if d in ['59468', '59483', '59565', '59590', '59591', '59594']:
                print("{} deploy: {}".format(d, major_event))

        slice_window.append(major_event)
    df = pd.DataFrame(np.array(slice_window), index=window.keys())
    return df




w, f = stat_window_observation(event_sequences, verbose=True)
# df = thresold_window_alignment(w, f, verbose=True)
#
# # 合并结果
# df.to_csv('../data/deploy_event_id_filtered.csv',  index=True, index_label='deploy_id')
# --------------------- step2. 训练模型  --------------------



# ----------------------------------------------------------


# --------------------- step3. 输入待检测数据 判断与真实事件的 --------------------





# ------------------------------------------------------------------------------
