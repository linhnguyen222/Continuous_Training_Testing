# from flask import Flask, request
import tflite_runtime.interpreter as tflite
import numpy as np
import json
import time
import pika, requests
import json
import random
from datetime import datetime
import os,sys,inspect
import threading
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)


TIMEOUT_TIME_SECONDS = 60

class StaticServer:

    def __init__(self):
        # Do not edit the init method.
        # Set the variables appropriately in the methods below.
        self.connection = None
        self.channel = None
        self.result = {}
        self.interpreter = tflite.Interpreter(model_path="{}/LSTM_single_series/LSTM_single_series.tflite".format(parentdir))
        self.interpreter.allocate_tensors()
        # Get input and output tensors.
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.last_received_msg = datetime.now()

    def watchdog_thread(self):
        while True:
            time.sleep(TIMEOUT_TIME_SECONDS)

            now = datetime.now()
            diff = now - self.last_received_msg

            print("Watchdog thread, now", now, "watching", self.last_received_msg, "diff", diff, "-", diff.total_seconds(), "s")

            if diff.total_seconds() >= TIMEOUT_TIME_SECONDS:
                print("Shutting down due to timeout")
                print("result", self.result)
                self.connection.add_callback_threadsafe(self.close)
                break

    def close(self):
        self.channel.close()
        self.connection.close()

    def initialize_rabbitmq(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost')) 
        self.channel = self.connection.channel() 

        self.stream_xchange = 'data_streaming'
        self.stream_queue = 'bts_data'
        # self.stream_queue = 'bts_data2'

        self.channel.queue_declare(queue=self.stream_queue, durable=True)
        # self.channel.queue_declare(queue=self.stream_queue2, durable=True)
        self.channel.exchange_declare(exchange = self.stream_xchange, exchange_type='x-consistent-hash')

        self.channel.queue_bind(exchange=self.stream_xchange, queue=self.stream_queue, routing_key="2")
        # self.channel.queue_bind(exchange=self.stream_xchange, queue=self.stream_queue2, routing_key="2")


    def handle_receiving_data(self, ch, method, properties, body):
        self.last_received_msg = datetime.now()
        msg = json.loads(body.decode('utf-8'))
        print("received message", msg)
        msg_id = msg["id"]
        if msg_id not in self.result:
            self.result[msg_id] = {}
        if msg["data_type"] == "input":
            input = [msg["value"]]
            input_data = np.array(input, dtype=np.float32)
            self.interpreter.set_tensor(self.input_details[0]['index'], input_data)

            self.interpreter.invoke()
            # The function `get_tensor()` returns a copy of the tensor data.
            # Use `tensor()` in order to get a pointer to the tensor.
            output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
            prediction_result = output_data[0][0][0]
            self.result[msg_id]["input"] = input
            self.result[msg_id]["output"] = prediction_result
        elif msg["data_type"] == "label" and "input" in self.result[msg_id]: 
            label_id = msg["id"]
            self.result[msg_id]["label"] = msg["value"]
            now = datetime.now()
            today = now.strftime("%m_%d_%y")
            with open('{}/Result/{}.csv'.format(parentdir, today), 'a') as f:
                print("result", self.result)
                new_line = "{input},{label},{pred}".format(input=self.result[msg_id]["input"], label=self.result[msg_id]["label"], pred=self.result[msg_id]["output"])
                print(new_line)
                f.write(new_line + '\n')
            self.result.pop(msg_id)
        else:   
            self.channel.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
            return
        self.channel.basic_ack(method.delivery_tag)

    def start_consuming(self):
        print("comsuming")
        self.channel.basic_consume(queue=self.stream_queue, on_message_callback=self.handle_receiving_data)
        self.channel.start_consuming()

def handle_server():
    print("ahoy")
    s_server = StaticServer()
    t1 = threading.Thread(name='watchdog_thread', target=s_server.watchdog_thread)
    t1.start()
    s_server.initialize_rabbitmq()
    s_server.start_consuming()
    t1.join()


