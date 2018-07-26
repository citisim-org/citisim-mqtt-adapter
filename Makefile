# -*- mode: makefile-gmake; coding: utf-8 -*-

all:
	python3 mqttAdapter.py citisim.config mqtt.config

.PHONY: tests
tests:
	nosetests3 tests/*.py

.PHONY: clean
clean:
	$(RM) -rf __pycache__
	$(RM) -rf tests/__pycache__
