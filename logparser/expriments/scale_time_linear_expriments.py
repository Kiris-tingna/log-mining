#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/11/14 15:14
 @Author  : Kiristingna
 @File    : scale_time_linear_expriments.py
 @Software: PyCharm
"""
from logparser.parser import *
from logparser.utils import *
import gc, re
import pandas as pd
from matplotlib import pyplot as plt
import numpy as np
plt.rcParams['font.sans-serif']=['SimHei']

if __name__ == '__main__':
    # spell_parser = Spell(reg_file='../config/config.paas.txt', threshold=0.7)
    # spell_parser2 = Spell(reg_file='../config/config.paas.txt', threshold=0.95)
    # drain_parser = Drain(reg_file='../config/config.paas.txt', max_child=10, max_depth=4, min_similarity=0.5)
    # draga_parser = Draga(reg_file='../config/config.paas.txt', max_child=10, merge_threshold=0.9)
    # bsg_parser = BSG(reg_file='../config/config.paas.txt', global_st=0.7)
    # bsgi_parser = BSGI(reg_file='../config/config.paas.txt', global_st=0.7)
    # bsgi_parser2 = BSGI(reg_file='../config/config.paas.txt', global_st=0.95)

    file = '../../../event_type_ansible.csv'
    # file = '../data/cc.csv'

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

    total = 330000
    df = pd.read_csv(file, nrows=total)
    k = int(total // 105)
    dfs = {0: df[:k],
           1: df[k: 3* k],
           2: df[3*k:6* k],
           3: df[6*k: 10* k],
           4: df[10*k:15* k],
           5: df[15*k:21* k],
           6: df[21*k:28* k],
           7: df[28*k:36* k],
           8: df[36*k:45* k],
           9: df[45*k:55* k],
           10: df[55:k: 66 * k],
           11: df[66:k: 78 * k],
           12: df[78:k: 91 * k],
           13: df[91:k: 105 * k],
        }

    time_spell = {i:0 for i in range(14)}
    time_bsg = {i:0 for i in range(14)}
    time_bsgi = {i:0 for i in range(14)}
    time_draga = {i:0 for i in range(14)}
    time_drain = {i:0 for i in range(14)}

    for i in range(14):
        t_spell, t_bsg, t_bsgi, t_draga, t_drain = 0, 0, 0, 0, 0

        spell_parser = Spell(reg_file='../config/config.paas.txt', threshold=0.7)
        bsg_parser = BSG(reg_file='../config/config.paas.txt', global_st=0.7)
        bsgi_parser = BSGI(reg_file='../config/config.paas.txt', global_st=0.7)
        drain_parser = Drain(reg_file='../config/config.paas.txt', max_child=10, max_depth=4, min_similarity=0.6)
        draga_parser = Draga(reg_file='../config/config.paas.txt', max_child=10, merge_threshold=0.9)

        for idx, row in dfs[i].iterrows():
            message = row.log_txt
            for p in RULE_LIST:
                message = re.sub(p, '', message)

            for p in time_stamps:
                message = re.sub(p, '', message)

            start = strict_time()
            spell_parser.online_train(message, idx, row.time)
            end = strict_time()
            t_spell += end - start

            start = strict_time()
            bsg_parser.online_train(message, idx, row.time)
            end = strict_time()
            t_bsg += end - start

            start = strict_time()
            bsgi_parser.online_train(message, idx, row.time)
            end = strict_time()
            t_bsgi += end - start

            start = strict_time()
            draga_parser.online_train(message, idx, row.time)
            end = strict_time()
            t_draga += end - start

            start = strict_time()
            drain_parser.online_train(message, idx, row.time)
            end = strict_time()
            t_drain += end - start

        time_spell[i] = t_spell
        time_bsg[i] = t_bsg
        time_bsgi[i] = t_bsgi
        time_draga[i] = t_draga
        time_drain[i] = t_drain

        del bsgi_parser
        del spell_parser
        del bsg_parser
        del draga_parser
        del drain_parser

    x = np.asarray(list(time_spell.keys()))
    y_spell = np.asarray(list(time_spell.values()))
    y_bsg = np.asarray(list(time_bsg.values()))
    y_bsgi = np.asarray(list(time_bsgi.values()))
    y_draga = np.asarray(list(time_draga.values()))
    y_drain = np.asarray(list(time_drain.values()))

    ax = plt.subplot(1, 1, 1)

    ax.set_xlabel('数据量/条')
    ax.set_ylabel('耗时/秒')
    ax.spines['right'].set_color('none')
    ax.spines['top'].set_color('none')

    p1 = ax.plot(x, y_spell, 'rX:', label="spell(0.7)")
    p2 = ax.plot(x, y_bsg, 'bs-', label="bsg(0.7)")
    p3 = ax.plot(x, y_bsgi, 'g^-', label="bsgi(0.7)")
    p4 = ax.plot(x, y_draga, 'yd-', label="draga")
    p5 = ax.plot(x, y_drain, 'ko-', label="drain")

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], loc='upper left')

    ax.set_xticklabels([str(i* k) for i in range(1, 15)])
    ax.grid(True)
    plt.show()
