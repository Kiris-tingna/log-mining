#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 @Time    : 2018/9/21 22:43
 @Author  : Kiristingna
 @File    : lag_em.py
 @Software: PyCharm
"""
import numpy as np
from logparser.utils import Timer
from scipy import stats

class LagEM(object):
    '''
    @author: Chunqiu Zeng
    @paper: Mining Temporal Lag from Fluctuating Events for Correlation and Root Cause Analysis

    lag em 算法挖掘时滞模式 使用EM算法寻找时滞的正态分布
    @key math formula
        1) miu = 1/n sum(j = 1, n) sum(i=1, m)  r_ij (b_j - a_i)
        2) sigma = miu = 1/n sum(j = 1, n) sum(i=1, m)  r_ij [ (b_j - a_i - miu) ^ 2 ]
        3) pi_ij = r_ij
    '''

    def __init__(self, an, cq, miu=10.0, sigma2=100, max_iteration=1e8):
        self.antecedents = np.asarray(an, dtype=np.float32)  # 祖先
        self.consequents = np.asarray(cq, dtype=np.float32)  # 结果
        self.miu = miu
        self.sigma2 = sigma2

        self.len_c = len(self.consequents)
        self.len_a = len(self.antecedents)

        average = 1.0 / self.len_a
        self.lags = np.asarray([self.consequents[i] - self.antecedents for i in range(self.len_c)])
        self.intermediate = np.full(shape=(self.len_c, self.len_a), fill_value=average)

        self.log_like_hood = 0.0
        self.max_iteration = max_iteration

        self.normalization = stats.norm.pdf(self.lags, self.miu, np.sqrt(self.sigma2))

    def run(self, threshold):
        '''
        迭代式运行em
        :param threshold:
        :return:
        '''
        it = 0
        delta = self._expectation_maximization()
        while delta > threshold and it < self.max_iteration:
            delta = self._expectation_maximization()
            it += 1
            print('delta:{:.2f} miu: {:.2f} sigma2: {:.2f} ratio: {:.2f}'.format(delta, self.miu, self.sigma2, self.miu /np.sqrt(self.sigma2)))

        return self.miu, self.sigma2

    @Timer
    def _expectation_maximization(self):
        '''
        运行em 得到正态分布的变化差值
        :return:
        '''
        old_log_like_hood = self.log_like_hood
        self._expectation()
        self._maximization()
        self._update_like_hood()

        return abs(self.log_like_hood - old_log_like_hood)

    def _expectation(self):
        '''
        step: E步
        :return:
        '''
        temp = self.intermediate * self.normalization
        temp_sum_row = temp.sum(axis=1)

        for i in range(self.len_c):
            if temp_sum_row[i] == 0:
                self.intermediate[i] *= 0
            else:
                self.intermediate[i] = temp[i] / temp_sum_row[i]

        return

    def _maximization(self):
        '''
        step: M步
        :return:
        '''
        self.miu = (self.intermediate * self.lags).sum() / self.len_c
        self.sigma2 = (self.intermediate * (self.lags - self.miu) ** 2).sum() / self.len_c
        return

    def _update_like_hood(self):
        '''
        更新对数似然
        :return:
        '''
        self.normalization = stats.norm.pdf(self.lags, self.miu, np.sqrt(self.sigma2))
        temp = self.intermediate * self.normalization

        accumulate = temp.sum(axis=1)
        _log_like_hood = 0.0

        for i in range(self.len_c):
            if accumulate[i]:
                _log_like_hood += np.log(accumulate[i])

        self.log_like_hood = _log_like_hood
        return