#UB CSE 610
#Special Topics
#Deep Learning
#Stock data Analysis using LSTM
#Mihir Kulkarni
#UB Person Number: 5016 8610
#Email:mihirdha@buffalo.edu
#Amol Salunkhe
#Ub Person Number:29612314
#Email:aas22@buffalo.edu
#Ref:https://goo.gl/Qjc5uE
#Date: 11 December 2016
#Req: See requirements.txt for the requirements.


#%pylab inline
import matplotlib.pyplot as plt
import tensorflow as tf
import numpy as np
import numpy.random as rng
import pandas.io.data as web
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error
import dateutil.parser
import datetime
import matplotlib.dates as mdates
from tensorflow.python.framework import dtypes
from tensorflow.contrib import learn as tflearn
from tensorflow.contrib import layers as tflayers


myDirectory = './log'
numSteps = 30
numLayers = [{'num_units': 5}]
trSteps = 10000
printSteps = trSteps / 10
batch = 100

def rnn_data(data, time_steps, labels=False):
    rnn_df = []
    for i in range(len(data) - time_steps):
        if labels:
            try:
                rnn_df.append(data.iloc[i + time_steps].as_matrix())
            except AttributeError:
                rnn_df.append(data.iloc[i + time_steps])
        else:
            data_ = data.iloc[i: i + time_steps].as_matrix()
            rnn_df.append(data_ if len(data_.shape) > 1 else [[i] for i in data_])

    return np.array(rnn_df, dtype=np.float32)


def split_data(data, val_size=0.1, test_size=0.1):
    ntest = int(round(len(data) * (1 - test_size)))
    nval = int(round(len(data.iloc[:ntest]) * (1 - val_size)))

    df_train, df_val, df_test = data.iloc[:nval], data.iloc[nval:ntest], data.iloc[ntest:]

    return df_train, df_val, df_test

def prepare_data(data, time_steps, labels=False, val_size=0.1, test_size=0.1):
    df_train, df_val, df_test = split_data(data, val_size, test_size)
    return (rnn_data(df_train, time_steps, labels=labels),
            rnn_data(df_val, time_steps, labels=labels),
            rnn_data(df_test, time_steps, labels=labels))

def load_csvdata(rawdata, time_steps, seperate=False):
    data = rawdata
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)

    train_x, val_x, test_x = prepare_data(data['a'] if seperate else data, time_steps)
    train_y, val_y, test_y = prepare_data(data['b'] if seperate else data, time_steps, labels=True)
    return dict(train=train_x, val=val_x, test=test_x), dict(train=train_y, val=val_y, test=test_y)

def get_stockPriceByDay(symbol):
    start, end = '2007-05-02', '2016-04-11'
    data = web.DataReader(symbol, 'yahoo', start, end)
    data=pd.DataFrame(data)
    print(list(data.columns.values))
    df =  pd.DataFrame(data, columns=['Adj Close'])
    return df

	
def lstm_model(num_units, rnn_layers, dense_layers=None, learning_rate=0.1, optimizer='Adagrad'):
    def lstm_cells(layers):
        if isinstance(layers[0], dict):
            return [tf.nn.rnn_cell.DropoutWrapper(tf.nn.rnn_cell.BasicLSTMCell(layer['num_units'],
                                                                               state_is_tuple=True),
                                                  layer['keep_prob'])
                    if layer.get('keep_prob') else tf.nn.rnn_cell.BasicLSTMCell(layer['num_units'],
                                                                                state_is_tuple=True)
                    for layer in layers]
        return [tf.nn.rnn_cell.BasicLSTMCell(steps, state_is_tuple=True) for steps in layers]

    def dnn_layers(input_layers, layers):
        if layers and isinstance(layers, dict):
            return tflayers.stack(input_layers, tflayers.fully_connected,
                                  layers['layers'],
                                  activation=layers.get('activation'),
                                  dropout=layers.get('dropout'))
        elif layers:
            return tflayers.stack(input_layers, tflayers.fully_connected, layers)
        else:
            return input_layers

    def _lstm_model(X, y):
        stacked_lstm = tf.nn.rnn_cell.MultiRNNCell(lstm_cells(rnn_layers), state_is_tuple=True)
        x_ = tf.unpack(X, axis=1, num=num_units)
        output, layers = tf.nn.rnn(stacked_lstm, x_, dtype=dtypes.float32)
        output = dnn_layers(output[-1], dense_layers)
        prediction, loss = tflearn.models.linear_regression(output, y)
        train_op = tf.contrib.layers.optimize_loss(
            loss, tf.contrib.framework.get_global_step(), optimizer=optimizer,
            learning_rate=learning_rate)
        return prediction, loss, train_op

    return _lstm_model	
	
stockPrices = get_stockPriceByDay('%5EGSPC')

X, y = load_csvdata(stockPrices, numSteps, seperate=False)

regressor = tf.contrib.learn.Estimator(model_fn=lstm_model(numSteps, numLayers),model_dir=myDirectory)


validation_monitor = tf.contrib.learn.monitors.ValidationMonitor(X['val'], y['val'],every_n_steps=printSteps,early_stopping_rounds=1000)
regressor.fit(X['train'], y['train'],monitors=[validation_monitor],batch_size=batch,steps=trSteps)

predicted = regressor.predict(X['test'])

print('-------------------------------------------------------------------------------------')

lst=list(predicted)

print('-------------------------------------------------------------------------------------')
score = mean_squared_error(lst, y['test'])
print ("MSE: %f" % score)

