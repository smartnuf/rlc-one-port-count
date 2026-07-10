#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/_common.sh
source "${SCRIPT_DIR}/_common.sh"

require_repo_root
require_venv_python

run bash scripts/lint.sh
run bash scripts/test.sh
run .venv/bin/python -m rice supports --max-edges 8
run .venv/bin/python -m rice bundles --max-r 3 --max-reactive 5
run .venv/bin/python -m rice labelings --max-r 3 --max-reactive 5
run .venv/bin/python -m rice reduced --max-r 2 --max-reactive 3
