#!/usr/bin/env bash
set -Eeuo pipefail

cd "${CODEX_REPO_DIR:-$PWD}"

echo "Codex setup for rice"
echo "Repository: $(pwd)"

if command -v python3.12 >/dev/null 2>&1; then
    PYTHON_BIN=python3.12
elif command -v python3.11 >/dev/null 2>&1; then
    PYTHON_BIN=python3.11
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN=python3
else
    echo "No suitable Python interpreter found." >&2
    exit 1
fi

echo "Using base Python: $($PYTHON_BIN --version)"

"$PYTHON_BIN" - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit(f"Python 3.11+ is required; found {sys.version.split()[0]}")
PY

"$PYTHON_BIN" -m venv .venv

.venv/bin/python -m pip install --upgrade pip setuptools wheel
.venv/bin/python -m pip install -e ".[dev]"

# Setup scripts run in a separate shell from agent commands. Add a guarded
# activation stanza for interactive convenience, but do not rely on it; repo
# docs and Makefile use .venv/bin/python explicitly.
BASHRC="$HOME/.bashrc"
MARKER_BEGIN="# >>> rice codex venv >>>"
MARKER_END="# <<< rice codex venv <<<"
if ! grep -Fq "$MARKER_BEGIN" "$BASHRC" 2>/dev/null; then
    {
        echo ""
        echo "$MARKER_BEGIN"
        echo "if [ -f \"$(pwd)/.venv/bin/activate\" ]; then"
        echo "    source \"$(pwd)/.venv/bin/activate\""
        echo "fi"
        echo "$MARKER_END"
    } >> "$BASHRC"
fi

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

echo "Codex setup complete. Use .venv/bin/python or make test/check for task commands."
