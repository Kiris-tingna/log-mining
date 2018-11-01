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
        1. 原始输入 [(635, 1508606072.958) ...]
        2. 以635为起点事件， 找到若干满足一个时间窗口约束的 模式对 [635-> 666, 635-> 1,...] 构建count matrix
        3. 根据统计 算出counter matrix 下的阈值， 用于过滤操作日志（低频）
        4. 得到key event 记录， 并使用 滑动时窗 挖掘继承事件 得到控制流图（控制冗余 ）
        5. 同样利用统计 得到事物的边界 形成 事务流图（适用阈值进行二分搜索 得到最大的那个区间）
    """
    def __init__(self,
                 vicinity_window=3,
                 vicinity_threshold=10,
                 cluster_threshold=0.7,
                 time_period=5,
                 FS_threshold=0.8,
                 transaction_epsilon=0.5,
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
        # ------------------ Step1：count matrix for events ------------------------
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

        # -------------------- Step2：考察每一个事件领域内事件的个数情况 -----------------
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

        # ---------------------- for debug : 记录统计矩阵 ---------------------
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
        # ------------------- step 1: FS group computation 挖掘继承事件 组成列表集 ---------------------
        FS_group = collections.defaultdict(list)
        event_count = collections.defaultdict(int)

        length = len(time_series)
        start = 0
        while start < length - 1:
            pos = start + 1
            # 寻找时间窗口上的最后一个点
            while pos < length and (time_series[pos][1] - time_series[start][1]) < self.time_period:
                pos += 1
            # 当前的窗口的起始时间和起始时间
            cur_event = time_series[start][0]
            cur_time = time_series[start][1]

            # 计算当前窗口后继时间与起始事件之间的时滞 并将其作为 series 对象
            series = sorted(list(map(lambda x: (x[0], x[1] - cur_time), time_series[start + 1: pos])),
                            key=lambda x: x[0])

            # todo: 1. need consider how to strip window

            #  去除series 对象 时间窗口内冗余项 冗余项包括：
            # 1. 窗口起始事件
            # 2. 在series 中第二次出现的相同事（这里使用离起始事件最近的那个事件）
            unique_series = [series[i] for i in range(len(series))
                             if series[i][0] != cur_event and
                             (i == 0 or (i > 0 and series[i][0] != series[i-1][0]))]
            #  拼接当前这个时间之后的总和序列
            FS_group[cur_event].extend(unique_series)
            # 事件在长序列中总共出现的次数
            event_count[cur_event] += 1
            # 滑动窗口
            start += 1

        # --------------------------- step2. 过滤事件集合上偶然出现的事件 ----------------------------
        for event in FS_group:
            group = list(map(lambda x: x[0], FS_group[event]))
            unique_group = list(set(group))
            unique_group = list(filter(lambda x: group.count(x) / event_count[event] > self.FS_threshold,
                                       unique_group))
            FS_group[event] = list(filter(lambda x: x[0] in unique_group, FS_group[event]))

        # todo Tinkle: 2. Verify sub-structure

        # ----------------------------- step 2: Edge time weight computation --------------------------------------
        # cfg : 控制图上的节点对的邻接矩阵
        cfg = [[-1 for _ in range(self.max_event)] for _ in range(self.max_event)]
        time_weight_mapping = dict()
        # event: 指当前起始事件 successor_id: 指当前起始事件开头的窗口内的后继事件
        for event in FS_group:
            if event not in time_weight_mapping:
                time_weight_mapping[event] = collections.defaultdict(list)
            # successor 是每个后继事件 包括事件ID 和 事件的时间time 两个部分
            for successor in FS_group[event]:
                successor_id = successor[0]
                transfer_time = successor[1]
                # item: {事件id:[时间差的有序列表]}
                bisect.insort_left(time_weight_mapping[event][successor_id], transfer_time)

        # 取最大的时间间隔
        for i in range(self.max_event):
            for j in range(self.max_event):
                if i != j and i in time_weight_mapping and len(time_weight_mapping[i][j]):
                    cfg[i][j] = time_weight_mapping[i][j][-1]
        return cfg, time_weight_mapping

    @Timer
    def determine_transaction_flow(self, time_weight_mapping):
        '''
        切分事物流，确定事物的起点和终点
        :param time_weight_mapping:
        :return:
        '''
        # tfg: transaction control graph  事物流图
        tfg = [[-1 for _ in range(self.max_event)] for _ in range(self.max_event)]
        for event in time_weight_mapping:
            for successor in time_weight_mapping[event]:
                time_stamp_count, transaction_time = -1, -1
                # 两个事件 所有的 时间差列表
                times = time_weight_mapping[event][successor]

                for transfer_time in times:
                    # 搜索区间
                    left = bisect.bisect_right(times, transfer_time - self.transaction_epsilon)
                    right = bisect.bisect_left(times, transfer_time + self.transaction_epsilon)
                    # 集中区域作为 最终的 分割事物流的依据
                    if right - left >= time_stamp_count:
                        time_stamp_count = right - left
                        transaction_time = transfer_time
                # 去掉转移时间超过outlier_epsilon的 事件对
                if -1 < transaction_time < self.outlier_epsilon:
                    tfg[event][successor] = transaction_time
        return tfg

if __name__ == '__main__':
    # 1. 读取数据 格式如下
    # ===========================================================
    # event(事件id) | instance_name(实例名) | time_stamp(时间戳)
    # ====================================================
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

    # 挖掘控制流图
    control_flow_graph, successor_map = LSGraph.time_weighted_cfg_mining(normal_series)
    # 生成事物流图
    transaction_flow_graph = LSGraph.determine_transaction_flow(successor_map)
    # 可视化图构建
    visualize_logsed_gvfile(control_flow_graph, transaction_flow_graph, path="../data/graphviz-logsed.gv")
