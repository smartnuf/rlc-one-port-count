#!/usr/bin/env bash

repo_root_error() {
    local script_name
    script_name="$(basename "$0")"
    {
        echo "Error: this script must be run from the RICE repository root."
        echo "Expected invocation: ./scripts/${script_name}"
    } >&2
}

require_repo_root() {
    if [[ ! -f pyproject.toml || ! -f README.md || ! -d src/rice ]]; then
        repo_root_error
        exit 1
    fi

    local project_name
    project_name="$(
        awk '
            /^\[project\]$/ { in_project = 1; next }
            /^\[/ { in_project = 0 }
            in_project && $1 == "name" {
                line = $0
                sub(/^[^=]*=[[:space:]]*/, "", line)
                gsub(/["'\'']/, "", line)
                gsub(/[[:space:]]/, "", line)
                print line
                exit
            }
        ' pyproject.toml
    )"

    if [[ "${project_name}" != "rice" ]]; then
        repo_root_error
        exit 1
    fi
}

require_venv_python() {
    if [[ ! -x .venv/bin/python ]]; then
# line-length: ignore-next-line -- legacy line pending wrap
        echo "Error: missing or unusable .venv/bin/python. Run ./scripts/setup.sh first." >&2
        exit 1
    fi

# line-length: ignore-next-line -- legacy line pending wrap
    if ! .venv/bin/python -c 'import sys; print("Using Python:", sys.executable); print("Python version:", sys.version.split()[0])'; then
# line-length: ignore-next-line -- legacy line pending wrap
        echo "Error: .venv/bin/python exists but could not run. Run ./scripts/setup.sh to recreate it." >&2
        exit 1
    fi
}

run() {
    echo
    printf '==> '
    printf '%q ' "$@"
    echo
    "$@"
}
