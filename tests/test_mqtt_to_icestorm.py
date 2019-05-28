# -*- coding: utf-8; mode: python -*-

import os
import contextlib
import shutil
import Ice
import IceStorm
import paho.mqtt.client as mqtt
import json

from time import time
from subprocess import Popen, PIPE
from select import select
from io import StringIO
from doublex import (
    assert_that, called, method_returning, method_raising, Mimic, Spy
)
from hamcrest import (
    calling, raises, is_not, anything, close_to, greater_than, equal_to
)
from unittest import TestCase

from mqtt_adapter import MqttAdapter

from libcitisim import MetadataHelper, MetadataField, SmartObject, Broker
from libcitisim.util import EventsMixin as UtilEventMixin


class EventsMixin(UtilEventMixin):
    pwd = os.path.dirname(__file__)
    config = os.path.join(pwd, "tests.config")

    def setUp(self):
        self._ice_setup()
        self.citisim_broker = Broker(self.config)
        self.mqtt_client = mqtt.Client('CitisimUCLM')

        with open(os.path.join(self.pwd, 'mqtt.test.config')) as cfg:
            self.config = json.loads(cfg.read())

        self.mqtt_adapter = MqttAdapter(
            self.mqtt_client, self.citisim_broker, self.config)
        print("- instance setup OK")

    def tearDown(self):
        self._ice_finish()
        self.citisim_broker.property_manager.clear()


class AnalogSinkI(SmartObject.AnalogSink):
    def __init__(self, servant):
        self.servant = servant

    def notify(self, *args, **kwargs):
        self.servant.notify(*args, **kwargs)


class MqttAdapterTests(EventsMixin, TestCase):
    def setUp(self):
        EventsMixin.setUp(self)

        self.icestorm_topic_name = 'FF00000100000023.private'

        self.servant = Mimic(Spy, SmartObject.AnalogSink)
        self.proxy = self._adapter_add(AnalogSinkI(self.servant))
        self._subscribe(self.icestorm_topic_name, self.proxy)

    def test_get_event_with_value_and_timestamp(self):
        # get an event from IceStorm originated in mqtt broker
        self.mqtt_msg = mqtt.MQTTMessage(mid=0, topic=b'meshliumf958/SCP4/TC')
        self.mqtt_msg.payload = (
            '{\r\n  "id": "186897",\r\n  "id_wasp": "SCP4", \r\n '
            '"id_secret": "751C67057C105442",\r\n  '
            '"sensor": "TC",\r\n  "value": "25.6",\r\n  '
            '"timestamp": "2018-07-19T11:01:41+03:00"\r\n}').encode()
        self.mqtt_msg.payload = self.mqtt_msg.payload
        self.formatted_timestamp = '1531987301'

        self.mqtt_adapter.on_message(client=self.mqtt_client, userdata=None, msg=self.mqtt_msg)
        meta = {SmartObject.MetadataField.Timestamp: self.formatted_timestamp}

        assert_that(self.servant.notify,
            called().
            with_args(close_to(25.6, 0.000001), 'FF00000100000023', meta, anything()).
            async(timeout=2))

    def test_event_from_unconfigured_sensor_id(self):
        self.mqtt_msg = mqtt.MQTTMessage(mid=0, topic=b'meshliumf958/SCP5/TC')
        self.mqtt_msg.payload = (
            '{\r\n  "id": "186897",\r\n  "id_wasp": "SCP5", \r\n '
            '"id_secret": "751C67057C105442",\r\n  '
            '"sensor": "TC",\r\n  "value": "25.6",\r\n  '
            '"timestamp": "2018-07-19T11:01:41+03:00"\r\n}').encode()
        self.mqtt_msg.payload = self.mqtt_msg.payload
        self.formatted_timestamp = '1531987301'

        self.mqtt_adapter.on_message(client=self.mqtt_client, userdata=None, msg=self.mqtt_msg)
        meta = {SmartObject.MetadataField.Timestamp: self.formatted_timestamp}

        assert_that(self.servant.notify, is_not(called()))

    def test_event_from_unconfigured_sensor_magnitude(self):
        self.icestorm_topic_name_unconfigured="Unconfigured"
        self.servant_unconfigured = Mimic(Spy, SmartObject.AnalogSink)
        self.proxy_unconfigured = self._adapter_add(self.servant_unconfigured)
        self._subscribe(self.icestorm_topic_name_unconfigured, self.proxy_unconfigured)

        self.mqtt_msg = mqtt.MQTTMessage(mid=0, topic=b'meshliumf958/SCP4/HUM')
        self.mqtt_msg.payload = (
            '{\r\n  "id": "186897",\r\n  "id_wasp": "SCP4", \r\n '
            '"id_secret": "751C67057C105442",\r\n  '
            '"sensor": "HUM",\r\n  "value": "25.6",\r\n  '
            '"timestamp": "2018-07-19T11:01:41+03:00"\r\n}').encode()
        self.mqtt_msg.payload = self.mqtt_msg.payload
        self.formatted_timestamp = '1531987301'

        self.mqtt_adapter.on_message(client=self.mqtt_client, userdata=None, msg=self.mqtt_msg)
        meta = {SmartObject.MetadataField.Timestamp: self.formatted_timestamp}

        assert_that(self.servant_unconfigured.notify, is_not(called()))

