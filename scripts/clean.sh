#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/_common.sh
source "${SCRIPT_DIR}/_common.sh"

require_repo_root

removed=0

remove_path() {
    local path="$1"
    if [[ -e "${path}" || -L "${path}" ]]; then
        echo "Removing ${path}"
        rm -rf -- "${path}"
        removed=1
    fi
}

remove_path .venv
remove_path .pytest_cache
remove_path .pytest-tmp
remove_path build
remove_path dist

shopt -s nullglob
for path in ./*.egg-info ./src/*.egg-info; do
    remove_path "${path}"
done
shopt -u nullglob

while IFS= read -r -d '' path; do
    remove_path "${path}"
# line-length: ignore-next-line -- legacy line pending wrap
done < <(find . \( -path ./.git -o -path ./.venv \) -prune -o -type d -name __pycache__ -print0)

if (( removed == 0 )); then
    echo "Development artefacts already clean."
fi
