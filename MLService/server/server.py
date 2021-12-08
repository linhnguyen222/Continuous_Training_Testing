# from flask import Flask, request
import tflite_runtime.interpreter as tflite
import numpy as np
import json
import pika
import json
import pandas as pd
from datetime import datetime
import os,sys,inspect
from google.cloud import storage
import requests
from Retrain.retrain import trigger_func_call
# import tensorflow as tf
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
TIMEOUT_TIME_SECONDS = 60
AMQP_URL = os.getenv("AMQP_URL", "amqps://kattclvg:phyP2rUTThSnUo9aaIaVRysG-E4Ei5c7@hawk.rmq.cloudamqp.com/kattclvg")

class StaticServer:

    def __init__(self):
        # Do not edit the init method.
        # Set the variables appropriately in the methods below.
        self.connection = None
        self.channel = None
        self.result = {}
        # self.interpreter = tf.lite.Interpreter(model_path="{}/LSTM_single_series/LSTM_single_series.tflite".format(parentdir))
        self.interpreter = tflite.Interpreter(model_path="{}/LSTM_single_series/LSTM_single_series.tflite".format(parentdir))
        self.interpreter.allocate_tensors()
        # Get input and output tensors.
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.last_received_msg = datetime.now()
        self.gsclient = storage.Client()
        self.buffer = np.zeros((7, 1), dtype=np.float32)
        self.pointer = 0
        self.data = {}
        with open("./LSTM_single_series/param.json") as f:
            self.data = json.load(f)

    def initialize_rabbitmq(self, param):
        # self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost')) 
        self.param = pika.URLParameters(param)
        self.connection = pika.BlockingConnection(self.param) 
    #     self.connection = pika.BlockingConnection(
    # pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel() 

        self.stream_xchange = 'data_streaming_fanout'
        self.stream_queue = 'bts_data'
