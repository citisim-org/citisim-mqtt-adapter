
SHELL = /bin/bash
SRC   = $(shell pwd)/../../src

all:

broker:
	mosquitto -c mosquitto.conf

adapter:
	$(SRC)/mqtt_adapter.py pike.config mqtt-adapter.json

subscriber:
	./subscriber.py pike.config DD00735700000001

publish:
	mosquitto_pub -t "mqtt-adapter/examples/temperature" -m \
		"{\"value\": 12.5, \"timestamp\": $$(date +%s)}"

.PHONY: clean
clean:
	$(RM) *.db
