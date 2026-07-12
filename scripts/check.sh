#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/_common.sh
source "${SCRIPT_DIR}/_common.sh"

require_repo_root
require_venv_python

run ./scripts/lint.sh
run .venv/bin/python -m pytest -q
run .venv/bin/python -m rice count supports --max-support-edges 8
run .venv/bin/python -m rice count bundle-types
run .venv/bin/python -m rice count bundle-sets --profile main
run .venv/bin/python -m rice count assignments --profile main
run .venv/bin/python -m rice count assigned-supports --profile main
run .venv/bin/python -m rice count networks --profile golden
