#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/11/14 10:39
 @Author  : Kiristingna
 @File    : construct_tflow_by_logsed.py
 @Software: PyCharm
"""
import sys, os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)
sys.path.append(PROJECT_DIR)

import pandas as pd
from loggraph.graph import LogSed
from logparser.utils import visualize_logsed_gvfile

if __name__ == "__main__":
    ''' -----------------Step 1. 确定读取数据 格式如下----------------
    ===========================================================
    event_id(事件id) | instance_name(实例名) | time(时间戳)
    ===========================================================
    54,da5bf2a5-6af4-4c06-88b1-61b83fb2f9cf,1504589505
    117,da5bf2a5-6af4-4c06-88b1-61b83fb2f9cf,1504590497
    288,83d92ad3-b83f-43c0-962b-ed79b153236a,1504627040
    ===========================================================
    '''
    file = '../data/message.csv'
    df = pd.read_csv(file)
    time_series = []
    id_max = 0

    ''' ------------------ Step 2. 构建series --------------------
        time series: [
            (event_1, time_1), ...
            (event_n, time_n)
        ]
    Example: (1417, 1537235360.7220001), 
            (1417, 1537235360.7370002), 
            (1417, 1537235360.7370002), 
            (1417, 1537235360.7420001), 
            (1417, 1537235360.756),
    '''

    for idx, row in df.iterrows():
        id_max = max(id_max, int(row.event_id))
        time_series.append((int(row.event_id), row.time))

    ''' ------------------ Step 3. 过滤操作日志 -------------------- 
    Example:
        There are 1628 templates, 1606 of them are operational logs. 
    '''
    LSGraph = LogSed(time_period=8, vicinity_window=5, vicinity_threshold=1000, FS_threshold=0.85, outlier_epsilon=4,
                     max_event=id_max)
    normal_series = LSGraph.filter_operational_logs(time_series=time_series)

    ''' ------------------ Step 4. 挖掘控制流图 包括节点和边/ 生成事物流图, 主要是确定事务流的边界 --------
    '''
    control_flow_graph, successor_map = LSGraph.time_weighted_cfg_mining(normal_series)
    transaction_flow_graph = LSGraph.determine_transaction_flow(successor_map)

    ''' ------------------ Step 5. 可视化图构建 ----------------------
    '''
    visualize_logsed_gvfile(control_flow_graph, transaction_flow_graph, path="../data/graphviz-logsed.gv")
    # visualize_gv_manually('../data/graphviz-logsed-2018-11-13.gv', render_mode='dot')
