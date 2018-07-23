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

        source = self._get_source(msg.topic)
        icestorm_topic = self._get_icestorm_topic(message)
        value = self._get_value(message['value'])
        formatted_timestamp = self._format_timestamp(message['timestamp'])
        meta = self._get_meta(formatted_timestamp)

        self.publish(source, icestorm_topic, value, meta)

    def _get_source(self, topic):
        if topic not in self.config['sensor_ids']:
            return topic
        else:
            return self.config['sensor_ids'][topic]

    def _get_icestorm_topic(self, message):
        if message['sensor'] not in self.config['icestorm_topics']:
            return "Unconfigured"
        else:
            return self.config['icestorm_topics'][message['sensor']]

    def _get_value(self, value):
        return float(value)

    def _format_timestamp(self, timestamp):
        formatted_timestamp = re.sub(r"[:]|([-](?!((\d{2}[:]\d{2})|(\d{4}))$))", '', timestamp)
        formatted_timestamp = int(datetime.strptime(formatted_timestamp, "%Y%m%dT%H%M%S%z").timestamp())
        return formatted_timestamp

    def _get_meta(self, timestamp):
        return {"timestamp": timestamp}

    def publish(self, source, topic, value, meta):
        publisher = self.citisim_broker.get_publisher(topic)
        publisher.publish(value, source=source, meta=meta)

    def run(self):
        self.mqtt_client.connect(self.config['broker_addr'])
        self.mqtt_client.loop_forever()


if __name__ == "__main__":
    citisim_broker = Broker(sys.argv[1])

    json_config=open(sys.argv[2]).read()
    config = json.loads(json_config)

    mqtt_client = mqtt.Client(config['client'])
    mqtt_2_citisim = MqttAdapter(mqtt_client, citisim_broker, config)
    mqtt_2_citisim.run()
