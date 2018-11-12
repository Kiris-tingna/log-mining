import numpy as np
import pandas as pd
import lstm_model
import process_data
from keras.utils import np_utils
import os
import warnings
import copy
import time


os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Hide messy TensorFlow warnings
warnings.filterwarnings("ignore")  # Hide messy Numpy warnings


def build_model(data, seq_len, lstm_path, split_rate=0.7):
    '''
    根据当前数据以及提供的训练sequence长度，对数据进行处理并且使用训练数据训练该sequence长度对应的lstm模型，并且将模型保存下来，避免反复训练
    :param data: 数据类型 dataframe， 用于训练的数据，没有经过处理
    :param seq_len: 2, 使用多长的历史sequence进行训练
    :param split_rate: 0.7， 使用多少比例来划分训练数据和测试数据
    :return: 返回一个lstm的对象
    '''

    X_train, y_train, X_test, y_test, row = process_data.process_data(data, seq_len, split_rate)  # 对数据进行处理，划分为训练数据和测试数据

    y_train = np_utils.to_categorical(y_train)

    params = {
        'lstm_output_dim': 50,
        'activation_lstm': 'relu',
        'activation_dense': 'relu',
        'activation_last': 'softmax',
        'dense_layer': 1,
        'lstm_layer': 2,
        'nb_epoch': 1
    }
    lstm_obj = lstm_model.RNN_network(**params)

    lstm_obj.model(X_train, y_train, X_test, y_test, lstm_path)
    return lstm_obj


def build_flow(lstm_path, all_flow, flowlist, data, lstm_obj, workflow, flow_len, start, distance=0, index=-1):
    '''
    针对当前的workflow，从workflow中截取一定的长度（flow_len），预测该序列的下一个可能的log key，从而建立workflow的图。具体方法是：1、在给定长度下，预测出来的下一个log key的概率>0.8，
    则表示预测出来的下一个log key是几乎百分之百会发生的，也就是当前是一个线性的workflow产生。2、在给定长度下，无法预测出来一个概率较大的log key作为下一个log key，那么我们有两种方案：
    1）增加当前的sequence的长度进行预测，看是否能够得到一个准确的、概率较高的log key作为下一个；2）如果增加长度一直无法给出一个准确的log key，那么我们考虑在此处workflow产生了分支，我们
    分别对workflow的每一个分支进行训练。3、此外，我们需要考虑在构建workflow的过程中会出现loop的情况，一般出现这种情况也就表明当前的workflow构建完成，同过调用if_loop函数来判断在构建的过
    程中是否形成了环。
    :param lstm_path: 数据类型 str， 保存lstm模型存放的位置
    :param all_flow: 数据类型 list，保存所有的workflow
    :param flowlist: 数据类型 list，保存在生成workflow的过程中在当前时间窗口内预测得到下一个log key的概率
    :param data: 数据类型 dataframe，用于训练的数据
    :param lstm_obj: 训练出来的lstm模型
    :param workflow: 数据类型 list，当前已有的workflow
    :param flow_len: 数据类型 int，以多长的长度进行预测下一个log key
    :param start: 数据类型 int，从当前workflow的那个位置开始预测下一个
    :param distance: 标志在当前位置是否产生循环，distance=1表示没有循环需要考虑，当distance>1时，表示产生循环，且distance的值表示当前为止还需要循环的位数，当distance=1时则表示一个循环完成
    :param index: 标志在当前位置是否产生循环，index=-1表示没有循环，index不等于-1则表示有循环，且index的值表示当前预测的值在workflow中index的位置出现
    :return:
    '''
    global start_time
    print(workflow, 'start from: ', start, 'test len is: ', flow_len)
    if start + flow_len <= len(workflow):
        print('test work flow is, ', workflow[start:start+flow_len])
        this_flow = np.array(workflow[start:start+flow_len])
        this_flow = np.reshape(this_flow, (1, this_flow.shape[0], 1))

        if not os.path.exists(lstm_path):  # 如果当前所需的模型没有存在过，那么调用模型训练的函数训练当前sequence长度的模型
            lstm_obj = build_model(data, flow_len, lstm_path)

        pre_class, class_pro = lstm_obj.prediction(this_flow, lstm_path)

        class_pro = np.array(class_pro[0])
        pre_index = np.argsort(-class_pro, axis=0)   # 对模型预测出来的序列发生的概率进行降序排列

        if class_pro[pre_index[0]] > 0.8:     # 预测出来下一个发生的概率接近1，即下一个序列跟在当前序列之后100%发生
            # 如果当前出现一个与现有workflow中的log key相同的log key，那么需要判断是否会出现环
            if_loop(lstm_path, all_flow, flowlist, lstm_obj, workflow, flow_len, start, pre_index[0], class_pro[pre_index[0]], distance, index)

        else:   # 如果预测出来下一个log key发生的概率不是接近于1，那么表示在这一位置有好几个事件可能会发生，我们需要扩大预测用的sequence的长度进一步确定
            if start+flow_len <= len(workflow) and flow_len <= 15 and start > 0:
                print('add sequence length, ', flow_len+1)
                build_flow(lstm_path, all_flow, flowlist, data, lstm_obj, workflow, flow_len + 1, start - 1, distance, index)

            # 扩大sequence长度也无法确定下一个log key时，需要考虑这是一个分叉点
            else:
                i = 0
                tmp = copy.deepcopy(workflow)
                while class_pro[pre_index[i]] >= 0.2:
                    i += 1
                    print('divergence at ', workflow[-1], 'new flow is ', pre_index[i-1])
                    print('----------------------divergence------------------------')
                    if_loop(lstm_path, all_flow, flowlist, lstm_obj, workflow, 2, len(workflow)-2, pre_index[i-1], class_pro[pre_index[i-1]], distance, index)
                    workflow = tmp
                    nowtime = time.time()
                    if nowtime-start_time > 2:
                        return


