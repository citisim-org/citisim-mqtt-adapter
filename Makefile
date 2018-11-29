# -*- mode: makefile-gmake; coding: utf-8 -*-

all:
	python3 ./mqttAdapter/__init__.py ./mqttAdapter/citisim.config ./mqttAdapter/mqtt.config

.PHONY: tests
tests:
	nosetests3 tests/*.py

.PHONY: clean
clean:
	$(RM) -rf __pycache__
	$(RM) -rf tests/__pycache__
