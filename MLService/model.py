import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.metrics import mean_squared_error
import json

def main():
    # Read dataset from file
    raw_dataset = pd.read_csv("./grouped_data/11_20_21_1161114004_122_.csv")
    mean_val = raw_dataset['value'].mean()
    raw_dataset['norm_value'] = raw_dataset['value']-mean_val
    max_val = raw_dataset['norm_value'].max()
    raw_dataset['norm_value'] = raw_dataset['norm_value']/max_val
    raw_dataset = raw_dataset.astype({'id':'float','value':'float', 'station_id':'int', 'parameter_id':'int', 'unix_timestamp':'int', 'norm_time':'float'})
    
    dataset = raw_dataset.copy()
    dataset = dataset.dropna().drop(['id','station_id','parameter_id','unix_timestamp'], axis=1)
    dataset_full = dataset.sort_values(by=['norm_time'])
    dataset = dataset_full[0:300]
    # Read test dataset from a different file
    test_file_name = "./grouped_data/11_21_21_1161114004_122_.csv"
    test_raw_dataset = pd.read_csv(test_file_name)
    test_raw_dataset['norm_value'] = test_raw_dataset['value']-mean_val

    test_raw_dataset['norm_value'] = test_raw_dataset['norm_value']/max_val
    test_raw_dataset = test_raw_dataset.astype({'id':'float','value':'float', 'station_id':'int', 'parameter_id':'int', 'unix_timestamp':'int', 'norm_time':'float'})
    test_dataset = test_raw_dataset.copy()
    test_dataset = test_dataset.dropna().drop(['id','station_id','parameter_id','unix_timestamp'], axis=1)
    test_dataset_full = test_dataset.sort_values(by=['norm_time'])
    # Choose a small part of the data to test the model
    start_line = 0
    end_line = 100
    test_data = test_dataset_full[start_line:end_line]

    # pre-processing data 

    serial_data = dataset.drop(['value','norm_time'], axis=1)
    serial_data['norm_1'] = serial_data['norm_value'].shift(1)
    serial_data['norm_2'] = serial_data['norm_value'].shift(2)
    serial_data['norm_3'] = serial_data['norm_value'].shift(3)
    serial_data['norm_4'] = serial_data['norm_value'].shift(4)
    serial_data['norm_5'] = serial_data['norm_value'].shift(5)
    serial_data['norm_6'] = serial_data['norm_value'].shift(6)
    serial_data = serial_data[6:]

    test_serial_data = test_data.drop(['value','norm_time'], axis=1)
    test_serial_data['norm_1'] = test_serial_data['norm_value'].shift(1)
    test_serial_data['norm_2'] = test_serial_data['norm_value'].shift(2)
    test_serial_data['norm_3'] = test_serial_data['norm_value'].shift(3)
    test_serial_data['norm_4'] = test_serial_data['norm_value'].shift(4)
    test_serial_data['norm_5'] = test_serial_data['norm_value'].shift(5)
    test_serial_data['norm_6'] = test_serial_data['norm_value'].shift(6)
    test_serial_data = test_serial_data[6:]

    train_dataset = serial_data
    test_dataset = test_serial_data
    train_features = np.array(train_dataset.drop(['norm_value'], axis=1))
    train_features = np.array(train_features)[:,:,np.newaxis]
    train_labels = np.array(train_dataset.drop(['norm_6'], axis=1))
    train_labels = train_labels.reshape(train_labels.shape[0],train_labels.shape[1],1)
    test_features = np.array(test_dataset.drop(['norm_value'], axis=1))
    test_features = test_features.reshape(test_features.shape[0],test_features.shape[1],1)
    test_labels = np.array(test_dataset.drop(['norm_6'], axis=1))
    test_labels = test_labels.reshape(test_labels.shape[0],test_labels.shape[1],1)


    model = keras.Sequential()
    model.add(layers.LSTM(32, return_sequences=True))
    model.add(layers.LSTM(32, return_sequences=True))
    model.add(layers.TimeDistributed(layers.Dense(1)))
    model.compile(loss='mean_squared_error', optimizer=tf.keras.optimizers.Adam(0.005))
    model.fit(train_features, train_labels, epochs=1, batch_size=1, verbose=2)
    # result = model.predict(test_features, batch_size=1, verbose=0)
    # # print(result)
    # x=pd.DataFrame(test_labels.reshape(test_labels.shape[0],test_labels.shape[1]))
    # y=pd.DataFrame(result.reshape(result.shape[0],result.shape[1]))
    # y_true = np.array(x[0])
    # y_pred = np.array(y[0])
    # mse = mean_squared_error(y_true, y_pred)
    # print(mse)
    # Convert the model.
    # Save the model.
    saved_model_path = "./LSTM_single_series/saved_model"
    model.save(saved_model_path)
    converter = tf.compat.v1.lite.TFLiteConverter.from_saved_model(saved_model_path)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.experimental_new_converter = True
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS, tf.lite.OpsSet.SELECT_TF_OPS]
    # converter.target_spec.supported_ops = [
    #     # tf.lite.OpsSet.TFLITE_BUILTINS, # enable TensorFlow Lite ops.
    #     tf.lite.OpsSet.SELECT_TF_OPS # enable TensorFlow ops.
    # ]
    tflite_model = converter.convert()
    model_dir_path = "./LSTM_single_series/LSTM_single_series.tflite"
    with open(model_dir_path, 'wb') as f:
        f.write(tflite_model)
    
    normalization_param = {
        "mean_val": mean_val,
        "max_val": max_val
    }
    # Serializing json 
    normalization_param_json = json.dumps(normalization_param, indent = 4)
    
    # Writing to sample.json
    with open("./LSTM_single_series/param.json", "w") as jsonfile:
        jsonfile.write(normalization_param_json)

if __name__ == "__main__":
    main()
