#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/10/22 14:28
 @Author  : Tinkle
 @File    : LogSed.py
 @Software: PyCharm
"""
import bisect
import collections
import datetime
import pandas as pd
# from logparser.utils import Timer

try:
    from graphviz import Digraph
except Exception as e:
    print("can't import graphviz")

import time
import sys
import functools


def strict_time():
    if sys.platform == "win32":
        return time.clock()
    else:
        return time.time()


def Timer(func):
    '''
    计时器 用于分析算法运行时间
    :param func:
    :return:
    '''
    @functools.wraps(func)
    def fn(*args, **kwargs):
        _start_time = strict_time()
        _func_result = func(*args, **kwargs)
        _end_time = strict_time()
        print('{} cost：{}s seconds'.format(func.__name__, _end_time - _start_time))
        return _func_result
    return fn

def datetime_timestamp(dt):
    """
    :param dt: string
    :return: Unix time stamp
    """
    return int(time.mktime(time.strptime(dt, '%Y-%m-%d %H:%M:%S')))


class LogSed(object):
    """
    @author: Tong Jia, Lin Yang
    @paper:  LogSed: Anomaly Diagnosis through Mining Time-weighted Control Flow Graph in Logs

    *********************************************
    LogSed
    1). Log Parsing Raw Logs -> template set
    2). Filter operational logs
        step 1: checking several predecessors and successors of a log rather than direct
                predecessor and direct successor.
        step 2: apply DBSCAN on the templates based on Levenshtein distance. Then compute the
                occurrence percentage of all templates in each cluster.
    3). Time-weighted CFG mining
        step 1: FS group computation
        step 2: Edge time weight computation
                the maximum time difference of all <Ti, Tj> pairs is recorded as the time weight
    4). Determine transaction flow
        step 1: Transaction border splitting
        step 2: Construct transaction flow

    ***********************************************
    Parameter settings
    vicinity_window: 指定邻域数
    vicinity_threshold：邻域过滤阈值，如果template的所有邻域内的template都低于该阈值，
                        则被认为是operational template
    cluster_threshold: 聚类过滤阈值，???
    time_period: 构建FS group的时间间隔
    FS_threshold: FS group过滤低频template
    transaction_epsilon: smoothing function epsilon
    outlier_epsilon: outlier transaction time
    """
    def __init__(self,
                 vicinity_window = 3,
                 vicinity_threshold = 10,
                 cluster_threshold = 0.7,
                 time_period = 5,
                 FS_threshold = 0.8,
                 transaction_epsilon = 1,
                 outlier_epsilon = 3
                 ):
        self.vicinity_window = vicinity_window
        self.vicinity_threshold = vicinity_threshold
        self.cluster_threshold = cluster_threshold
        self.time_period = time_period
        self.FS_threshold = FS_threshold
        self.transaction_epsilon = transaction_epsilon
        self.outlier_epsilon = outlier_epsilon

        self.max_event = 1000

    @Timer
    def filter_operational_logs(self, time_series):
        vicinity_matrix = [[0 for i in range(self.max_event)] for j in range(self.max_event)]
        length = len(time_series)
        for i in range(length):
            for j in range(1, self.vicinity_window + 1):
                if i + j < length:
                    root = time_series[i][0]
                    vicinity = time_series[i + j][0]
                    vicinity_matrix[root][vicinity] += 1
                    vicinity_matrix[vicinity][root] += 1

        operational_logs = []
        a0, a1 = 0, 0
        for event in range(self.max_event):
            if(sum(vicinity_matrix[event])):
                a0 += 1
                if not any(filter(lambda x: x > self.vicinity_threshold, vicinity_matrix[event])):
                    a1 += 1
                    operational_logs.append(event)
        print("There are %d templates, %d of them are operational logs." % (a0, a1))

        # (TODO tinkle): cluster step
        return list(filter(lambda x: x[0] not in operational_logs, time_series))

    @Timer
    def time_weighted_CFG_mining(self, time_series):
        # step 1: FS group computation
        # construct successor group
        FS_group = collections.defaultdict(list)
        event_count = collections.defaultdict(int)

        length = len(time_series)
        start = 0
        while(start < length - 1):
            pos = start + 1
            while(pos < length and (time_series[pos][1] - time_series[start][1]) < self.time_period):
                pos += 1
            cur_event = time_series[start][0]
            cur_time = time_series[start][1]

            series = sorted(list(map(lambda x:(x[0], x[1] - cur_time), time_series[start + 1 : pos])), \
                            key = lambda x:x[0])

            unique_series = [series[i] for i in range(len(series)) \
                             if series[i][0]!=cur_event and \
                             (i == 0 or (i > 0 and series[i][0] != series[i-1][0]))]

            FS_group[cur_event] += unique_series
            event_count[cur_event] += 1
            start += 1

        for event in FS_group:
            group = list(map(lambda x:x[0], FS_group[event]))
            unique_group = list(set(group))
            unique_group = list(filter(lambda x: group.count(x) / event_count[event] > self.FS_threshold, \
                                       unique_group))
            FS_group[event] = list(filter(lambda x: x[0] in unique_group, FS_group[event]))

        # (TODO Tinkle): Verify sub-structure

        # step 2: Edge time weight computation
        control_flow_graph = [[-1 for i in range(self.max_event)] for j in range(self.max_event)]
        successor_map = dict()
        for event in FS_group:
            for successor_time in FS_group[event]:
                successor = successor_time[0]
                transfer_time = successor_time[1]
                if event not in successor_map:
                    successor_map[event] = collections.defaultdict(list)
                bisect.insort_left(successor_map[event][successor], transfer_time)

        for i in range(self.max_event):
            for j in range(self.max_event):
                if i != j and i in successor_map and len(successor_map[i][j]):
                    control_flow_graph[i][j] = successor_map[i][j][-1]
        return control_flow_graph, successor_map

    @Timer
    def determine_transaction_flow(self, successor_map):
        transaction_flow_graph = [[-1 for i in range(self.max_event)] for j in range(self.max_event)]
        for event in successor_map:
            for successor in successor_map[event]:
                count, transaction_time = -1, -1
                times = successor_map[event][successor]
                for transfer_time in times:
                    left = bisect.bisect_right(times, transfer_time - self.transaction_epsilon)
                    right = bisect.bisect_left(times, transfer_time + self.transaction_epsilon)
                    if right - left >= count:
                        count = right - left
                        transaction_time = transfer_time
                if transaction_time > -1 and transaction_time < self.outlier_epsilon:
                    transaction_flow_graph[event][successor] = transaction_time
        return transaction_flow_graph

def visualize_logsed_gvfile(control_flow_graph, transaction_flow_graph, path="../graphviz-logsed.gv"):
    gv_object = Digraph(strict=True, comment='The visualization of prefix tree '+ str(datetime.date.today()))
    length = len(control_flow_graph)
    visited = [False for i in range(length)]
    nodes = 0
    edges = 0
    for i in range(length):
        for j in range(length):
            if transaction_flow_graph[i][j] > -1:
                if not visited[i]:
                    nodes +=1
                    gv_object.node('N_'+str(i), shape='circle')
                    visited[i] = True
                if not visited[j]:
                    nodes +=1
                    visited[j] = True
                    gv_object.node('N_'+str(j), shape='circle')
                gv_object.edge('N_'+str(i), 'N_'+str(j), label=str(transaction_flow_graph[i][j]))
                edges += 1
    print('There are %d edges with %d nodes' % (edges, nodes))
    ext = '.gv'
    if ext in path:
        path = path[:-3] + "-" + str(datetime.date.today()) + ext

    with open(path, 'w', encoding='utf-8') as f:
        f.write(gv_object.source)

    gv_object.render(path, view=True)
    return path

if __name__ == '__main__':
    file = '../data/message.csv'
    df = pd.read_csv(file)#,nrows=10000)
    '''
    df.time_stamp = df.time_stamp.map(lambda x:datetime_timestamp(x))
    df = df.sort_values(by=['time_stamp'])
    df.to_csv('../message.csv', index = None)
    '''
    time_series = []
    for idx, row in df.iterrows():
        time_series.append((row.event, row.time_stamp))
    S = LogSed()
    time_series = S.filter_operational_logs(time_series)
    control_flow_graph, successor_map = S.time_weighted_CFG_mining(time_series)
    transaction_flow_graph = S.determine_transaction_flow(successor_map)
    visualize_logsed_gvfile(control_flow_graph, transaction_flow_graph, path="../graphviz-logsed.gv")
