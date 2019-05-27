# -*- coding: utf-8; mode: python -*-

import os
from time import time
from subprocess import Popen, PIPE
from select import select
from io import StringIO
import contextlib
import shutil
import Ice
import IceStorm
from doublex import (
    assert_that, called, method_returning, method_raising, Mimic, Spy
)
from hamcrest import (
    calling, raises, is_not, anything, close_to, greater_than, equal_to
)
from unittest import TestCase

import mqttAdapter

from libcitisim import MetadataHelper, MetadataField, SmartObject, Broker
import paho.mqtt.client as mqtt
import json

class EventsMixin:
    @classmethod
    def setUpClass(cls):
        pwd = os.path.dirname(__file__)

        db_path = "/tmp/test-mqttadapter-is-db"
        if os.path.exists(db_path):
            shutil.rmtree(db_path)
        os.makedirs(db_path)

        cls.pwd = pwd
        cls.config = os.path.join(pwd, "tests.config")
        cmd = "icebox --Ice.Config=" + cls.config
        cls.is_server = Popen(cmd.split(), cwd=pwd, stdout=PIPE)

        pipe = select([cls.is_server.stdout], [], [], 3)[0]
        assert len(pipe), "IceStorm service did not launch correctly"
        assert pipe[0].readline() == b"IceStorm is ready\n"

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "is_server"):
            cls.is_server.terminate()
            cls.is_server.kill()

    def setUp(self):
        # for testing purposes only
        args = ["", "--Ice.Config=" + self.config]
        self.ic = Ice.initialize(args)
        self.adapter = self.ic.createObjectAdapterWithEndpoints(
            'adapter', 'tcp -h 127.0.0.1')
        self.adapter.activate()
        self.mqtt_client = mqtt.Client('CitisimUCLM')
        self.citisim_broker = Broker(self.config)
        json_config = open(os.path.join(self.pwd, 'mqtt.test.config')).read()
        self.config = json.loads(json_config)
        # the real subject under testing
        self.mqttAdapter = mqttAdapter.MqttAdapter(self.mqtt_client, self.citisim_broker, self.config)

    def _get_topic(self, name):
        manager = self.ic.propertyToProxy("TopicManager.Proxy")
        manager = IceStorm.TopicManagerPrx.checkedCast(manager)
        try:
            return manager.retrieve(name)
        except IceStorm.NoSuchTopic:
            return manager.create(name)

    def _subscribe(self, topic_name, proxy):
        topic = self._get_topic(topic_name)
        topic.subscribeAndGetPublisher({}, proxy)

    def _adapter_add(self, servant):
        return self.adapter.addWithUUID(servant)

class MqttAdapter(EventsMixin, TestCase):
    def setUp(self):
        EventsMixin.setUp(self)

        self.icestorm_topic_name='Temperature'

        self.servant = Mimic(Spy, SmartObject.AnalogSink)
        self.proxy = self._adapter_add(self.servant)
        self._subscribe(self.icestorm_topic_name, self.proxy)

    def test_get_event_with_value_and_timestamp(self):
        # get an event from IceStorm originated in mqtt broker
        self.mqtt_msg = mqtt.MQTTMessage(mid=0, topic=b'meshliumf958/SCP4/TC')
        self.mqtt_msg.payload = ('{\r\n  "id": "186897",\r\n  "id_wasp": "SCP4", \r\n '
                                '"id_secret": "751C67057C105442",\r\n  '
                                '"sensor": "TC",\r\n  "value": "25.6",\r\n  '
                                '"timestamp": "2018-07-19T11:01:41+03:00"\r\n}').encode()
        self.mqtt_msg.payload = self.mqtt_msg.payload
        self.formatted_timestamp = '1531987301'

        self.mqttAdapter.on_message(client=self.mqtt_client, userdata=None, msg=self.mqtt_msg)
        meta = {SmartObject.MetadataField.Timestamp: self.formatted_timestamp}

        assert_that(self.servant.notify,
                    called().
                    with_args(close_to(25.6, 0.000001), 'FF00000100000023', meta, anything()).
                    async(timeout=2))

    def test_get_event_from_unconfigured_sensor_id(self):
        self.mqtt_msg = mqtt.MQTTMessage(mid=0, topic=b'meshliumf958/SCP5/TC')
        self.mqtt_msg.payload = ('{\r\n  "id": "186897",\r\n  "id_wasp": "SCP5", \r\n '
                                '"id_secret": "751C67057C105442",\r\n  '
                                '"sensor": "TC",\r\n  "value": "25.6",\r\n  '
                                '"timestamp": "2018-07-19T11:01:41+03:00"\r\n}').encode()
        self.mqtt_msg.payload = self.mqtt_msg.payload
        self.formatted_timestamp = '1531987301'

        self.mqttAdapter.on_message(client=self.mqtt_client, userdata=None, msg=self.mqtt_msg)
        meta = {SmartObject.MetadataField.Timestamp: self.formatted_timestamp}

        assert_that(self.servant.notify,
                    called().
                    with_args(close_to(25.6, 0.000001), 'MISSING_ID: meshliumf958/SCP5/TC', meta, anything()).
                    async(timeout=2))

    def test_get_event_from_unconfigured_sensor_magnitude(self):
        self.icestorm_topic_name_unconfigured="Unconfigured"
        self.servant_unconfigured = Mimic(Spy, SmartObject.AnalogSink)
        self.proxy_unconfigured = self._adapter_add(self.servant_unconfigured)
        self._subscribe(self.icestorm_topic_name_unconfigured, self.proxy_unconfigured)

        self.mqtt_msg = mqtt.MQTTMessage(mid=0, topic=b'meshliumf958/SCP4/HUM')
        self.mqtt_msg.payload = ('{\r\n  "id": "186897",\r\n  "id_wasp": "SCP4", \r\n '
                                '"id_secret": "751C67057C105442",\r\n  '
                                '"sensor": "HUM",\r\n  "value": "25.6",\r\n  '
                                '"timestamp": "2018-07-19T11:01:41+03:00"\r\n}').encode()
        self.mqtt_msg.payload = self.mqtt_msg.payload
        self.formatted_timestamp = '1531987301'

        self.mqttAdapter.on_message(client=self.mqtt_client, userdata=None, msg=self.mqtt_msg)
        meta = {SmartObject.MetadataField.Timestamp: self.formatted_timestamp}

        assert_that(self.servant_unconfigured.notify,
                    called().
                    with_args(close_to(25.6, 0.000001), 'MISSING_ID: meshliumf958/SCP4/HUM', meta, anything()).
                    async(timeout=2))
