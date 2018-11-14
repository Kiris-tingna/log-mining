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
    # ================ Ex4. 用于将提取过后的时间分类文件重新打事件id的标记 ===================
    # generally idea:
    #       从日志事件结果数据结构中还原笔记录每一条日志的事件id
    # experiment record:
    #   1. 速度太慢
    #   2. 日志在线分类的逻辑需要优化
    # Solutions:
    #   1. pd.loc 改为 pd.at
    #   2. 想法是这样的 现在需要增加接口 对于每一条日志过来 改为每处理一条日志 就输出对应的分类id
    # =========================================================================

    '''
     ---------------- step 1 : construct a parser with domain knowledge ---------------
     1. 使用的 日志 为中兴提供的日志预处理文件 格式为
     time,deploy_id,service,component,event_id,level,ip,log_txt
     2018-10-23 09:44:02.747,59442,cf-pdman,cf-pdman,1,INFO,192.169.7.98,"2018-10-23 09:44:02.747 INFO  cloudframe.pdman.cmd.worker Configuration: 

    '''
    spell_parser = Spell(reg_file='../config/config.paas.txt', threshold=0.7)
    spell_parser2 = Spell(reg_file='../config/config.paas.txt', threshold=0.95)
    drain_parser = Drain(reg_file='../config/config.paas.txt', max_child=10, max_depth=4, min_similarity=0.5)
    draga_parser = Draga(reg_file='../config/config.paas.txt', max_child=10, merge_threshold=0.9)
    bsg_parser = BSG(reg_file='../config/config.paas.txt', global_st=0.7)
    bsgi_parser = BSGI(reg_file='../config/config.paas.txt', global_st=0.7)
    bsgi_parser2 = BSGI(reg_file='../config/config.paas.txt', global_st=0.95)

    '''
     -------------------- step 2 : train data line step by line  -------------------
     Example: 以下用法适用于dataframe的部分
    '''

    file = '../../../event_type_ansible.csv'
    # file = '../data/cc.csv'
    # c_parser = spell_parser
    # c_parser = spell_parser2
    # c_parser = drain_parser
    # c_parser = draga_parser
    # c_parser = bsg_parser
    c_parser = bsgi_parser
    # c_parser = bsgi_parser2

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

        c_parser.online_train(message, idx, row.time)

    end = strict_time()
    print(end - start)

    # visualize_spell_gvfile(spell_parser, path='../data/Ex3/graphviz_spell_zte_original.gv')

    '''
    ----------------------------- step3-2. 记录并解析结果转为csv文件存储 ------------------------------------
     Example: 
    '''

    parser_name = c_parser.__class__.__name__

    start = strict_time()
    final_templates = c_parser.get_final_template(verbose=False)
    end = strict_time()
    print(end - start)

    #  ----------------------------------- Need Optimization Start ---------------------------------
    start = strict_time()
    td = pd.DataFrame(final_templates, columns=['template', 'log_ids'])
    td['event_id'] = pd.Series([i for i in range(len(td))])
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
