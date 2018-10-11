#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/10/11 10:30
 @Author  : Kiristingna
 @File    : draga.py
 @Software: PyCharm
"""
from logparser.parser.tree_parser import TreeParser, TreeParserNode
from logparser.utils import Timer
import gc, re
import math


class LogClusterObject:
    cluster_id = 1

    #  注意 new的时候会自增 这个策略在并行是 可能存在问题！
    def __init__(self, log_template='', similarity_threhold=0.1, out_cell=None):
        self.log_template = log_template
        self.updateCount = 0
        self.similarity_threhold = similarity_threhold
        self.base = -1
        self.init_st = -1
        self.out_cell = out_cell

        self.cluster_id = LogClusterObject.cluster_id
        LogClusterObject.cluster_id += 1

class DragaParserNode(TreeParserNode):
    '''
    node for length layer and token layer
    '''
    def __init__(self, digit_or_token):
        self.children = {}
        # digit_or_token 对于数字是 '*' 对于token 是 单个word
        self.digit_or_token = digit_or_token

class DragaOutputNode(TreeParserNode):
    '''
    node for output layer
    '''
    def __init__(self, log_ids=[]):
        self.log_ids = log_ids
        # 最终这个节点输出的日志模板
        self.output_templates = ''
        self.active = True
        self.parent_layer = []

class Draga(TreeParser):
    '''
    @author: Pinjia He
    @paper: A Directed Acyclic Graph Approach to Online Log Parsing

    *********************************************
    DRAGA 解析算法简述
    这个算法是 He 的 Drain 算法的改进版

    1）日志预处理
    2）整体的来说  讲处理过程分为三层 第一层长度层也叫length layer 日志每来一条都根据长度将日志的划分到相应子树上 如果没有对应长度就创建
    3）接下来进入token 层 token层主要存放的是日志的第一个词和最后一个词 以及 *通配符 这一点主要用于快速匹配 如果没有的就创建新的token层节点
        另外token 层如果超过最大孩子的限制时 将日志归入* 下查找
    4）将 cluster 结构放入 所在查找位置叶节点 这个叶节点下可能有很多cluser结构体
    5）查找的时候先根据首尾字串进行匹配 如果找不到就去* 下匹配 到达叶节点就在所有结构体找大于阈值且最相似的那个cluster结构体 如果没有查找到就新建一个输出层
    6）

    ============ threshold is updated dynamically ============
    min_similarity = min{1, min_similarity_init + 0.5 × log_base(yeta + 1)}
    base = max{2, digLen + 1}
    where yeta is is the accumulated number of tokens that have been replaced by wildcards when updating the log events
    yeta get higher indicates the more variables found, and the more difficult for log message to get accepted to a log group.
    '''
    REPL = '*'  # 通配符 wildcards

    # 特殊字符
    SPECIAL_CHARS = set(
        "#$&'*+,/<=>@^_`|~)"
    )
    SPECIAL_CHARS_IN_WORD = '^[\w]+[#$&\'*+,\/<=>@^_`|~.]+$'

    # 第二层 token 层的 key 预设字串
    FIRST_TOKEN_KEY = '00_Drain_'
    LAST_TOKEN_KEY = '-1_Drain_'

    def __init__(self, reg_file):
        self.max_child =

        self.root =
        self.mergethredhold =


        # 缓存的指针 加速查找
        self.pointer =  dict()
        super(Draga, self).__init__(reg_file)

        # 全局列表
        self.LogClus = []
        self.Outputs = []

    @Timer
    def _online_train(self, log, id):
        return self.online_train(log=log, id=id)

    def online_train(self, log, id):
        '''
        处理某一条日志的插入的逻辑
        :param log:
        :param id:
        :return:
        '''
        # 从字符串到一个list 预处理过程
        filtered_log = self.pre_process_single(log)
        log_length = len(filtered_log)
        # 删除指定的列 （这里需要注意一下 如果该列字段下没有值 也就是日志产生了噪声 这样做会把产生偏移 最好用字段名对应起来）
        # self.filter_column(log) # todo: 暂时没做

        matched_cluster = self.lookup(filtered_log)
        # Todo:::::::::::::::::::::::::::::::::::

        # 没有找到合适的叶节点
        if not matched_cluster:
            # 新建输出层
            output_layer_node = DragaOutputNode(log_ids=[id])
            # 插入前缀树 LogClusterObject
            new_cluster = LogClusterObject(log_template=filtered_log, out_cell=output_layer_node)
            # 同一个输出节点可能由不同的叶节点汇集而成
            output_layer_node.parent_layer.append(new_cluster)

            # the initial value of st is 0.5 times the percentage of non-digit tokens in the log message
            number_of_parameters = 0
            for token in filtered_log:
                if self.hasNumbers(token):
                    number_of_parameters += 1

            # "similarity_threhold" is the similarity threshold used by the similarity layer
            # 给 新的集合一个初始的相似阈值
            new_cluster.similarity_threhold = 0.5 * (log_length - number_of_parameters) / float(log_length)
            new_cluster.init_st = new_cluster.similarity_threhold

            # 参数个数被合并得越来越多的时候, 这个日志组趋向于生成模板
            new_cluster.base = max(2, number_of_parameters + 1)  # base 是更新时的对数底数

            # 全局的统计
            self.LogClus.append(new_cluster)
            self.Outputs.append(output_layer_node)

            # 插入前缀树
            self.insert(new_cluster)
            # 更新缓存策略
            self.pointer[log_length] = new_cluster

        # successfully match an existing cluster, add the new log message to the existing cluster
        else:
            new_template, number_updated_tokens = self.marge_template(filtered_log, matched_cluster.log_template)
            matched_cluster.out_cell.log_ids.append(id)

            if ' '.join(new_template) != ' '.join(matched_cluster.log_template):
                matched_cluster.log_template = new_template

                # the update of updateCount
                matched_cluster.updateCount += number_updated_tokens
                matched_cluster.similarity_threhold = min(
                    1, matched_cluster.init_st + 0.5 * math.log(matched_cluster.updateCount + 1, matched_cluster.base)
                )

                # if the merge mechanism is used, them merge the nodes
                if self.mergethredhold < 1:
                    self.adjustOutputCell(matched_cluster, self.LogClus)



# Check if there is number
    def has_numbers(self, s):
        return any(c.isdigit() for c in s)

    # Check if there is special character
    def has_special(self, s):
        return any(c in self.SPECIAL_CHARS for c in s)

    def has_special_tail(self, s):
        '''
        检查单词或者sequence中是否存在特殊字符
        :param s:
        :return:
        '''
        # CASE1 : ....word1 special_char word2 ....
        if not self.has_special(s):
            return False
        # CASE2 : word1(char123+special_char) ...
        if re.match(self.SPECIAL_CHARS_IN_WORD, s):
            return False
        return True

    def lookup(self, log_sequence):
        '''
        在前缀树的查找过程 （改进： 带了缓存指针）
        :param log_sequence:
        :return:
        '''
        log_cluster = None

        n = len(log_sequence)
        # 第一层长度的匹配
        if n not in self.root.children:
            return log_cluster  # 当前长度的日志不存在

        # 缓存指针：if the pointer exist, compare the pointer and the new log first
        log_cluster_cached = self.pointer[n]

        #  ---------------------  缓存指针 直接计算部分 速度优势明显 -------------------------
        # if first token or last token matches with the key in the tree, them calculate similarity; otherwise, skip
        if (
                log_cluster_cached.log_template[0] == log_sequence[0]
                and not self.has_numbers(log_sequence[0])
                and not self.has_special(log_sequence[0])  # 第一个满足特征 首词相同并且不是数字和不包含特殊字符
            ) or \
            (
                log_cluster_cached.log_template[-1] == log_sequence[-1]
                and not self.has_numbers(log_sequence[-1])
                and not self.has_special(log_sequence[-1]) # 第二个满足特征 尾词相同并且不是数字和不包含特殊字符
            ) or \
            (  # 第三个满足特征 以通配符涵盖起始和结束的
                log_cluster_cached.log_template[0] == '*' and log_cluster_cached.log_template[-1] == '*'
            ):
            # 计算当前日志和缓存的模板日志的相似度 若大于阈值则返回缓存的cluster
            current_similarity, current_parameters = self.pattern_dist(log_cluster_cached.log_template, log_sequence)
            if current_similarity >= log_cluster_cached.similarity_threhold:
                log_cluster = log_cluster_cached
                return log_cluster
        #  --------------------- -------------------------------- -------------------------

        prefix_tree_parent = self.root.children[n]  # 前缀树上的根节点 第一层
        first_token = log_sequence[0]
        last_token = log_sequence[-1]

        token_first_key = self.FIRST_TOKEN_KEY + first_token
        token_last_key = self.LAST_TOKEN_KEY + last_token

        # 根据这两个key 在前缀树上查找
        token_layer_node = None
        if token_first_key in prefix_tree_parent.children:
            token_layer_node = prefix_tree_parent.children[token_first_key]
        elif token_last_key in prefix_tree_parent.children:
            token_layer_node = prefix_tree_parent.children[token_first_key]
        # 都没有就是 * 下查找 （这里也是相当于分情况查找策略符合 构建时使用的快速策略）
        elif self.has_numbers(first_token) and self.has_numbers(last_token) and '*' in prefix_tree_parent.children:
            token_layer_node = prefix_tree_parent.children['*']
        else:
            # 其实就是没有查找到 返回None
            return None

        # 查找到了叶节点
        log_cluster_group = token_layer_node.children
        # 快速查找在组中的最符合的某一个结构体
        log_cluster = self.fast_match(log_cluster_group, log_sequence)

        # update the pointer 更新缓存指针 这一步很重要 否则快速策略不会奏效
        if log_cluster is not None:
            self.pointer[n] = log_cluster

        return log_cluster


    def insert(self, log_cluster):
        '''
        在树上插入日志的过程
        :param logClust:
        :return:
        '''
        # 当前日志的长度
        n = len(log_cluster.log_template)

        # ------------ Stage 1. find or insert length node ---------------
        # first layer node 比较特殊 是匹配的开始比较点
        # 这一层是分桶层 依据长度查找长度层下面的节点是哪个
        if n not in self.root.children:
            first_layer_node = DragaParserNode(digit_or_token=n)
            self.root.children[n] = first_layer_node

            # add an others-node for the token layer
            # 这一个比较重要 应为第二层开始每一个节点对应要么是通配符要么是普通字符
            # 通配符要挂在长度节点下面的孩子节点中
            wildcard_node = DragaParserNode(digit_or_token='*')
            first_layer_node.children['*'] = wildcard_node
        else:
            first_layer_node = self.root.children[n]

        # ------------ Stage 2. 找出日志的first token 和last token 并插入树---------------
        first_token = log_cluster.log_template[0]
        last_token = log_cluster.log_template[-1]
        # 生成first token 和 last token 上的key key 加上前缀区别是第一个字符还是最后一个字符
        token_first_key = self.FIRST_TOKEN_KEY + first_token
        token_last_key = self.LAST_TOKEN_KEY + last_token

        # if the index token already exists find it
        #    length_layer_node
        #     |- token1
        #     |- token2
        #     |- ...(token layer node)
        #     |- *
        if token_first_key in first_layer_node.children:
            token_layer_node = first_layer_node.children[token_first_key]
        elif token_last_key in first_layer_node.children:
            token_layer_node = first_layer_node.children[token_last_key]
        # else need to add index token to the tree
        else:
            # **************   比较复杂的插入策略 ****************
            # 如果超过了最大孩子的限制 就把其归入到 * 下
            if len(first_layer_node.children) == self.max_child:
                token_layer_node = first_layer_node.children['*']
            # 否则 用首尾上部位数字的单词作为节点插入
            else:
                # CASE1 : first token has numbers  12 ....
                if self.has_numbers(first_token):
                    # last token has numbers : 12 w w w w w 12
                    if self.has_numbers(last_token):
                        token_layer_node = first_layer_node.children['*']
                    # last token does not have numbers: 12 w w w w
                    else:
                        # 用last token 作为 节点插入
                        token_layer_node = DragaParserNode(digit_or_token=token_last_key)
                        first_layer_node.children[token_last_key] = token_layer_node
                # CASE2 : first token does not have numbers w ...
                else:
                    # 主要是看头部节点是否还含有特殊节点 last token has numbers
                    if self.has_numbers(last_token):
                        token_layer_node = DragaParserNode(digit_or_token=token_first_key)
                        first_layer_node.children[token_first_key] = token_layer_node
                    # last token does not have numbers
                    else:
                        # last token has punctuations
                        if self.has_special(last_token):
                            token_layer_node = DragaParserNode(digit_or_token=token_first_key)
                            first_layer_node.children[token_first_key] = token_layer_node
                        # first token has punctuations, last token does not have punctuations
                        elif self.has_special(first_token):
                            token_layer_node = DragaParserNode(digit_or_token=token_last_key)
                            first_layer_node.children[token_last_key] = token_layer_node
                        # first/last token has punctuations  头尾词都有特殊字符
                        else:
                            token_layer_node = DragaParserNode(digit_or_token=token_first_key)
                            first_layer_node.childD[token_first_key] = token_layer_node

        # ------------ Stage 3. add the cluster to the leave node -----------
        # 需要注意的是一个叶节点下面log_cluster结构体可以有多个
        if len(token_layer_node.children) == 0:
            token_layer_node.children = [log_cluster]
        else:
            token_layer_node.childD.append(log_cluster)

    def pattern_dist(self, seq_1, seq_2):
        '''
        计算两个序列的相似度 （快速）
        :param seq_1:
        :param seq_2:
        :return:
        '''
        similar_tokens = 0  # 相似token的个数
        number_of_parameters = 0  # * 的个数

        for token_1, token_2 in zip(seq_1, seq_2):
            if token_1 == '*':
                number_of_parameters += 1
            elif token_1 == token_2:
                similar_tokens += 1

        number_of_chars = len(seq_1) - number_of_parameters

        # 相似性
        similarity = 0.0

        # 如果全是参数
        if not number_of_chars:
            # word 和 * word1 word2...
            if len(seq_1) == 1 and self.has_numbers(seq_2[0]):
                similarity = 1.0
        # 如果不全是参数
        else:
            # 相似度 = （A 和 B 共有的字符个数） / （A 上面去除参数的长度）
            similarity = float(similar_tokens) / number_of_chars

        return similarity, number_of_parameters

    def fast_match(self, log_cluster_group, log_sequence):
        '''
        快速匹配过程（逐个比较）
        Find the most suitable log cluster in the leaf node, token-wise comparison, used to find the most similar cluster
        :return:
        '''
        max_similarity = -1
        max_parameter = -1
        max_cluster_group = None  # 最相似的那个group组对象

        for log_cluster in log_cluster_group:
            similarity, n_parameter = self.pattern_dist(log_cluster.log_template, log_sequence)
            # 相同相似度的情况下 取参数个数多的
            if similarity > max_similarity or (similarity == max_similarity and n_parameter > max_parameter):
                max_similarity = similarity
                max_parameter = n_parameter
                max_cluster_group = log_cluster
        #  判断相对于之前的版本多了 阈值的判断 这里的阈值已经不再是一个预设的定值了
        if max_cluster_group is not None and max_similarity >= max_cluster_group.similarity_threhold:
            return max_cluster_group
        else:
            return None  # 没有最相似的日志组

    def marge_template(self, seq_1, seq_2):
        '''
        合并签名 template = signature 返回合并之后的签名 和 之中被通配符替换的字符个数
        :param seq_1:
        :param seq_2:
        :return:
        '''
        if not len(seq_1) == len(seq_2):
            raise AssertionError("two sequence must have same length")

        merged_template = []
        combined_tokens = 0
        n = len(seq_1)

        for i in range(n):
            if seq_1[i] == seq_2[i]:
                merged_template.append(seq_1[i])
            else:
                if seq_2[i] != self.REPL:
                    combined_tokens += 1
                merged_template.append(self.REPL)

        return merged_template, combined_tokens

    def adjust



















        # return the lcs in a list
        def LCS(self, seq1, seq2):
            lengths = [[0 for j in range(len(seq2) + 1)] for i in range(len(seq1) + 1)]
            # row 0 and column 0 are initialized to 0 already
            for i in range(len(seq1)):
                for j in range(len(seq2)):
                    if seq1[i] == seq2[j]:
                        lengths[i + 1][j + 1] = lengths[i][j] + 1
                    else:
                        lengths[i + 1][j + 1] = max(lengths[i + 1][j], lengths[i][j + 1])

            # read the substring out from the matrix
            result = []
            lenOfSeq1, lenOfSeq2 = len(seq1), len(seq2)
            while lenOfSeq1 != 0 and lenOfSeq2 != 0:
                if lengths[lenOfSeq1][lenOfSeq2] == lengths[lenOfSeq1 - 1][lenOfSeq2]:
                    lenOfSeq1 -= 1
                elif lengths[lenOfSeq1][lenOfSeq2] == lengths[lenOfSeq1][lenOfSeq2 - 1]:
                    lenOfSeq2 -= 1
                else:
                    assert seq1[lenOfSeq1 - 1] == seq2[lenOfSeq2 - 1]
                    result.insert(0, seq1[lenOfSeq1 - 1])
                    lenOfSeq1 -= 1
                    lenOfSeq2 -= 1
            return result

        def adjustOutputCell(self, logClust, logClustL):

            similarClust = None
            lcs = []
            similarity = -1
            logClustLen = len(logClust.logTemplate)

            for currentLogClust in logClustL:
                currentClustLen = len(currentLogClust.logTemplate)
                if currentClustLen == logClustLen or currentLogClust.outcell == logClust.outcell:
                    continue
                currentlcs = self.LCS(logClust.logTemplate, currentLogClust.logTemplate)
                currentSim = float(len(currentlcs)) / min(logClustLen, currentClustLen)

                if currentSim > similarity or (currentSim == similarity and len(currentlcs) > len(lcs)):
                    similarClust = currentLogClust
                    lcs = currentlcs
                    similarity = currentSim

            if similarClust is not None and similarity > self.para.mt:
                similarClust.outcell.logIDL = similarClust.outcell.logIDL + logClust.outcell.logIDL

                removeOutputCell = logClust.outcell

                for parent in removeOutputCell.parentL:
                    similarClust.outcell.parentL.append(parent)
                    parent.outcell = similarClust.outcell

                removeOutputCell.logIDL = None
                removeOutputCell.active = False