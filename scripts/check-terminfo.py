#!/usr/bin/env python3
"""Compile the optional Ghostty terminfo entry into a disposable database."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    tic = shutil.which("tic")
    if not tic:
        print("tic is unavailable; optional terminfo check skipped")
        return 0
    with tempfile.TemporaryDirectory(prefix="dotfiles terminfo ") as database:
        result = subprocess.run(
            [tic, "-x", "-o", database, str(ROOT / "third-party/xterm-ghostty.terminfo")],
            capture_output=True,
            text=True,
        )
        if result.returncode:
            print(result.stderr.strip() or "Ghostty terminfo did not compile", file=sys.stderr)
            return result.returncode
        if not (Path(database) / "x" / "xterm-ghostty").is_file():
            print("tic succeeded but did not produce xterm-ghostty entry", file=sys.stderr)
            return 1
    print("Ghostty terminfo compiled into a disposable database")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
