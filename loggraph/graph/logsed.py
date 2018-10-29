#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/10/22 14:28
 @Author  : Tinkle
 @File    : logsed.py
 @Software: PyCharm
"""
import bisect
import collections
import pandas as pd
import numpy as np
from logparser.utils import Timer, visualize_logsed_gvfile, datetime_to_timestamp


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
    Example:
        1. 输入
    """
    def __init__(self,
                 vicinity_window=3,
                 vicinity_threshold=10,
                 cluster_threshold=0.7,
                 time_period=5,
                 FS_threshold=0.8,
                 transaction_epsilon=1,
                 outlier_epsilon=3,
                 max_event=1000
                 ):
        '''
        初始化 参数
        Parameter settings
        :param vicinity_window: 指定邻域数
        :param vicinity_threshold: 邻域过滤阈值，如果template的所有邻域内的template都低于该阈值，
                                    则被认为是operational template
        :param cluster_threshold: 聚类过滤阈值，???
        :param time_period: 构建FS group的时间间隔
        :param FS_threshold: FS group过滤低频template
        :param transaction_epsilon: smoothing function epsilon
        :param outlier_epsilon: outlier transaction time
        :param max_event: 事件最大序号 用于构建matrix
        '''
        self.vicinity_window = vicinity_window
        self.vicinity_threshold = vicinity_threshold
        self.cluster_threshold = cluster_threshold
        self.time_period = time_period
        self.FS_threshold = FS_threshold
        self.transaction_epsilon = transaction_epsilon
        self.outlier_epsilon = outlier_epsilon
        self.max_event = max_event + 1

    @Timer
    def filter_operational_logs(self, time_series):
        '''
        从原始日志序列中过滤操作日志
        考察一个事件，他的所有邻域事件的个数都不超过vicinity_threshold 就被认为是操作日志
        :param time_series: [(event id, event time) , ....]
        :return: 去除操作日志后的序列
        '''
        # Step1：count matrix for events
        vicinity_matrix = [[0 for _ in range(self.max_event)] for _ in range(self.max_event)]
        # 检查长度必须一致
        if len(time_series) != len(time_series):
            raise AssertionError("two sequence must have the same length")
        # find all relational events follow current event
        sequence_length = len(time_series)
        for i in range(sequence_length):
            for j in range(1, self.vicinity_window + 1):
                if i + j < sequence_length:
                    root = time_series[i][0]
                    vicinity = time_series[i + j][0]
                    vicinity_matrix[root][vicinity] += 1
                    vicinity_matrix[vicinity][root] += 1

        # Step2：考察每一个事件领域内事件的个数情况
        operational_logs = []
        ob_matrix = []

        noraml_log_number, opt_log_number = 0, 0
        for eventID in range(self.max_event):
            if sum(vicinity_matrix[eventID]):
                noraml_log_number += 1
                # 过滤操作日志的关键步骤 根据阈值
                if not any(filter(lambda x: x > self.vicinity_threshold, vicinity_matrix[eventID])):
                    opt_log_number += 1
                    operational_logs.append(eventID)
                else:
                    ob_matrix.append([eventID] + vicinity_matrix[eventID])

        # 记录观察矩阵
        np.savetxt('../data/matrix.sample', np.asarray((ob_matrix)), fmt='%s')
        print("There are {} templates, {} of them are operational logs. \n"
              "these operational logs are event {}".format(noraml_log_number, opt_log_number, operational_logs)
              )

        # todo tinkle: cluster step
        return list(filter(lambda x: x[0] not in operational_logs, time_series))

    @Timer
    def time_weighted_cfg_mining(self, time_series):
        '''
        控制流挖掘
        :param time_series:
        :return:
        '''
        # step 1: FS group computation 挖掘继承事件
        # construct successor group
        FS_group = collections.defaultdict(list)
        event_count = collections.defaultdict(int)

        length = len(time_series)
        start = 0
        while start < length - 1:
            pos = start + 1
            # 寻找时间窗口上的最后一个点
            while pos < length and (time_series[pos][1] - time_series[start][1]) < self.time_period:
                pos += 1
            cur_event = time_series[start][0]
            cur_time = time_series[start][1]
            # 计算时滞
            series = sorted(list(map(lambda x: (x[0], x[1] - cur_time), time_series[start + 1: pos])),
                            key=lambda x: x[0])
            #  去除世家窗口内冗余项  这里使用最近的那个事件
            unique_series = [series[i] for i in range(len(series))
                             if series[i][0] != cur_event and
                             (i == 0 or (i > 0 and series[i][0] != series[i-1][0]))]

            FS_group[cur_event] += unique_series
            event_count[cur_event] += 1
            # todo: need consider how to strip window
            start += 1

        # 过滤偶然出现的事件
        for event in FS_group:
            group = list(map(lambda x:x[0], FS_group[event]))
            unique_group = list(set(group))
            unique_group = list(filter(lambda x: group.count(x) / event_count[event] > self.FS_threshold,
                                       unique_group))
            FS_group[event] = list(filter(lambda x: x[0] in unique_group, FS_group[event]))

        # todo Tinkle: Verify sub-structure

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

if __name__ == '__main__':
    # df.time_stamp = df.time_stamp.map(lambda x:datetime_to_timestamp(x))
    # df = df.sort_values(by=['time_stamp'])
    # df.to_csv('../message.csv', index = None)

    # 1. 读取数据 格式如下
    # ===========================================================
    # event(事件id) | instance_name(实例名) | time_stamp(时间戳)
    # ===========================================================
    # 54,da5bf2a5-6af4-4c06-88b1-61b83fb2f9cf,1504589505
    # 117,da5bf2a5-6af4-4c06-88b1-61b83fb2f9cf,1504590497
    # 288,83d92ad3-b83f-43c0-962b-ed79b153236a,1504627040
    # ====================================================
    file = '../data/message.csv'
    df = pd.read_csv(file)
    time_series = []
    id_max = 0
    for idx, row in df.iterrows():
        id_max = max(id_max, row.event)
        time_series.append((row.event, row.time_stamp))

    # 过滤操作日志
    LSGraph = LogSed(vicinity_window=10, vicinity_threshold=100, max_event=id_max)
    normal_series = LSGraph.filter_operational_logs(time_series=time_series)
    # print(normal_series)

    # 挖掘控制流图
    control_flow_graph, successor_map = LSGraph.time_weighted_cfg_mining(normal_series)
    # 生成事物流图
    transaction_flow_graph = LSGraph.determine_transaction_flow(successor_map)
    # 可视化图构建
    visualize_logsed_gvfile(control_flow_graph, transaction_flow_graph, path="../data/graphviz-logsed.gv")
