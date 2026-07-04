PYTHON ?= python3
VENV_PYTHON := .venv/bin/python

.PHONY: install ensure-venv test supports legacy-count legacy-generic check print-env clean

install:
	$(PYTHON) -m venv .venv
	$(VENV_PYTHON) -m pip install --upgrade pip setuptools wheel
	$(VENV_PYTHON) -m pip install -e ".[dev]"

ensure-venv:
	@test -x $(VENV_PYTHON) || (echo "Missing $(VENV_PYTHON). Run 'make install' first." >&2; exit 1)

test: ensure-venv
	$(VENV_PYTHON) -m pytest -q

supports: ensure-venv
	$(VENV_PYTHON) -m rlc_oneport_count supports --max-edges 8

legacy-count: ensure-venv
	$(VENV_PYTHON) -m rlc_oneport_count --mode lc --max-r 3 --max-reactive 5

legacy-generic: ensure-venv
	$(VENV_PYTHON) -m rlc_oneport_count --mode generic --max-r 3 --max-reactive 5

check: test supports legacy-count

print-env: ensure-venv
	$(VENV_PYTHON) - <<'PY'
import sys
import networkx
import pytest
import rlc_oneport_count
print("python", sys.executable)
print("networkx", networkx.__version__)
print("pytest", pytest.__version__)
print("rlc_oneport_count", rlc_oneport_count.__file__)
PY

clean:
	rm -rf .venv .pytest_cache build dist *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
