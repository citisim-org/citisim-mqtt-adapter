#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

import sys
import re
import Ice
import paho.mqtt.client as mqtt
import json
import logging
from functools import lru_cache
from libcitisim import Broker
from datetime import datetime

logging.getLogger().setLevel(logging.INFO)


class MqttAdapter:
    def __init__(self, mqtt_client, citisim_broker, config):
        self.citisim_broker = citisim_broker
        self.mqtt_client = mqtt_client
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.config = config

    def run(self):
        try:
            logging.info("MQTT server: " + self.config['broker_addr'])
            self.mqtt_client.connect(self.config['broker_addr'])
            self.mqtt_client.loop_forever()
        except KeyboardInterrupt:
            self.mqtt_client.disconnect()
            del self.citisim_broker

    def on_connect(self, client, userdata, flags, rc):
        logging.info("Connected with result code " + str(rc))
        mqtt_topics = self.config['mqtt_topics']
        for topic in mqtt_topics:
            client.subscribe(topic.strip())
            logging.info("Subscribed to MQTT: " + topic)
        logging.info("Ready, waiting events...")

    def on_message(self, client, userdata, msg):
        sensor = self._get_sensor(msg.topic)
        if sensor is None:
            logging.warning(" Unknown MQTT Topic: '{}', discarding message".format(
                msg.topic))
            return

        source = sensor.get("source")
        transducer_type = sensor.get("type")
        if source in (None, "") or transducer_type in (None, ""):
            logging.warning(" Invalid sensor configuration: '{}', discarding message".format(
                msg.topic))
            return

        message = json.loads(msg.payload.decode())
        value = float(message['value'])
        timestamp = self._format_timestamp(message['timestamp'])
        meta = self._get_meta(timestamp)

        # self._print_message_info(msg)
        self._publish(source, transducer_type, value, meta)

    def _publish(self, source, type_, value, meta):
        publisher = self._get_publisher(source, type_)
        publisher.publish(value, meta=meta)

    @lru_cache(maxsize=128)
    def _get_publisher(self, source, type_):
        return self.citisim_broker.get_publisher(source, type_)

    def _get_sensor(self, mqtt_topic):
        return self.config["sensors"].get(mqtt_topic)

    def _format_timestamp(self, timestamp):
        formatted_timestamp = re.sub(
            r"[:]|([-](?!((\d{2}[:]\d{2})|(\d{4}))$))", '', timestamp)
        formatted_timestamp = int(datetime.strptime(
            formatted_timestamp, "%Y%m%dT%H%M%S%z").timestamp())
        return formatted_timestamp

    def _get_meta(self, timestamp):
        return {"timestamp": timestamp}

    def _print_message_info(self, msg):
        print("\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n")
        print("New MQTT message received:")
        print("MQTT topic: " + msg.topic)
        print("Message: \n" + msg.payload.decode())
        print("\n")


if __name__ == "__main__":
    citisim_broker = Broker(sys.argv[1])

    json_config = open(sys.argv[2]).read()
    config = json.loads(json_config)
    mqtt_client = mqtt.Client(config['client'])

    mqtt_2_citisim = MqttAdapter(mqtt_client, citisim_broker, config)
    mqtt_2_citisim.run()
