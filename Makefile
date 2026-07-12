VENV_PYTHON := .venv/bin/python

.PHONY: setup test lint check validate-changed count-supports count-bundle-types count-bundle-sets count-assignments count-assigned-supports count-networks clean install

setup:
	./scripts/setup.sh

test:
	$(VENV_PYTHON) -m pytest -q

lint:
	./scripts/lint.sh

count-supports:
	$(VENV_PYTHON) -m rice count supports --max-support-edges 8

count-bundle-types:
	$(VENV_PYTHON) -m rice count bundle-types

count-bundle-sets:
	$(VENV_PYTHON) -m rice count bundle-sets --profile main

count-assignments:
	$(VENV_PYTHON) -m rice count assignments --profile main

count-assigned-supports:
	$(VENV_PYTHON) -m rice count assigned-supports --profile main

count-networks:
	$(VENV_PYTHON) -m rice count networks --profile golden

check:
	./scripts/check.sh

validate-changed:
	$(VENV_PYTHON) scripts/validate_changes.py

clean:
	./scripts/clean.sh

install: setup