def if_loop(lstm_path, all_flow, flowlist, lstm_obj, workflow, flow_len, start, pre, pro, distance=0, index=-1):
    '''
    判断在构建workflow的过程中是否形成环。
    :param lstm_path: 数据类型 str， 保存lstm模型存放的位置
    :param all_flow: 数据类型 list，保存所有的workflow
    :param flowlist: 数据类型 list，保存在生成workflow的过程中在当前时间窗口内预测得到下一个log key的概率
    :param lstm_obj: 训练出来的lstm模型
    :param workflow: 数据类型 list，当前已有的workflow
    :param flow_len: 数据类型 int，以多长的长度进行预测下一个log key
    :param start: 数据类型 int，从当前workflow的那个位置开始预测下一个
    :param pre: 当前的sequence能够预测出来的下一个log key
    :param pro: 当前sequence预测出来下一个log key的概率
    :param distance: 标志在当前位置是否产生循环，distance=1表示没有循环需要考虑，当distance>1时，表示产生循环，且distance的值表示当前为止还需要循环的位数，当distance=1时则表示一个循环完成
    :param index: 标志在当前位置是否产生循环，index=-1表示没有循环，index不等于-1则表示有循环，且index的值表示当前预测的值在workflow中index的位置出现
    :return:
    '''
    # 如果workflow的长度过长，不在继续向下构建，直接返回
    if len(workflow) > 30:
        print('flow too long----------------------------------------')
        return

    # 当前预测出来的sequence在前面出现过，可能会形成环
    if pre in workflow:
        if index == -1:  # 如果是第一次出现相同的log key，那么需要记录当前两个相同的log key之间的距离以及相同的log key最后一次出现的位置
            index = int(np.where(np.array(workflow) == pre)[-1][-1])
            distance = len(workflow) - index + 1
            print('loop exist, loop start from ', workflow[index], 'loop length is ', distance)
            print('--------------------------loop----------------------------')

            workflow.append(pre)
            flowlist.append((workflow[start:start+flow_len], pre, pro))
            build_flow(lstm_path, all_flow, flowlist, data, lstm_obj, workflow, flow_len, start + 1, distance=distance - 1,
                       index=index + 1)  # 将当前的log key加入到当前sequence中，向前移动一步，继续预测下一步的log key

        elif pre == workflow[index]:  # 如果不是第一次出现相同log key，首先如果distance减小为1，表示当前为止形成一个环，结束程序，给出形成的work flow

            if distance == 1:
                print('loop finish----------------------------------------')
                all_flow.append(workflow)
                return
            else:  # 如果distance没有减小到1，表示当前还没有形成环，distance-1，继续预测下一个出现的log key
                print('loop continue-------------')
                workflow.append(pre)
                flowlist.append((workflow[start:start + flow_len], pre, pro))
                build_flow(lstm_path, all_flow, flowlist, data, lstm_obj, workflow, flow_len, start + 1, distance=distance - 1,
                           index=index + 1)  # 将当前的log key加入到当前sequence中，向前移动一步，继续预测下一步的log key

        else:
            print('loop break-----------------')
            workflow.append(pre)
            flowlist.append((workflow[start:start + flow_len], pre, pro))
            build_flow(lstm_path, all_flow, flowlist, data, lstm_obj, workflow, flow_len,
                       start + 1)  # 将当前的log key加入到当前sequence中，向前移动一步，继续预测下一步的log key

    # 不存在出现环的可能性
    else:
        print('no loop------------------')
        workflow.append(pre)
        flowlist.append((workflow[start:start + flow_len], pre, pro))
        build_flow(lstm_path, all_flow, flowlist, data, lstm_obj, workflow, flow_len,
                   start + 1)  # 将当前的log key加入到当前sequence中，向前移动一步，继续预测下一步的log key


