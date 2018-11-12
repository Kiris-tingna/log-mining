import numpy as np


def process_data(data, seq_len, split_rate, normalise_window=False):
    '''
    对数据进行处理，将数据的一行变为一个sequence，直接预测这一行对应的sequence的下面可能的log，同时划分训练数据和测试数据
    :param data: 数据类型 dataframe， 输入数据
    :param seq_len: 以多长的序列作为输入进行预测下面的log
    :param split_rate: 将数据划分为训练数据和测试数据的比例
    :param normalise_window: 是否需要将数据正则化
    :return: x_train, y_train, x_test, y_test, row， 数据类型：np.array
    '''
    sequence_length = seq_len + 1
    result = []
    for index in range(len(data) - sequence_length):
        result.append(data[index: index + sequence_length])

    if normalise_window:
        result = normalise_windows(result)

    result = np.array(result)

    row = round(split_rate * result.shape[0])
    train = result[:int(row), :]

    np.random.shuffle(train)
    x_train = train[:, :-1]
    y_train = train[:, -1]
    x_test = result[int(row):, :-1]
    y_test = result[int(row):, -1]

    x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))   # 将训练数据和测试数据转化为(samples, timestep, features)的三维张量
    x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1))

    return [x_train, y_train, x_test, y_test, row]


def normalise_windows(window_data):
    normalised_data = []
    for window in window_data:
        normalised_window = [((float(p) / float(window[0])) - 1) for p in window]
        normalised_data.append(normalised_window)
    return normalised_data