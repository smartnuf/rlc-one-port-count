# 01-dev-env / 03 — Validate WSL2 Ubuntu path

Status: `done`

## Goal

Use a fresh WSL2 Ubuntu instance on the ARM Windows laptop as the first clean Linux validation environment.

## Tasks

- Install base tools: Git, Make, Python, venv support, pip.
- Clone the repository cleanly.
- Confirm that no project dependency has been installed into system Python.
- Use this environment to run `make setup` and `make test`.

## Suggested commands

```bash
sudo apt update
sudo apt install -y git make python3 python3-venv python3-pip
git clone <repo-url>
cd <local-repo>
```

## Done means

- WSL2 Ubuntu is usable for rice development.
- The repository is cloned.
- System packages are installed only as OS-level prerequisites.