# self.channel.queue_declare(queue=self.stream_queue, durable=True)
        result = self.channel.queue_declare(queue="", durable=True)
        self.queue_name = result.method.queue

        self.channel.exchange_declare(exchange = self.stream_xchange, exchange_type='fanout')

        self.channel.queue_bind(exchange=self.stream_xchange, queue=self.queue_name)
        # self.channel.queue_bind(exchange=self.stream_xchange, queue=self.stream_queue2, routing_key="2")
    def update_buffer(self,new_val):
        # print("new val", new_val)
        if self.pointer <= 7:
            # self.buffer = self.buffer[:6]
            self.buffer = np.concatenate((np.array([[new_val]], dtype=np.float32),self.buffer[:6]))
        if self.pointer < 7:
            self.pointer= self.pointer + 1
 
    def input_preprocessing(self):
        # print("buffer", self.buffer)
        # Example input
        # [[5693281222.0], [11.0], [1161114004.0], [122.0], [1.493254874e+18], [-0.47443986275555555]]
        with open("./LSTM_single_series/param.json") as f:
            # print("buffer", self.buffer)
            serial_data = pd.DataFrame(self.buffer, columns=["norm_value"])
            serial_data['norm_1'] = serial_data['norm_value'].shift(1)
            serial_data['norm_2'] = serial_data['norm_value'].shift(2)
            serial_data['norm_3'] = serial_data['norm_value'].shift(3)
            serial_data['norm_4'] = serial_data['norm_value'].shift(4)
            serial_data['norm_5'] = serial_data['norm_value'].shift(5)
            serial_data['norm_6'] = serial_data['norm_value'].shift(6)
            serial_data = serial_data.drop(["norm_value"], axis=1)
            # print("serial", serial_data)
            serial_np = serial_data.iloc[6].to_numpy()
            return [[val] for val in serial_np]

    def handle_receiving_data(self, ch, method, properties, body):
        self.last_received_msg = datetime.now()
        msg = json.loads(body.decode('utf-8'))
        print("received message", msg)
        msg_id = msg["id"] if "id" in msg else None
        if msg_id and msg_id not in self.result:
            self.result[msg_id] = {}
        if msg["data_type"] == "input":
            input = msg["value"]
            input_data = np.array(input, dtype=np.float32)
            # Need to run input preprocessing
            input_data = self.input_preprocessing()
            # print("input data", input_data)
            self.interpreter.set_tensor(self.input_details[0]['index'], [input_data])
            self.interpreter.invoke()
            # The function `get_tensor()` returns a copy of the tensor data.
            # Use `tensor()` in order to get a pointer to the tensor.
            output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
            prediction_result = output_data[0][0][0]
            self.result[msg_id]["input"] = input
            self.result[msg_id]["output"] = prediction_result
            # self.channel.basic_ack(method.delivery_tag)
        elif msg["data_type"] == "label" and "input" in self.result[msg_id]: 
            self.result[msg_id]["raw_label"] = msg["value"]
            label = (msg["value"] - self.data["mean_val"])/self.data["max_val"]
            self.result[msg_id]["label"] = label
            self.update_buffer(label)
            # now = datetime.now()
            send_date = msg["send_date"]
            # today = now.strftime("%m_%d_%y")
            print("opening", '{}/Result/{}.csv'.format(parentdir, send_date))
            input_str = ", ".join(["{}".format(x) for x in self.result[msg_id]["input"]])
            with open('{}/Result/{}.csv'.format(parentdir, send_date), 'a') as f:
                # print("result", self.result)
                new_line = "{input}, {raw_label}, {label}, {pred}".format(input=input_str, raw_label= self.result[msg_id]["raw_label"], label=self.result[msg_id]["label"], pred=self.result[msg_id]["output"])
                print("new line", new_line)
                f.write(new_line)
                f.write("\n")
            self.result.pop(msg_id)
            # self.channel.basic_ack(method.delivery_tag)
        if msg["data_type"] == "end-of-file": 
            bucket = self.gsclient.get_bucket('bts-data-atss')
            file_to_upload = "Result/{}.csv".format(msg["send_date"])
            if os.path.exists(file_to_upload):
                print("UPLOADING", file_to_upload)
                blob = bucket.blob(file_to_upload)
                blob.upload_from_filename(file_to_upload)
                print("RESULT UPLOADED")
                # Trigger retrain
                # Step1: calculate the msg of the day calculation
                daily_prediction_result = pd.read_csv(file_to_upload, 
                    names=["id","station_id","parameter_id","unix_timestamp","norm_time","value", "label", "prediction"])
                y_true = np.array(daily_prediction_result["label"])
                y_pred = np.array(daily_prediction_result["prediction"])
                MSE = np.square(np.subtract(y_true,y_pred)).mean()
                if MSE > 0.1:
                    # API_ENDPOINT = "http://0.0.0.0:8080/retrain"
                    # param = {
                    # "file_name": json.dumps("Result/12_06_21.csv")
                    # }
                    # # sending post request and saving response as response object
                    # response = requests.post(url = API_ENDPOINT, data = param)

                    # # result = response.json()
                    # # extracting response text 
                    # print("retrain-response",response)
                    print("Trigger retrain")
                    trigger_func_call(file_to_upload)
                    print("Retrained done")
                    self.interpreter = tflite.Interpreter(model_path="{}/LSTM_single_series/LSTM_single_series.tflite".format(parentdir))
                    self.interpreter.allocate_tensors()
                    # Get input and output tensors.
                    self.input_details = self.interpreter.get_input_details()
                    self.output_details = self.interpreter.get_output_details()
                    print("Model updated!")
                    with open("{}/LSTM_single_series/param.json".format(parentdir)) as f:
                        self.data = json.load(f)
                    print("Parameter updated!")
            # self.channel.basic_ack(method.delivery_tag)
            
        else:   
            self.channel.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
            return
        print("come here")
        self.channel.basic_ack(method.delivery_tag)
        print("ack")

    def start_consuming(self):
        self.channel.basic_consume(queue=self.queue_name, on_message_callback=self.handle_receiving_data)
        self.channel.start_consuming()

def handle_server():
    print("Starting BTS server ...")
    s_server = StaticServer()
    # t1 = threading.Thread(name='watchdog_thread', target=s_server.watchdog_thread)
    # t1.start()
    s_server.initialize_rabbitmq(AMQP_URL)
    s_server.start_consuming()
    # t1.join()


