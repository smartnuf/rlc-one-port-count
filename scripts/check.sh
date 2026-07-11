#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
run() { printf '+ %q ' "$@"; printf '\n'; "$@"; }
run .venv/bin/python -m ruff check .
run .venv/bin/python -m pytest -q
run .venv/bin/python -m rice count supports --max-support-edges 8
run .venv/bin/python -m rice count bundle-types
run .venv/bin/python -m rice count bundle-sets --profile main
run .venv/bin/python -m rice count assignments --profile main
run .venv/bin/python -m rice count assigned-supports --profile main
run .venv/bin/python -m rice count networks --profile golden
