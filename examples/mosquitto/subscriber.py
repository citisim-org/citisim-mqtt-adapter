#!/usr/bin/python3 -u
# -*- mode: python; coding: utf-8 -*-

import sys
from libcitisim import Broker


class Subscriber:
    def run(self, args):
        if len(args) != 3:
            print("Usage: {} <config> <source-id>".format(args[0]))
            return -1

        config = args[1]
        source = args[2]

        print("Subscribing to '{}'".format(source))
        broker = Broker(config)
        broker.subscribe_to_publisher(source, self.on_event)

        print("Waiting events...")
        broker.wait_for_events()

    def on_event(self, value, source, meta):
        print("Event arrived from '{}': {}".format(source, value))


if __name__ == "__main__":
    exit(Subscriber().run(sys.argv))
