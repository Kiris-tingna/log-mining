import pandas as pd
import lstm_model
import logkey_analomy_detect
import process_data
import time
from keras.utils import np_utils
import os
import warnings


os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Hide messy TensorFlow warnings
warnings.filterwarnings("ignore")  # Hide messy Numpy warnings


if __name__ == '__main__':
    global_start_time = time.time()

    seq_len = 10        # 训练sequence长度
    split_rate = 0.1      # 划分训练数据和测试数据的比例

    # df = pd.read_csv(r'E:\data\data\test_env_12_1m_deal\data_proc1_sort_slot1.txt')
    # data = list(df['number'].values)

    df1 = pd.read_csv(r'E:\data\data\bsg_nova_1030_sort.csv')
    # df1 = df1.sort_values(by='time')
    df1 = df1.head(3000000)      # 自己机器运行报memery error错，因此用前300000条运行

    data = list(df1['event'].values)

    X_train, y_train, X_test, y_test, row = process_data.process_data(data, seq_len, split_rate)   # 对数据格式进行处理，对数据进行划分为训练数据和测试数据

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
    obj_lstm = lstm_model.RNN_network(**params)

    obj_lstm.model(X_train, y_train, X_test, y_test, model_save_path=r'result\model_bsg')          # 调用模型进行训练

    predict_class, class_pro = obj_lstm.prediction(X_test, model_save_path=r'result\model_bsg')     # 调用模型预测
    print(predict_class.shape)
    print(class_pro.shape)

    # top_g = 3
    # logkey_analomy_detect.analomy_detec(y_test, class_pro, top_g, outputfile=r'result\anamoly_bsg.txt')     # 异常检测

