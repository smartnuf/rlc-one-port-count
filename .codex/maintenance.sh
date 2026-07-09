#!/usr/bin/env bash
set -Eeuo pipefail

cd "${CODEX_REPO_DIR:-$PWD}"

echo "Codex maintenance for rice"
echo "Repository: $(pwd)"

if [ ! -x .venv/bin/python ]; then
    echo "No usable .venv found; running full setup."
    bash .codex/setup.sh
    exit 0
fi

# Cached environments may reuse a venv created against a previous checkout. The
# package itself is editable, but refreshing without dependency resolution keeps
# this maintenance step from trying to fetch packages during restricted phases.
.venv/bin/python -m pip install --no-build-isolation --no-deps -e .

echo "Environment smoke test:"
.venv/bin/python - <<'PY'
import sys
import networkx
import pytest
import rice
print("python", sys.executable)
print("networkx", networkx.__version__)
print("pytest", pytest.__version__)
print("rice", rice.__file__)
PY

.venv/bin/python -m pytest -q

echo "Codex maintenance complete. Use .venv/bin/python or make test/check for task commands."
