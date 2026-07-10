#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/_common.sh
source "${SCRIPT_DIR}/_common.sh"

require_repo_root

python_candidate_is_usable() {
    local candidate_path temp_dir status
    candidate_path="$1"

    case "${candidate_path}" in
        "${PWD}/.venv/"*) return 1 ;;
    esac

    if ! "${candidate_path}" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1; then
        return 1
    fi

    temp_dir="$(mktemp -d "${TMPDIR:-/tmp}/rice-venv-check.XXXXXX")" || return 1
    status=0
    if ! "${candidate_path}" -m venv "${temp_dir}/venv" >/dev/null 2>&1; then
        status=1
    fi
    rm -rf -- "${temp_dir}"
    return "${status}"
}

find_base_python() {
    local candidate candidate_path seen_paths selected
    seen_paths=""
    selected=""

    for candidate in python3.14 python3.13 python3.12 python3.11 python3; do
        while IFS= read -r candidate_path; do
            [[ -n "${candidate_path}" ]] || continue
            case "
${seen_paths}
" in
                *"
${candidate_path}
"*) continue ;;
            esac
            seen_paths="${seen_paths}${candidate_path}
"
            if python_candidate_is_usable "${candidate_path}"; then
                selected="${candidate_path}"
                break
            fi
        done <<EOF_CANDIDATES
$(type -P -a "${candidate}" 2>/dev/null || true)
EOF_CANDIDATES
        [[ -n "${selected}" ]] && break
    done

    [[ -n "${selected}" ]] || return 1
    printf '%s\n' "${selected}"
}

echo "Setting up RICE development environment"

PYTHON_BIN="$(find_base_python || true)"
if [[ -z "${PYTHON_BIN}" ]]; then
    echo "Error: Python 3.11 or newer with working venv support is required, but no suitable interpreter was found." >&2
    exit 1
fi

echo "Selected base Python:"
"${PYTHON_BIN}" -c 'import sys; print("  executable:", sys.executable); print("  version:", sys.version.split()[0])'

if [[ "${RICE_SETUP_ONLY_PRINT_PYTHON:-}" == "1" ]]; then
    exit 0
fi

if ! run "${PYTHON_BIN}" -m venv .venv; then
    echo "Error: selected Python failed to create .venv even though the capability probe succeeded: ${PYTHON_BIN}" >&2
    exit 1
fi
run .venv/bin/python -m pip install --upgrade pip setuptools wheel
run .venv/bin/python -m pip install -e ".[dev]"

echo
echo "Virtual environment Python:"
.venv/bin/python -c 'import sys; print("  executable:", sys.executable); print("  version:", sys.version.split()[0])'

echo
echo "Import smoke test:"
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

echo
echo "Setup complete."
