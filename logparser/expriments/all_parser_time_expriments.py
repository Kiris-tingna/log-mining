#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/11/9 10:19
 @Author  : Kiristingna
 @File    : offline_parser_expriments.py
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


spell_parser = Spell(reg_file='../config/config.iaas.txt', threshold=0.7)
spell_parser2 = Spell(reg_file='../config/config.iaas.txt', threshold=0.95)
drain_parser = Drain(reg_file='../config/config.iaas.txt', max_child=10, max_depth=8, min_similarity=0.7)
draga_parser = Draga(reg_file='../config/config.iaas.txt', max_child=10, merge_threshold=0.9)
bsg_parser = BSG(reg_file='../config/config.iaas.txt', global_st=0.7)
bsgi_parser = BSGI(reg_file='../config/config.iaas.txt', global_st=0.7)
bsgi_parser2 = BSGI(reg_file='../config/config.iaas.txt', global_st=0.95)

file = '../data/iaas_filtered.csv'

df = pd.read_csv(file)
times = {'spell': 0, 'spell2': 0, 'drain': 0, 'draga': 0, 'bsg': 0, 'bsg-gini': 0, 'bsg-gini2': 0}
templates = {'spell': 0, 'spell2': 0, 'drain': 0, 'draga': 0, 'bsg': 0, 'bsg-gini': 0, 'bsg-gini2': 0}

for idx, row in df.iterrows():
    start = strict_time()
    spell_parser.online_train(row.message, row.log_id, row.time)
    end = strict_time()
    times['spell'] += end - start

    start = strict_time()
    spell_parser2.online_train(row.message, row.log_id, row.time)
    end = strict_time()
    times['spell2'] += end - start

    start = strict_time()
    drain_parser.online_train(row.message, row.log_id, row.time)
    end = strict_time()
    times['drain'] += end - start

    start = strict_time()
    draga_parser.online_train(row.message, row.log_id, row.time)
    end = strict_time()
    times['draga'] += end - start

    start = strict_time()
    bsg_parser.online_train(row.message, row.log_id, row.time)
    end = strict_time()
    times['bsg'] += end - start

    start = strict_time()
    bsgi_parser.online_train(row.message, row.log_id, row.time)
    end = strict_time()
    times['bsg-gini'] += end - start

    start = strict_time()
    bsgi_parser2.online_train(row.message, row.log_id, row.time)
    end = strict_time()
    times['bsg-gini2'] += end - start

templates['spell'] = len(spell_parser.signature_map)
templates['spell2'] = len(spell_parser2.signature_map)
templates['drain'] = len(drain_parser.LogClusterMap)
templates['draga'] = draga_parser.get_templates_number()
templates['bsg'] = bsg_parser.get_templates_number()
templates['bsg-gini'] = bsgi_parser.get_templates_number()
templates['bsg-gini2'] = bsgi_parser2.get_templates_number()

for k, v in times.items():
    print(k, v, templates[k])
