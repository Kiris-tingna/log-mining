#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/9/23 15:21
 @Author  : Kiristingna
 @File    : dependency_expriments.py
 @Software: PyCharm
"""
import gc
import math

from logparser.dependency import LagEM, LagICE

gc.disable()
# ================ Ex2. 用于分析 event 之间的相关性 ===================
# experiment record:
#       1. lag em 算法效果不好
#       2. lag ice 算法的结果严重依赖子空间采样的参数


# step1: collect data
events = {0: [], 1: []}
with open('./data/hdfs_event_timepoints.log') as f:
    for line in f.readlines():
        data = line.split(',')
        cate = int(data[0])
        timestamp = round(float(data[1]), 4)
        events[cate].append(timestamp)

# step2: run lag em
lag_em = LagEM(an=events[0], cq=events[1], miu=15, sigma2=3)
miu, sigma2 = lag_em.run(threshold=0.02)
print('miu: {} sigma2: {} ratio: {}'.format(miu, sigma2, miu / math.sqrt(sigma2)))

lag_ice = LagICE(an=events[0], cq=events[1], lag_init=100)
lag = lag_ice.run(an_samples=30, cq_samples=50, sample_times=50, threshold=0.01)
print(lag)

gc.collect()
