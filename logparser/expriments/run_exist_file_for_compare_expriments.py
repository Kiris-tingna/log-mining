#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/11/17 17:26
 @Author  : Kiristingna
 @File    : run_exist_file_for_compare_expriments.py
 @Software: PyCharm
"""
import sys, os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)
sys.path.append(PROJECT_DIR)

from logparser.parser import *
from logparser.utils import *
import gc, re
import pandas as pd


def thread_task(template, event_id, log_ids):
    '''
    每个进程负责在df上进行event id 的替换
    :param template:
    :param event_id:
    :param example:
    :return:
    '''
    example = None
    for line in log_ids:
        id = line[0]
        df.at[id, 'template'] = template
        df.at[id, 'event_id'] = event_id
        if not example:
            example = df.loc[id, 'log_txt']
        df.at[id, 'example'] = example
    return


if __name__ == '__main__':
    # ================ Ex1. 用于离线分析和比较各个parser的效果 ===================
    # generally idea:
    #       将日志解析器的前缀树可视化、构建workflow等
    # experiment record:
    #   1. spell的树上有路径偏移的情况产生
    #   2. drain 能识别异常日志模式（突增的日志长度）， 但是drain算法被noise影响的问题比较严重 （有大量重复的日志signature 在不同的bucket上）
    #   3. Spell 的事件个数会比其他算法多（可能这是Spell 本省的特性）
    # Solutions:
    #   1. ADD 加入日志对于一些特殊规则的分割
    #   2. 这个问题在drage里已经被修正了 原理就是加入输出层进行合并 (add 2018/10/22 这个似乎不是drain的问题)
    #   3. Spell 的事件会分的更细
    # =========================================================================

    '''
     ---------------- step 1 : construct a parser with domain knowledge ---------------
     1. 使用的 日志 为中兴提供的日志预处理文件 格式为
     time,deploy_id,service,component,event_id,level,ip,log_txt
     2018-10-23 09:44:02.747,59442,cf-pdman,cf-pdman,1,INFO,192.169.7.98,"2018-10-23 09:44:02.747 INFO  cloudframe.pdman.cmd.worker Configuration: 

    '''
    spell_parser = Spell(reg_file='../config/config.paas.txt', threshold=0.7)
    # drain_parser = Drain(reg_file='../config/config.paas.txt', max_child=10, max_depth=4, min_similarity=0.5)
    # draga_parser = Draga(reg_file='../config/config.paas.txt', max_child=10, merge_threshold=0.9)
    # bsg_parser = BSG(reg_file='../config/config.paas.txt', global_st=0.7)
    # bsgi_parser = BSGI(reg_file='../config/config.paas.txt', global_st=0.7)

    '''
     -------------------- step 2 : train data line step by line  -------------------
     Example: 以下用法适用于dataframe的部分
    '''

    # file = '../../../event_type_ansible.csv'
    file = '../data/cc.csv'
    RULE_LIST = [
        '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d{3} \d+',
        '\sINFO|\sWARNING|\sWARN|\sCRIT|\sDEBUG|\sTRACE|\sFATAL|\sERROR|\swarning|\sinfo',
        '(req-)?[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12}'
    ]

    time_stamp_1 = re.compile("\d{4} \d{2}:\d{2}:\d{2}.\d{6}")
    time_stamp_2 = re.compile("\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}")
    time_stamp_3 = re.compile("\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d{3}")
    time_stamp_4 = re.compile("\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}")
    time_stamp_5 = re.compile("\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}")
    time_stamp_6 = re.compile("\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")
    time_stamp_7 = re.compile("\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},?")

    time_stamps = [
        time_stamp_1, time_stamp_2,
        time_stamp_3, time_stamp_4,
        time_stamp_5, time_stamp_6,
        time_stamp_7
    ]

    df = pd.read_csv(file)
    start = strict_time()

    for idx, row in df.iterrows():
        message = row.log_txt
        for p in RULE_LIST:
            message = re.sub(p, '', message)

        for p in time_stamps:
            message = re.sub(p, '', message)

        spell_parser.online_train(message, idx, row.time)
        # drain_parser.online_train(message, row.log_id, row.time)
        # draga_parser.online_train(message, row.log_id, row.time)
        # bsg_parser.online_train(message, row.log_id, row.time)
        # bsgi_parser.online_train(message, row.log_id, row.time)

    end = strict_time()
    print(end - start)

    # visualize_spell_gvfile(spell_parser, path='../data/Ex3/graphviz_spell_zte_original.gv')

    '''
    ----------------------------- step3-2. 记录并解析结果转为csv文件存储 ------------------------------------
     Example: 
    '''
    parser_name = spell_parser.__class__.__name__

    start = strict_time()
    final_templates = []
    for item in spell_parser.signature_map.values():
        final_templates.append((' '.join(item.signature), item.sig_id, item.log_ids))
    end = strict_time()
    print(end - start)

    #  ----------------------------------- Need Optimization Start ---------------------------------
    start = strict_time()

    td = pd.DataFrame(final_templates, columns=['template', 'event_id', 'log_ids'])
    td.apply(lambda x: thread_task(x['template'], x['event_id'], x['log_ids']), axis=1)

    end = strict_time()
    print(end - start)
    #  ----------------------------------- Need Optimization End ---------------------------------

    start = strict_time()
    df.drop(['template', 'example'], axis=1).to_csv('%s/%s.csv' % ('../../loggraph/data', parser_name), index=None)
    # event_id,template,level,example
    df[['event_id', 'template', 'level', 'example']].drop_duplicates().to_csv(
        '%s/%s_template.csv' % ('../../loggraph/data', parser_name), index=None)
    end = strict_time()
    print(end - start)
