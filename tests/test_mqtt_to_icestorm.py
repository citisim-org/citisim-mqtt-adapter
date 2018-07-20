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

from libcitisim import MetadataHelper, MetadataField, SmartObject
import libcitisim
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
        self.mqttClient = mqtt.Client('CitisimUCLM')

        # the real subject under testing
        self.mqttAdapter = MqttAdapter()

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
        self.topic_name='Temperature'

        self.servant = Mimic(Spy, SmartObject.AnalogSink)
        self.proxy = self._adapter_add(self.servant)
        self._subscribe(self.topic_name, self.proxy)

    def test_get_event(self):
        # get an event from IceStorm originated in mqtt broker
        msg = mqtt.MQTTMessage(mid=0, topic=b'meshliumf958/SCP4/PRES')
        print(msg.topic)
        msg.payload = b'{\r\n  "id": "186897",\r\n  "id_wasp": "SCP4", \r\n  "id_secret": "751C67057C105442",\r\n  "sensor": "TC",\r\n  "value": "25.6",\r\n  "timestamp": "2018-07-19T11:01:41+03:00"\r\n}'
        print(msg.payload)

        mqttAdapter.on_message(client=self.mqttClient, userdata=None, msg=msg)
        assert_that(self.servant.notify,
                    called().
                    with_args(25.6, anything() ,anything(),anything()).
                    async(timeout=2))
