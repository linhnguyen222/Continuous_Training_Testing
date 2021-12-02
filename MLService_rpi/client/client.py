from os import pread
import time
import pika, requests
import json
import random
from datetime import datetime
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
class Client:

    def __init__(self):
        # Do not edit the init method.
        # Set the variables appropriately in the methods below.
        self.connection = None
        self.channel = None
    
    def initialize_rabbitmq(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()
        self.stream_xchange = 'data_streaming'
        self.pred_xchange = 'prediction'
        self.stream_queue = 'bts_data'
        channel.exchange_declare(exchange = self.stream_xchange, exchange_type='fanout')
        channel.queue_declare(queue = self.stream_queue, exclusive=True)
        channel.queue_bind(exchange=self.stream_xchange, queue=self.stream_queue)

        channel.exchange_declare(exchange = self.pred_xchange, exchange_type='x-consistent-hash')


    def handle_receiving_data(self, ch, method, properties, body):
        msg = json.loads(body.decode('utf-8'))
        print("received message", msg)
        # Extract label
        label = msg[6]
        print("label", label)
        # Extract input
        input = msg[:6]
        # data to be sent to api
        pred_message = {
            "inputs": json.dumps([input]),
            "type": "input"
        }
        # publish the new input to the prediction queue with type input
        channel.basic_publish(exchange='logs', routing_key='', body=json.dumps(vars(pred_message)))

        # publish the new label to the prediction queue with type observation
        label_message = {
            "inputs": json.dumps([input]),
            "type": "label"
        }
        # sending post request and saving response as response object
        # response = requests.post(url = API_ENDPOINT, data = param)
        # result = response.json()
        # extracting response text 
        # print("result", result)
        # now = datetime.now()
        # time = now.strftime("%m_%d_%y")
        # with open('{}/Result/{}.csv'.format(parentdir, time), 'a') as f:
        #     new_line = "{input},{label},{pred}".format(input=input, label=label, pred=result["prediction_result"])
        #     print(new_line)
        #     f.write(new_line + '\n')

    def start_consuming(self):
        channel.basic_consume(queue=self.stream_queue, on_message_callback=handle_receiving_data, auto_ack=True)
        channel.start_consuming()

def handle_client():

    print("ahoy")


