#!/usr/bin/env python3
# line-length: ignore-next-line -- legacy line pending wrap
"""Print a lightweight fingerprint for the repository Python environment inputs."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = (
    "pyproject.toml",
    "requirements*.txt",
    "constraints*.txt",
    "*lock*",
)


def main() -> int:
    h = hashlib.sha256()
# line-length: ignore-next-line -- legacy line pending wrap
    h.update(f"python={sys.version_info.major}.{sys.version_info.minor}\n".encode())
    files = []
    for pattern in PATTERNS:
# line-length: ignore-next-line -- legacy line pending wrap
        files.extend(p for p in ROOT.glob(pattern) if p.is_file() and ".venv" not in p.parts)
    for path in sorted(set(files)):
        rel = path.relative_to(ROOT).as_posix()
        data = path.read_bytes()
# line-length: ignore-next-line -- legacy line pending wrap
        h.update(rel.encode() + b"\0" + hashlib.sha256(data).hexdigest().encode() + b"\n")
    print(h.hexdigest())
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
