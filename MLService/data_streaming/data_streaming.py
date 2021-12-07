import pika
import re, json
from datetime import datetime
import time
# from dotenv import dotenv_values
import threading
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
# config = dotenv_values("{}/.env".format(parentdir))
AMQP_URL = os.getenv("AMQP_URL", "amqps://kattclvg:phyP2rUTThSnUo9aaIaVRysG-E4Ei5c7@hawk.rmq.cloudamqp.com/kattclvg")


class DataStreaming:
    def __init__(self, file_name, send_date):
        # Do not edit the init method.
        # Set the variables appropriately in the methods below.
        self.connection = None
        self.channel = None
        self.file_name = file_name
        self.send_date = send_date
    
    def initialize_rabbitmq(self, param):
        print("param", param)
        # self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost')) 
        self.param = pika.URLParameters(param)
        self.connection = pika.BlockingConnection(self.param) 
        # pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        # 
        self.channel = self.connection.channel()
        self.stream_xchange = 'data_streaming_fanout'
        self.channel.exchange_declare(exchange=self.stream_xchange, exchange_type='fanout')
    def close(self):
        # Do not edit this method
        self.channel.close()
        self.connection.close()

class InputStreaming(DataStreaming):
    def __init__(self, file_name, send_date):
        super().__init__(file_name, send_date)
                
    def publish_input(self):
        print("publishing data", self.file_name)
        with open("{}/grouped_data/{}".format(parentdir, self.file_name), "r") as filel:
            data_lines = filel.readlines()
            for line_no in range(1, len(data_lines)):
                line = data_lines[line_no]
                line_arr = line.split(",")
                line_arr.pop(1)
                point_id = line_arr[0]
                data_point = [float(i) for i in line_arr[:6]]
                input_msg = {
                            "id": point_id,
                            "data_type": "input",
                            "value": data_point,
                            "send_date": self.send_date
                        }
                self.channel.basic_publish(exchange=self.stream_xchange, routing_key="", body=json.dumps(input_msg))
                print(" [x] Sent input %r" % data_point)
                # time.sleep(3)


class LabelStreaming(DataStreaming):
    def __init__(self, file_name, send_date):
        super().__init__(file_name, send_date)    
    
    def publish_label(self):
        with open("{}/grouped_data/{}".format(parentdir, self.file_name), "r") as filel:
            data_lines = filel.readlines()
            for line_no in range(1, len(data_lines)):
                line = data_lines[line_no]
                line_arr = line.split(",")
                point_id = line_arr[0]
                label = line_arr[1]
                label_msg = {
                    "id": point_id,
                    "data_type": "label",
                    "value": float(label.strip()),
                    "send_date": self.send_date
                }
                self.channel.basic_publish(exchange=self.stream_xchange, routing_key="", body=json.dumps(label_msg))
                print(" [x] Sent label %r" % label_msg)
                # time.sleep(3)
            end_of_file_msg = {
                    "data_type": "end-of-file",
                    "send_date": self.send_date
            }
            self.channel.basic_publish(exchange=self.stream_xchange, routing_key="", body=json.dumps(end_of_file_msg))
            print(" [x] Sent end of file notice %r" % end_of_file_msg)
            # time.sleep(3)


def stream_input(file_name, send_date):
    input_streaming = InputStreaming(file_name, send_date)
    input_streaming.initialize_rabbitmq(AMQP_URL)
    input_streaming.publish_input()
    input_streaming.close()

def stream_label(file_name, send_date):
    input_streaming = LabelStreaming(file_name, send_date)
    input_streaming.initialize_rabbitmq(AMQP_URL)
    input_streaming.publish_label()
    input_streaming.close()

def handle_streaming_data():
    print("parent", parentdir)
    now = datetime.now()
    send_date = now.strftime("%m_%d_%y")

    file_name = "{}_1161114004_122_.csv".format(send_date)
    t1 = threading.Thread(name='stream_input', target=stream_input, args=[file_name, send_date])
    t2 = threading.Thread(name='stream_label', target=stream_label, args=[file_name, send_date])
    t1.start()
    time.sleep(4)
    t2.start()

    t1.join()
    t2.join()