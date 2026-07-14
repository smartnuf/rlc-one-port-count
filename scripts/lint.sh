#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/_common.sh
source "${SCRIPT_DIR}/_common.sh"

require_repo_root
require_venv_python

run git diff --check
run .venv/bin/python scripts/check_line_lengths.py

echo
echo "==> syntax compile tracked Python files under src/ and tests/"
python_files=()
while IFS= read -r python_file; do
    python_files+=("${python_file}")
done < <(git ls-files 'src/*.py' 'tests/*.py')

if (( ${#python_files[@]} == 0 )); then
    echo "No tracked Python files found under src/ or tests/."
else
    .venv/bin/python - "${python_files[@]}" <<'PY'
import pathlib
import sys

failed = False
for raw_path in sys.argv[1:]:
    path = pathlib.Path(raw_path)
    try:
        source = path.read_text(encoding="utf-8")
        compile(source, raw_path, "exec")
    except SyntaxError as exc:
        failed = True
        location = f"{raw_path}:{exc.lineno}:{exc.offset or 0}"
        print(f"Syntax error in {location}: {exc.msg}", file=sys.stderr)
    except OSError as exc:
        failed = True
        print(f"Could not read {raw_path}: {exc}", file=sys.stderr)

if failed:
    raise SystemExit(1)

print(f"Compiled {len(sys.argv) - 1} Python files without writing bytecode.")
PY
fi
