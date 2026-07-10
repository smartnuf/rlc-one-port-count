VENV_PYTHON := .venv/bin/python

.PHONY: setup install ensure-venv test lint supports bundles labelings reduced check print-env clean

setup:
	bash scripts/setup.sh

install: setup

ensure-venv:
	@test -x $(VENV_PYTHON) || (echo "Missing $(VENV_PYTHON). Run 'make setup' first." >&2; exit 1)

test:
	bash scripts/test.sh

lint:
	bash scripts/lint.sh

supports: ensure-venv
	$(VENV_PYTHON) -m rice supports --max-edges 8

bundles: ensure-venv
	$(VENV_PYTHON) -m rice bundles --max-r 3 --max-reactive 5

labelings: ensure-venv
	$(VENV_PYTHON) -m rice labelings --max-r 3 --max-reactive 5

reduced: ensure-venv
	$(VENV_PYTHON) -m rice reduced --max-r 2 --max-reactive 3

check:
	bash scripts/check.sh

print-env: ensure-venv
	$(VENV_PYTHON) -c 'import sys, networkx, pytest, rice; print("python", sys.executable); print("networkx", networkx.__version__); print("pytest", pytest.__version__); print("rice", rice.__file__)'

clean:
	bash scripts/clean.sh
