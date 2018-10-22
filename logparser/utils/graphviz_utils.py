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
except Exception as e:
    print("can't import graphviz")
import datetime
import re


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
                # _word = re.sub(r"\"|\@|\\", '', _word)
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
