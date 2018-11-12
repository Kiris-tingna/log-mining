import numpy as np


def analomy_detec(true, pre, top_g, outputfile):
    '''
    对log的log key sequence进行异常检测，对于测试数据，通过调用前面的lstm模型可以生成预测属于每个类别的概率。判断预测出的前top_g的类别中是否包含真实类别，若果不包含，说明此时发生了异常
    :param true: 数据类型 list，真实发生的log key
    :param pre: 数据类型 二维list， 预测出发生的log key的概率
    :param top_g: 前top_g个log key用于判断
    :param outputfile: 将结果保存到文件的路径
    :return: 返回对于每个序列预测和真实是否一致的标签
    '''
    output = open(outputfile, 'w+')
    output.write('test, predicted, label\n')
    label = []
    pre = np.array(pre)
    pre_index = np.argsort(-pre, axis=1)   # 对预测出来的概率进行降序排列
    for i in range(len(true)):
        # pre_key = [k for k in pre[i][0:top_g]]
        pre_dict = {}
        for k in range(top_g):
            pre_dict[pre_index[i][k]] = pre[i][pre_index[i][k]]   # 预测出来的前top_g个类别的log
        if true[i] not in pre_dict.keys():   # 真实log的类别是否在前top_g中
            label.append(1)
        else:
            label.append(0)

        line = []
        for key, value in pre_dict.items():
            line.append(str(key) + ': ' + str(value))
        line = '{' + ', '.join(line) + '}'

        line = str(true[i]) + ', ' + line + ', ' + str(label[i]) + '\n'
        output.write(line)

    auc = (len(label) - sum(label)) / len(label)
    output.write('the accuracy score is: %f\n' % auc)
    output.close()
    return label