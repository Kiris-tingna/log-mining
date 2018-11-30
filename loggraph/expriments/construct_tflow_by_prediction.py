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

# --------------------- step1. 针对单个事务确定训练输入数据  --------------------
event_sequences = {}
with open('../data/deploy_event_id.csv') as f:
    for line in f.readlines():
        deploy = line.strip('\n').strip('[').strip(']').split(',')
        deploy_id = deploy[0]
        sequences = [int(event.strip(' ')) for event in deploy[1:]]
        event_sequences[deploy_id] = sequences

print(event_sequences['60017'][:20])
print(event_sequences['60349'][:20])
print(event_sequences['59442'][:20])

print(event_sequences['60017'][-20:])
print(event_sequences['60349'][-20:])
print(event_sequences['59442'][-20:])

# --------------------- step2. 训练模型  --------------------



# ----------------------------------------------------------


# --------------------- step3. 输入待检测数据 判断与真实事件的 --------------------





# ------------------------------------------------------------------------------
