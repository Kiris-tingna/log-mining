import os
import numpy as np
import pandas as pd
from keras.models import Sequential
from keras.layers import LSTM, Dense
from keras.models import load_model, save_model
import process_data
from keras.utils import np_utils


class RNN_network():

    def __init__(self, **kwargs):
        '''
        模型的参数
        :param kwargs:
        **kwargs: lstm_output_dim=4: output dimension of LSTM layer;
                        activation_lstm='relu': activation function for LSTM layers;
                        activation_dense='relu': activation function for Dense layer;
                        activation_last='softmax': activation function for last layer;
                        drop_out=0.2: fraction of input units to drop;
                        np_epoch=25, the number of epoches to train the model. epoch is one forward pass and one backward pass of all the training examples;
                        batch_size=100: number of samples per gradient update. The higher the batch size, the more memory space you'll need;
                        loss='categorical_crossentropy': loss function;
                        optimizer='rmsprop'
        '''
        self.output_dim = kwargs.get('output_dim', 8)
        self.activation_lstm = kwargs.get('activation_lstm', 'relu')
        self.activation_dense = kwargs.get('activation_dense', 'relu')
        self.activation_last = kwargs.get('activation_last', 'softmax')
        self.dense_layer = kwargs.get('dense_layer', 1)
        self.lstm_layer = kwargs.get('lstm_layer', 2)
        self.drop_out = kwargs.get('drop_out', 0.2)
        self.nb_epoch = kwargs.get('nb_epoch', 10)
        self.batch_size = kwargs.get('batch_size', 100)
        self.loss = kwargs.get('loss', 'categorical_crossentropy')
        self.optimizer = kwargs.get('optimizer', 'rmsprop')

    def model(self, trainX, trainY, testX, testY, model_save_path):
        '''
        构建双层的lstm模型，其中输入为序列长度的一列数据，输出预测该序列长度的下一个label是什么。输入维度为序列长度，输出维度为label的长度
        :param trainX: 数据类型 dataframe， 训练数据输入
        :param trainY: 数据类型 dataframe， 训练数据输出
        :param testX: 数据类型 dataframe，测试数据输入
        :param testY: 数据类型 dataframe，测试数据输出
        :param model_save_path: 模型保存路径
        :return:
        '''
        print('training model is LSTM network')
        # input_dim = trainX[0].shape[1]   # lstm模型的输入维度
        input_dim = 1   # lstm模型的输入维度
        output_dim = trainY.shape[1]     # lstm模型的输出维度

        model = Sequential()
        model.add(LSTM(
            output_dim=self.output_dim,
            input_dim=input_dim,
            activation=self.activation_lstm,
            dropout=self.drop_out,
            return_sequences=True
        ))

        model.add(LSTM(
            output_dim=self.output_dim,
            input_dim=self.output_dim,
            activation=self.activation_lstm,
            dropout=self.drop_out
        ))

        model.add(Dense(
            output_dim=output_dim,
            activation=self.activation_last))

        model.compile(loss=self.loss, optimizer=self.optimizer, metrics=['accuracy'])

        model.fit(x=trainX, y=trainY, nb_epoch=self.nb_epoch, batch_size=self.batch_size,
                  validation_split=0.1)

        # score = model.evaluate(trainX, trainY, self.batch_size)
        # print("Model evaluation: {}".format(score))

        save_model(model, model_save_path)

    @staticmethod
    def prediction(dataset, model_save_path):
        '''
        对测试数据进行预测
        :param dataset: 数据类型 dataframe， 测试数据
        :param model_save_path: 模型保存的路径
        :return: predict_class, class_prob：预测的最终类别，预测数属于每个类别的概率
        '''
        dataset = np.asarray(dataset)

        if not os.path.exists(model_save_path):
            raise ValueError(
                "Lstm model not found! Train one first or check your input path: {}".format(model_save_path))
        model = load_model(model_save_path)

        predict_class = model.predict_classes(dataset)
        class_prob = model.predict_proba(dataset)
        return predict_class, class_prob


# def use_model(data, seq_len, split_rate, model_path):
#     X_train, y_train, X_test, y_test, row = process_data.process_data(data, seq_len, split_rate)
#
#     y_train = np_utils.to_categorical(y_train)
#
#     params = {
#         'lstm_output_dim': 50,
#         'activation_lstm': 'relu',
#         'activation_dense': 'relu',
#         'activation_last': 'softmax',
#         'dense_layer': 1,
#         'lstm_layer': 2
#     }
#     lstm_obj = RNN_network(**params)
#
#     lstm_obj.model(X_train, y_train, X_test, y_test, model_path + str(seq_len))
