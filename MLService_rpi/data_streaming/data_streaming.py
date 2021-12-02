import pika
import sys
import time
import re, json
from datetime import datetime
import threading
import os,sys,inspect
con
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
class DataStreaming:
    def __init__(self, file_name):
        # Do not edit the init method.
        # Set the variables appropriately in the methods below.
        self.connection = None
        self.channel = None
        self.file_name = file_name
    
    def initialize_rabbitmq(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()
        self.stream_xchange = 'data_streaming'
        self.channel.exchange_declare(exchange=self.stream_xchange, exchange_type='x-consistent-hash')
        
    def close(self):
        # Do not edit this method
        self.channel.close()
        self.connection.close()

class InputStreaming(DataStreaming):
    def __init__(self, file_name):
        super().__init__(file_name)
                
    def publish_input(self):
        with open("{}/grouped_data/{}".format(parentdir, self.file_name), "r") as filel:
            data_lines = filel.readlines()
            for line_no in range(1, len(data_lines)):
                line = data_lines[line_no]
                line_arr = line.split(",")
                point_id = line_arr[0]
                data_point = [[float(i)] for i in line_arr[:6]]
                input_msg = {
                            "id": point_id,
                            "data_type": "input",
                            "value": data_point
                        }
                self.channel.basic_publish(exchange=self.stream_xchange, routing_key=input_msg["id"], body=json.dumps(input_msg))
                print(" [x] Sent input %r" % data_point)
                time.sleep(3)


class LabelStreaming(DataStreaming):
    def __init__(self, file_name):
        super().__init__(file_name)    
    
    def publish_label(self):
        with open("{}/grouped_data/{}".format(parentdir, self.file_name), "r") as filel:
            data_lines = filel.readlines()
            for line_no in range(1, len(data_lines)):
                line = data_lines[line_no]
                line_arr = line.split(",")
                point_id = line_arr[0]
                label = line_arr[6]
                label_msg = {
                    "id": point_id,
                    "data_type": "label",
                    "value": label
                }
                self.channel.basic_publish(exchange=self.stream_xchange, routing_key=label_msg["id"], body=json.dumps(label_msg))
                print(" [x] Sent label %r" % label_msg)
                time.sleep(3)


def stream_input(file_name):
    input_streaming = InputStreaming(file_name)
    input_streaming.initialize_rabbitmq()
    input_streaming.publish_input()
    input_streaming.close()

def stream_label(file_name):
    input_streaming = LabelStreaming(file_name)
    input_streaming.initialize_rabbitmq()
    input_streaming.publish_label()
    input_streaming.close()

def handle_streaming_data():
    print("parent", parentdir)
    list_of_files = os.listdir("{}/grouped_data".format(parentdir))
    now = datetime.now()
    today = now.strftime("%m_%d_%y")

    file_name = "{}_1161114004_122_.csv".format(today)
    t1 = threading.Thread(name='stream_input', target=stream_input, args=[file_name])
    t2 = threading.Thread(name='stream_label', target=stream_label, args=[file_name])
    t1.start()
    time.sleep(5)
    t2.start()

    t1.join()
    t2.join()