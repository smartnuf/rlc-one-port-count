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

FINGERPRINT_FILE=.venv/rice-env.fingerprint
CURRENT_FINGERPRINT="$(.venv/bin/python .codex/env_fingerprint.py)"
STORED_FINGERPRINT=""
if [ -f "$FINGERPRINT_FILE" ]; then
    STORED_FINGERPRINT="$(cat "$FINGERPRINT_FILE")"
fi

if [ "$CURRENT_FINGERPRINT" = "$STORED_FINGERPRINT" ]; then
    echo "Environment inputs unchanged; skipping editable-install refresh."
else
    echo "Environment inputs changed; refreshing editable install."
    .venv/bin/python -m pip install --upgrade pip setuptools wheel
    .venv/bin/python -m pip install --no-build-isolation -e ".[dev]"
    .venv/bin/python .codex/env_fingerprint.py > "$FINGERPRINT_FILE"
fi

echo "Environment smoke test:"
.venv/bin/python - <<'PY'
import sys
import networkx
import rice
print("python", sys.executable)
print("networkx", networkx.__version__)
print("rice", rice.__file__)
PY

# line-length: ignore-next-line -- legacy line pending wrap
echo "Codex maintenance complete. Environment prepared; run task validation separately."
