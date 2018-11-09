#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/11/7 13:40
 @Author  : Kiristingna
 @File    : parser_record.py
 @Software: PyCharm
"""
import pandas as pd
import collections
from .timer_utils import datetime_to_timestamp


def parser_tocsv(parser, path):
    '''
    解析到构建事务流所需的中间结果
    :param parser:
    :param path:
    :return:
    '''
    parser_name = parser.__class__.__name__

    if parser_name not in ['Spell', 'Drain', 'Draga', 'BasicSignatureGren', 'BasicSignatureGrenGini']:
        raise TypeError('Must give correct parser')
    else:
        final_templates = parser.get_final_template()

    data = {'template':[], 'event':[],'log_id':[], 'time_stamp': []}
    for i in range(len(final_templates)):
        template = final_templates[i][0]
        for line in final_templates[i][1]:
            data['template'] += [template]
            data['event'] += [i + 1]
            data['log_id'] += [line[0]]
            data['time_stamp'] += [datetime_to_timestamp(line[1])]
    df = pd.DataFrame(data)
    df[['event', 'template']].drop_duplicates().to_csv('%s/%s_template.csv' % (path, parser_name), index=None)
    del df['template']
    df.sort_index(by=['time_stamp']).to_csv('%s/%s.csv' % (path, parser_name), index=None)
