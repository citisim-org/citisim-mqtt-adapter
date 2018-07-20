#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

import sys
import re
import Ice
import paho.mqtt.client as mqtt
import json
from libcitisim import Broker
from datetime import datetime

class MqttAdapter:
    def __init__(self, mqtt_client, citisim_broker, config):
        self.citisim_broker = citisim_broker
        self.mqtt_client = mqtt_client
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.config = config

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code "+str(rc))
        mqtt_topics = self.config['topic_list']
        mqtt_topics = mqtt_topics.split(',')
        for topic in mqtt_topics:
            print(topic.strip())
            client.subscribe(topic.strip())

    def on_message(self, client, userdata, msg):
        message = json.loads(msg.payload.decode())

        source = self.config['sensor_ids'][msg.topic]
        topic = self.config['icestorm_topics'][message['sensor']]

        message['timestamp'] = re.sub(r"[:]|([-](?!((\d{2}[:]\d{2})|(\d{4}))$))", '', message['timestamp'])
        message['timestamp'] = int(datetime.strptime(message['timestamp'], "%Y%m%dT%H%M%S%z").timestamp())
        meta = {'timestamp': message['timestamp']}

        #self.publish(source, topic, value, meta)

    def publish(self, source, topic, value, meta):
        publisher = self.citisim_broker.get_publisher(topic)
        publisher.publish(value, source=source, meta=meta)

    def run(self):
        self.mqtt_client.connect(self.config['broker_addr'])
        self.mqtt_client.loop_forever()


if __name__ == "__main__":
    citisim_broker = Broker(sys.argv[1])

    json_data=open(sys.argv[2]).read()
    config = json.loads(json_data)

    mqtt_client = mqtt.Client(config['client'])
    mqtt_2_citisim = MqttAdapter(mqtt_client, citisim_broker, config)
    mqtt_2_citisim.run()
