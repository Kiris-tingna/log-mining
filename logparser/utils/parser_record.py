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
    final_templates = []
    if parser_name == 'Spell':
        for item in parser.signature_map.values():
            final_templates.append((' '.join(item.signature), item.log_ids))

    elif parser_name == 'Draga':
        periodic_output_nodes = []
        for current_output_node in parser.Outputs:
            if current_output_node.active:
                periodic_output_nodes.append(current_output_node)
        # 合并template输出
        for log_cluster in parser.LogClus:
            # it is possible that several logClusts point to the same outcell, so we present
            # all possible templates separated by '\t---\t'
            current_template = ' '.join(log_cluster.log_template) + '\n'
            log_cluster.out_cell.output_templates = log_cluster.out_cell.output_templates + current_template
            # print(log_cluster.out_cell.output_templates)
        for idx, output_node in enumerate(periodic_output_nodes):
            # reporter.write(str(idx + 1) + '\t' + output_node.output_templates + '\n')
            final_templates.append((output_node.output_templates.strip('\n'), output_node.log_ids))
            # print(idx+1, output_node.output_templates)

    elif parser_name == 'Drain':
        for item in parser.LogClusterMap:
            final_templates.append((' '.join(item.log_template), item.log_ids))

    elif parser_name == 'BasicSignatureGren' or parser_name == 'BasicSignatureGrenGini':
        ans = collections.defaultdict(list)
        for pos in parser.bucket:
            for key in parser.bucket[pos]:
                for cluster in parser.bucket[pos][key]:
                    ans[' '.join(cluster.log_template)] += cluster.log_ids

        for sid, signature in enumerate(ans):
            final_templates.append((signature, ans[signature]))
    else:
        raise TypeError('Must give correct parser')

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