def generate(data, lstm_path, resultpath):
    seq_len = 2

    lstm_obj = build_model(data, seq_len, lstm_path+str(seq_len))

    # ini_flow = data[0:seq_len+4]
    ini_flow = [261, 149]
    # ini_flow = [67, 66]
    print('initial sequence:', ini_flow)

    flow_list = []
    all_flow = []
    build_flow(lstm_path+str(seq_len), all_flow, flow_list, data, lstm_obj, ini_flow, seq_len, 0)
    print('all_flow')
    print(all_flow)

    flow_pro = []
    sum = 0
    for i in all_flow:
        index = int(np.where(np.array(i[:-2]) == i[-1])[-1][-1])
        flow_pro.append(flow_list[sum:sum+index-1])
        sum += len(i)

    # output = open(resultpath, 'w+')
    # output.write(all_flow)
    # output.write(flow_pro)

    return flow_pro


def plot_flow(data, resultpath, template=None):
    '''
    画workflow图
    :param data: 生成的workflow的结果
    :param resultpath: 存放图的位置
    :param template: 存放template的位置
    :return:
    '''
    from graphviz import Digraph
    dot = Digraph(resultpath)
    dot.attr('node', shape='box')
    if template:
        df1 = pd.read_csv(template, index_col='event')

        for flow in data:
            for i in flow:
                dot.node(str(i[0][-1]), df1.iat[i[0][-1], 0])
                dot.node(str(i[1]), df1.iat[i[1], 0])
                dot.edge(str(i[0][-1]), str(i[1]), str(i[2]))
        dot.render(view=True, format='png')

    else:
        for flow in data:
            for i in flow:
                dot.node(str(i[0][-1]))
                dot.node(str(i[1]))
                dot.edge(str(i[0][-1]), str(i[1]), str(i[2]))
        dot.render(view=True, format='png')


if __name__ == '__main__':
    start_time = time.time()
    # df = pd.read_csv(r'E:\data\data\test_env_12_1m_deal\data_proc1_sort_slot1.txt')
    # data = list(df['number'].values)
    #
    # workflow = generate(data, 'result\model', 'result\workflow1')
    #
    # plot_flow(workflow, 'result_graph\workflow_new_1')

    df1 = pd.read_csv(r'E:\data\data\bsg_nova_1030_300000.csv')

    data = list(df1['event'].values)

    lstm_path = r'result\model_bsg'
    workflow = generate(data, lstm_path, 'result\workflow_bsg')

    template = r'E:\data\data\template.csv'
    plot_flow(workflow, 'result_graph\workflow_bsg3', template)













