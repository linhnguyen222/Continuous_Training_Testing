import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import tflite_runtime.interpreter as tflite

# from sklearn.metrics import mean_squared_error
import json
def retrain(file_name):
    # Read dataset from file
    raw_dataset = pd.read_csv(file_name, 
        names=["id","value","station_id","parameter_id","unix_timestamp","label", "prediction"])
    mean_val = raw_dataset['value'].mean()
    raw_dataset['norm_value'] = raw_dataset['value']-mean_val
    max_val = raw_dataset['norm_value'].max()
    raw_dataset['norm_value'] = raw_dataset['norm_value']/max_val
    raw_dataset = raw_dataset.astype({'id':'float','value':'float', 'station_id':'int', 'parameter_id':'int', 'unix_timestamp':'int', 'norm_time':'float'})
    
    dataset = raw_dataset.copy()
    dataset = dataset.dropna().drop(['id','station_id','parameter_id','unix_timestamp'], axis=1)
    dataset_full = dataset.sort_values(by=['norm_time'])
    dataset = dataset_full[0:300]

    # pre-processing data 

    serial_data = dataset.drop(['value','norm_time'], axis=1)
    serial_data['norm_1'] = serial_data['norm_value'].shift(1)
    serial_data['norm_2'] = serial_data['norm_value'].shift(2)
    serial_data['norm_3'] = serial_data['norm_value'].shift(3)
    serial_data['norm_4'] = serial_data['norm_value'].shift(4)
    serial_data['norm_5'] = serial_data['norm_value'].shift(5)
    serial_data['norm_6'] = serial_data['norm_value'].shift(6)
    serial_data = serial_data[6:]

   # Split data into training and testing
    train_dataset = serial_data.sample(frac=0.8, random_state=1)
    test_dataset = serial_data.drop(train_dataset.index)

    train_features = np.array(train_dataset.drop(['norm_value'], axis=1))
    train_features = np.array(train_features)[:,:,np.newaxis]
    train_labels = np.array(train_dataset.drop(['norm_6'], axis=1))
    train_labels = train_labels.reshape(train_labels.shape[0],train_labels.shape[1],1)
    
    test_features = np.array(test_dataset.drop(['norm_value'], axis=1))
    test_features = test_features.reshape(test_features.shape[0],test_features.shape[1],1)
    test_features.shape

    model = keras.Sequential()
    model.add(layers.LSTM(128, return_sequences=True))
    model.add(layers.TimeDistributed(layers.Dense(1)))
    model.compile(loss='mean_squared_error', optimizer=tf.keras.optimizers.Adam(0.005))
    model.fit(train_features, train_labels, epochs=1, batch_size=1, verbose=2)
    # load saved_model 
    interpreter = tflite.Interpreter("./exported_models/tflite_model/LSTM_single_series.tflite")
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    # interpreter.resize_tensor_input(input_details[0]['index'],batch_input)
    # interpreter.resize_tensor_input(output_details[0]['index'],batch_input)
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    interpreter.allocate_tensors()
    interpreter.set_tensor(input_details[0]['index'], test_features)
    interpreter.invoke()
    old_model_result = interpreter.get_tensor(output_details[0]['index']) 
