#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/9/18 21:02
 @Author  : Kiristingna
 @File    : graphviz_utils.py
 @Software: PyCharm
"""
try:
    from graphviz import Digraph
    from graphviz import render
except Exception as e:
    print("can't import graphviz")
import datetime


def visualize_logsed_gvfile(control_flow_graph, transaction_flow_graph, path="../graphviz-logsed.gv"):
    '''
    可视化事物流图
    :param control_flow_graph:
    :param transaction_flow_graph: dict value 为 事件i到事件j的转移时间
                                使用 cfg 就是最大的转移时间（时滞 用于异常检测）
                                使用 tfg 就是正态分布的均值转移时间
    :param path:
    :return:
    '''
    gv_object = Digraph(strict=True, comment='The visualization of prefix tree ' + str(datetime.date.today()))
    length = len(control_flow_graph)
    visited = [False for _ in range(length)]
    nodes = 0
    edges = 0
    for i in range(length):
        for j in range(length):
            if transaction_flow_graph[i][j] > -1:
                # 编号逻辑
                if not visited[i]:
                    nodes +=1
                    visited[i] = True
                    gv_object.node('E_'+str(i), shape='circle')

                if not visited[j]:
                    nodes +=1
                    visited[j] = True
                    gv_object.node('E_'+str(j), shape='circle')
                # 连接两个点形成一条边
                gv_object.edge('E_'+str(i), 'E_'+str(j), label=str(round(control_flow_graph[i][j], 3)))
                edges += 1
    print('There are {} edges with {} nodes'.format(edges, nodes))
    ext = '.gv'
    if ext in path:
        path = path[:-3] + "-" + str(datetime.date.today()) + ext

    with open(path, 'w', encoding='utf-8') as f:
        f.write(gv_object.source)
    # 效果综合来看  circo 和  sfdp 这两个布局比较好
    render(engine='sfdp', format='pdf', filepath=path, quiet=False)
    return path


def visualize_bsg_gvfile(parser, path='../data/graphviz-bsg.gv'):
    '''
    产生bsg 算法树的gv描述文件 并可视化
    :param parser:
    :param path: 描述文件产生的位置
    :return:
    '''
    if not parser:
        raise ValueError("Must give a parser object")

    tree_gv_object = Digraph(strict=True, comment='The visualization of bsg '+ str(datetime.date.today()))
    tree_gv_object.node('N_0', label="root", shape='circle')

    offset2map = {0:'start', 1:'end', 2:'arbitrarily'}
    cur_index = 1
    for pos in parser.bucket:
        length = pos // 3
        offset = pos % 3
        keyValue_index = cur_index
        cur_index += 1
        tree_gv_object.node('N_'+str(keyValue_index), shape = "box")
        tree_gv_object.edge('N_0', 'N_'+str(keyValue_index), label= str(length) + '_' + offset2map[offset])
        for keyvalue in parser.bucket[pos]:
            tree_gv_object.node('N_' + str(cur_index), shape="circle")
            tree_gv_object.edge('N_' + str(keyValue_index), 'N_' + str(cur_index), \
                                label=keyvalue)
            kv = cur_index
            cur_index += 1
            for logcluster in parser.bucket[pos][keyvalue]:
                last = kv
                for token in logcluster.log_template:
                    tree_gv_object.node('N_' + str(cur_index), shape="circle")
                    tree_gv_object.edge('N_'+str(last), 'N_' + str(cur_index), label=token)
                    last = cur_index
                    cur_index += 1

    ext = '.gv'
    if ext in path:
        path = path[:-3] + "-" + str(datetime.date.today()) + ext

    with open(path, 'w', encoding='utf-8') as f:
        f.write(tree_gv_object.source)

    tree_gv_object.render(path, view=True)
    return path


def visualize_spell_gvfile(prefix_tree, path="../data/graphviz-spell.gv"):
    '''
    产生spell 算法树的gv描述文件 并可视化
    :type path: 描述文件产生的位置
    :type prefix_tree: 必须是前缀树自类的对象
    :return:
    '''
    if not prefix_tree:
        raise ValueError("Must give a prefix tree object")

    tree_gv_object = Digraph(strict=True, comment='The visualization of prefix tree '+ str(datetime.date.today()))
    tree_gv_object.node('N_0', label="root", shape='circle')

    def dfs_traverse(node, dot, parent_index, current_index):
        if not node:
            return current_index

        if node.children:
            for _word, _child in node.children.items():
                current_index += 1
                dot.node('N_'+str(current_index), label="", shape='circle')
                dot.edge('N_'+str(parent_index), 'N_'+str(current_index), label=str(_word))
                current_index = dfs_traverse(_child, dot, current_index, current_index)
        else:
            return current_index

        return current_index

    dfs_traverse(prefix_tree.root, tree_gv_object, 0, 0)

    ext = '.gv'
    if ext in path:
        path = path[:-3] + "-" + str(datetime.date.today()) + ext

    with open(path, 'w', encoding='utf-8') as f:
        f.write(tree_gv_object.source)

    tree_gv_object.render(path, view=True)
    return path


def visualize_drain_gvfile(prefix_tree, path="../data/graphviz-drain.gv"):
    '''
    产生 drain 算法树的gv描述文件 并可视化
    :type path: 描述文件产生的位置
    :type prefix_tree: 必须是前缀树自类的对象
    :return:
    '''
    if not prefix_tree:
        raise ValueError("Must give a prefix tree object")

    tree_gv_object = Digraph(strict=True, comment='The visualization of prefix tree ' + str(datetime.date.today()))
    tree_gv_object.node('N_0', label="root", shape='circle')

    def dfs_traverse(node, dot, parent_index, current_index):
        if not node:
            return current_index

        if isinstance(node.children, dict):
            for _word, _child in node.children.items():
                current_index += 1
                # print(_word)
                dot.node('N_' + str(current_index), shape='circle')
                dot.edge('N_' + str(parent_index), 'N_' + str(current_index), label=str(_word))
                current_index = dfs_traverse(_child, dot, current_index, current_index)
        else:
            return current_index

        return current_index

    dfs_traverse(prefix_tree.root, tree_gv_object, 0, 0)

    ext = '.gv'
    if ext in path:
        path = path[:-3] + "-" + str(datetime.date.today()) + ext

    with open(path, 'w', encoding='utf-8') as f:
        f.write(tree_gv_object.source)

    tree_gv_object.render(path, view=True)
    return path


def visualize_gv_manually(gv_file, render_mode='dot'):
    '''
    手动生成可视化图
    :param gv_file:
    :param render_mode:
    :return:
    '''

    render(engine=render_mode, format='pdf', filepath=gv_file, quiet=False)
    return
