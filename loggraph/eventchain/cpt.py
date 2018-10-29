#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/10/27 22:37
 @Author  : Kiristingna
 @File    : cpt.py
 @Software: PyCharm
"""
import TreePredictor


class CompactPredictionTree(object):
    '''
    @author:
    @paper:

    **************************************************
    序列紧凑预测树

    原理: 倒排索引 + 查找表 + 前缀树

    '''

    # A set of all unique items in the entire data file
    event_mapping = None  # 也称为事件的字母表
    # Root node of the Prediction Tree
    tree_root = None
    # Inverted Index dictionary, where key : unique item, value : set of sequences containing this item
    invert_index = None  # 倒排索引
    # A Lookup table dictionary, where key : id of a sequence(row), value: leaf node of a Prediction Tree
    lookup_table = None  # 查找表

    def __init__(self):
        self.event_mapping = set()
        self.tree_root = TreePredictor()
        self.invert_index = {}
        self.lookup_table = {}

    def train(self, train):
        """
        根据预测数据构建预测树 的树结构

        This functions populates the Prediction Tree, Inverted Index and LookUp Table for the algorithm.
        Input: The list of list training data
            [[1, 4, 5, 5]
            [2, 3, 4 , 5]
            ...]
        Output : Boolean True
        """
        current_node = self.root

        for seq_id, seq_row in enumerate(train):
            # 对序列片段构建前缀树
            for element in seq_row:
                # 没有改孩子节点就生成该孩子节点
                if not current_node.hasChild(element):
                    current_node.addChild(element)
                    current_node = current_node.getChild(element)
                # 顺着树查找下去
                else:
                    current_node = current_node.getChild(element)

                # 将该元素（事件）的片段序号 添加到倒排索引 invert_index 上去
                # 表示该元素 在 序列id 中出现过
                # 倒排索引： {事件 -> 片段序号}
                if not self.invert_index.get(element):
                    self.invert_index[element] = set()

                self.invert_index[element].add(seq_id)
                # 将该事件加入事件表上
                self.event_mapping.add(element)

            # 到这里 current_node 就是前缀树上的根节点了
            # 查找表： {片段序号 -> 树上的根节点}
            self.lookup_table[seq_id] = current_node
            # 重置 节点指针
            current_node = self.root

        return True

    def predict(self, train, test, k, n=1):
        """
        Here target is the test dataset in the form of list of list,
        k is the number of last elements that will be used to find similar sequences and,
        n is the number of predictions required.
        Input: training list of list, target list of list, k,n
        Output: max n predictions for each sequence
        """

        predictions = []

        for each_target in tqdm(test):
            each_target = each_target[-k:]

            intersection = set(range(0,len(train)))

            for element in each_target:
                if self.invert_index.get(element) is None:
                    continue
                intersection = intersection & self.invert_index.get(element)

            similar_sequences = []

            for element in intersection:
                current_node = self.lookup_table.get(element)
                tmp = []
                while current_node.Item is not None:
                    tmp.append(current_node.Item)
                    current_node = current_node.Parent
                similar_sequences.append(tmp)

            for sequence in similar_sequences:
                sequence.reverse()

            count_table = {}

            for sequence in similar_sequences:
                try:
                    index = next(i for i,v in zip(range(len(sequence)-1, 0, -1), reversed(sequence)) if v == each_target[-1])
                except:
                    index = None
                if index is not None:
                    count = 1
                    for element in sequence[index+1:]:
                        if element in each_target:
                            continue

                        count_table = self.score(count_table,element,len(each_target),len(each_target),len(similar_sequences),count)
                        count+=1

            pred = self.get_n_largest(count_table,n)
            predictions.append(pred)

        return predictions

    def get_n_largest(self, dictionary, n):
        """
        A small utility to obtain top n keys of a Dictionary based on their values.
        """
        largest = sorted(dictionary.items(), key=lambda t: t[1], reverse=True)[:n]
        return [key for key, _ in largest]

    def score(self, count_table, key, length, target_size, number_of_similar_sequences, number_items_counttable):
        """
        This function is the main workhorse and calculates the score to be populated against an item. Items are predicted
        using this score.
        Output: Returns a count_table dictionary which stores the score against items. This count_table is specific for a
        particular row or a sequence and therefore re-calculated at each prediction.
        """

        weight_level = 1 / number_of_similar_sequences
        weight_distance = 1 / number_items_counttable
        score = 1 + weight_level + weight_distance * 0.001

        if count_table.get(key) is None:
            count_table[key] = score
        else:
            count_table[key] = score * count_table.get(key)

        return count_table
