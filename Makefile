# -*- mode: makefile-gmake; coding: utf-8 -*-

export PYTHONPATH=$$(pwd)/src

all:
	python3 src/mqtt_adapter.py example/citisim.config example/mqtt.json

.PHONY: tests
tests:
	$(RM) -fr /tmp/test-mqttadapter-is-db
	mkdir -p /tmp/test-mqttadapter-is-db
	nosetests3 -s tests/*.py

.PHONY: clean
clean:
	find -name "__pycache__" | xargs $(RM) -r

