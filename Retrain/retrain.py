import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import tflite_runtime.interpreter as tflite
import os, inspect, sys
import subprocess
# from flask import Flask, request
from google.cloud import storage
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
# app = Flask(__name__)
gsclient = storage.Client()
import json
def retrain(file_name):
    print("running retrain", file_name)
        # Read dataset from file
    raw_dataset = pd.read_csv(file_name, 
        names=["id","station_id","parameter_id","unix_timestamp","norm_time","value", "label", "prediction"])
    mean_val = raw_dataset['value'].mean()
    raw_dataset['norm_value'] = raw_dataset['value']-mean_val
    max_val = raw_dataset['norm_value'].max()
    raw_dataset['norm_value'] = raw_dataset['norm_value']/max_val
    raw_dataset = raw_dataset.astype({'id':'float','value':'float', 'station_id':'int', 'parameter_id':'int', 'unix_timestamp':'int', 'label':'float', 'prediction':'float'})
    
    dataset = raw_dataset.copy()
    dataset = dataset.dropna().drop(['id','station_id','parameter_id','unix_timestamp', "label", "prediction"], axis=1)
    dataset_full = dataset.sort_values(by=['norm_time'])
    dataset = dataset_full[0:300]

    # pre-processing data 

    serial_data = dataset.drop(["value", "norm_time"], axis=1)
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
    test_labels = np.array(test_dataset.drop(['norm_6'], axis=1))
    test_labels = test_labels.reshape(test_labels.shape[0],test_labels.shape[1],1)

    print("creating model")
    model = keras.Sequential()
    model.add(layers.LSTM(128, return_sequences=True))
    model.add(layers.TimeDistributed(layers.Dense(1)))
    model.compile(loss='mean_squared_error', optimizer=tf.keras.optimizers.Adam(0.005))
    print("fitting model using tf cpu only")
    model.fit(train_features, train_labels, epochs=100, batch_size=1, verbose=2)
    print("done fitting, predicting new result")
    new_result = model.predict(test_features, batch_size=1, verbose=2)
    print("done predicting")
    # load saved_model 
    print("trying to load the in-use model")
    print("read {}/LSTM_single_series/LSTM_single_series.tflite".format(parentdir))
    interpreter = tflite.Interpreter(model_path="{}/LSTM_single_series/LSTM_single_series.tflite".format(parentdir))
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    interpreter.allocate_tensors()
    test_features = np.array(test_features, dtype='f')
    old_model_result_arr = []
    for item in test_features:
    # print("test_feature",test_features.shape)
        interpreter.set_tensor(input_details[0]['index'], [item])
        interpreter.invoke()
        old_model_result = interpreter.get_tensor(output_details[0]['index'])
        old_model_result_arr.append(old_model_result)
    Y_new_pred = [y[0][0] for y in new_result]
    Y_old_pred = [y[0][0][0] for y in old_model_result_arr]
    Y_true =  [y[0][0] for y in test_labels]
    new_model_mse = np.square(np.subtract(Y_true,Y_new_pred)).mean()
    old_model_mse = np.square(np.subtract(Y_true,Y_old_pred)).mean()
    print("new", new_model_mse, "old", old_model_mse)
    # if new_model_mse < old_model_mse:
    if True:
        print("replace the new model with old model")
        saved_model_path = "{}/LSTM_single_series/saved_model".format(parentdir)
        model.save(saved_model_path)
        converter = tf.lite.TFLiteConverter.from_saved_model(saved_model_path)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.experimental_new_converter = True
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS, tf.lite.OpsSet.SELECT_TF_OPS]
        tflite_model = converter.convert()
        model_dir_path = "{}/LSTM_single_series/LSTM_single_series.tflite".format(parentdir)
        with open(model_dir_path, 'wb') as f:
            f.write(tflite_model)
        
        normalization_param = {
            "mean_val": mean_val,
            "max_val": max_val
        }
        # Serializing json 
        normalization_param_json = json.dumps(normalization_param, indent = 4)
        print("replace old param with new param")
        # Writing to sample.json
        with open("{}/LSTM_single_series/param.json".format(parentdir), "w") as jsonfile:
            jsonfile.write(normalization_param_json)

        # start a subprocess to pack and deploy the model
        print("build, tag, and push new model")
        subprocess.call(['sh', '{}/deploy_server.sh'.format(parentdir)]) 

    sys.stdout.flush()

def trigger_retrain():
    
    bucket = gsclient.get_bucket('bts-data-atss')
    files = bucket.list_blobs()
    print("files", files)
    fileList = [file.name for file in files if 'Result' in file.name]
    print("fileList", fileList)
    last_file = len(fileList)-1
    blob = bucket.blob(fileList[last_file]) 
    print("try to download", blob)
    blob.download_to_filename(fileList[last_file])
    print("trigger retrain with", fileList[last_file])
    retrain(fileList[last_file])
    return 'retrained successfully with %s' % fileList[last_file]
