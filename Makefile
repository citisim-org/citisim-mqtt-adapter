# -*- mode: makefile-gmake; coding: utf-8 -*-

all:
	python3 ./mqttAdapter/__init__.py ./mqttAdapter/citisim.config ./mqttAdapter/mqtt.config

.PHONY: tests
tests:
	$(RM) -fr /tmp/test-mqttadapter-is-db
	mkdir -p /tmp/test-mqttadapter-is-db
	nosetests3 -s tests/*.py

.PHONY: clean
clean:
	$(RM) -rf __pycache__
	$(RM) -rf tests/__pycache__
	$(RM) -rf mqttAdapter/__pycache__
