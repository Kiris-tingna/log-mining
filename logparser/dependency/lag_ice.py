#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/9/21 22:43
 @Author  : Kiristingna
 @File    : lag_ice.py
 @Software: PyCharm
"""
import numpy as np


class LagICE(object):
    '''
    @author:
    @paper:

    lag ice 算法 注意随机子空间采样必须使用较多的点，否则不能很好的估计时滞
    # TODO ice 算法的评估标准
    @key math formula

    '''
    def __init__(self, an, cq, lag_init, max_iteration=1000):
        self.antecedents = np.asarray(an, dtype=np.float32)  # 祖先
        self.consequents = np.asarray(cq, dtype=np.float32)  # reference sequence

        self.len_a = len(self.antecedents)
        self.len_b = len(self.consequents)

        self.lagT = lag_init  # 初始化时滞
        self.max_iteration = max_iteration
        self.which_b_in_consequent = []

    def run(self, an_samples, cq_samples, sample_times, threshold):
        '''
        先运行自采样 估计时滞 然后在进行具体的时滞挖掘
        :param an_samples:
        :param cq_samples:
        :param sample_times:
        :param threshold:
        :return:
        '''
        print("lag before estimat is {}".format(self.lagT))
        self.ransac(an_samples, cq_samples, sample_times)
        print("lag after estimated is {}".format(self.lagT))
        self.ice(threshold)
        print("lag after run ice: {}".format(self.lagT))
        res_lag = self.consequents[self.which_b_in_consequent] - self.antecedents
        return res_lag

    def ice(self, threshold):
        '''
        ice 运行
        :param threshold:
        :return:
        '''
        delta = 1.0
        iteration = 0

        while delta > threshold and iteration < self.max_iteration:
            estimate_lag = 0
            # 用于存储b中接近点的下标
            self.which_b_in_consequent = []

            for i in range(self.len_a):
                # a 是原始序列 这里找到按时滞时间平移之后最接近的 a中的第i个点 的点下标
                a = self.antecedents[i]
                time_delay_between_a_b = np.fabs(self.consequents - (a + self.lagT))
                j = time_delay_between_a_b.argmin()
                self.which_b_in_consequent.append(j)
                # 估计一下a与b之间在第i个点上的时滞
                estimate_lag += self.consequents[j] - a

            # 所有的a中的时刻点的平均估计时滞
            estimate_lag = 1.0 * estimate_lag / self.len_a

            # 时滞的减少量
            delta = abs(self.lagT - estimate_lag)
            self.lagT = estimate_lag
            iteration += 1

            print("delta lag {} in round {}".format(delta, iteration))

    def nearest_k_samples(self, time_arr, target_position, k):
        '''
        寻找最近的k的点 前提：arr有序
        :param time_arr:
        :param target_position:
        :param k:
        :return:
        '''
        nearests = []
        indices = []
        max_indice = len(time_arr)
        if target_position > 0:
            lowest = target_position - 1
        else:
            lowest = 0
        if target_position < max_indice -1:
            highest = target_position + 1
        else:
            highest = max_indice -1

        left_part = abs(time_arr[lowest] - time_arr[target_position])
        right_part = abs(time_arr[highest] - time_arr[target_position])

        while k:
            if left_part < right_part:
                nearests.append(time_arr[lowest])
                indices.append(lowest)
                if lowest > 0:
                    lowest -= 1
                left_part = abs(time_arr[lowest] - time_arr[target_position])
            else:
                nearests.append(time_arr[highest])
                indices.append(highest)
                if highest < max_indice - 1:
                    highest += 1
                right_part = abs(time_arr[highest] - time_arr[target_position])
            k -= 1

        return nearests, indices

    def ransac(self, s, k, sample_times):
        '''
        随机子空间采样
        :param s: antecedents 中采样 S 个
        :param k: consequents 中采样 k 个
        :param sample_times: 采样次数
        :return:
        '''
        lag_error = 0
        iteration = 0
        # inplace
        self.antecedents.sort()
        self.consequents.sort()

        while iteration < sample_times:
            # 在SA中选择s个点,保证样本点距离最小(先随机挑选一个点,然后使用最近邻选集合)
            center = np.random.randint(self.len_a, size=1)[0]
            _, indices_a = self.nearest_k_samples(self.antecedents, center, s)
            # print(center, indices_a)

            lag_sample = 0
            # S 个 点
            for i in indices_a:
                # 对每个样本点在SB中找到K最近邻
                a = self.antecedents[i]
                distance_arr = np.fabs(self.consequents - a)
                near_a_in_b = distance_arr.argmin()

                # print(near_a_in_b, self.consequents[near_a_in_b], a)

                _, indices_b = self.nearest_k_samples(self.consequents, near_a_in_b, k)
                # print(near_a_in_b, indices_b)

                # 随机选择一个作为配对 采样lag
                j = np.random.randint(k, size=1)[0]
                # print(self.consequents[indices_b[j]], a)

                lag_sample += self.consequents[indices_b[j]] - a
                # print(lag_sample)

            # 计算平均采样时滞时间
            lag_sample = 1.0 * lag_sample / s
            # print('o: ', lag_sample)

            # 余集计算平均时滞,获得lag_error,将lag_error最小的lag_sample作为初始值
            lag_new = 0
            diff = np.setdiff1d(self.antecedents, self.antecedents[indices_a])
            for a in diff:
                temp = np.fabs(self.consequents - (a + lag_sample))
                j = temp.argmin()
                lag_new += self.consequents[j] - a
            lag_new = 1.0 * lag_new / self.len_a
            # print('n: ', lag_new)

            # 计算lag的变化
            delta = abs(lag_new - lag_sample)
            # 初始化lag_error
            if iteration == 0:
                lag_error = delta
                self.lagT = lag_sample
            else:
                if lag_error > delta:
                    print(lag_error)
                    lag_error = delta
                    self.lagT = lag_sample

            iteration += 1
