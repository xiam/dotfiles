#!/usr/bin/env python3
"""Report workstation dependencies and optional applications."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from importlib.util import find_spec
from format import managed_tool


def version(command: list[str]) -> tuple[int, ...] | None:
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    match = re.search(r"\d+(?:\.\d+)+", result.stdout + result.stderr)
    return tuple(int(part) for part in match.group().split(".")) if match else None


def main() -> int:
    failures = []
    requirements = (
        ("python3", [sys.executable, "--version"], (3, 10)),
        ("vim", ["vim", "--version"], (9, 0)),
        ("tmux", ["tmux", "-V"], (3, 2)),
        ("zsh", ["zsh", "--version"], (5, 8)),
    )
    print("Required tools (minimum versions):")
    for name, command, minimum in requirements:
        found = version(command)
        ok = found is not None and found >= minimum
        print(f"  {'OK' if ok else 'MISSING/OLD'} {name}: need {'.'.join(map(str, minimum))}+; found {found or 'not installed'}")
        if not ok:
            failures.append(name)

    print("\nRequired workflow tools:")
    for name in ("git", "make"):
        path = shutil.which(name)
        print(f"  {'OK' if path else 'MISSING'} {name}{': ' + path if path else ''}")
        if not path:
            failures.append(name)

    print("\nTerminal and rendering tools:")
    openssl = shutil.which("openssl")
    print(f"  {'available' if openssl else 'not found'} openssl{': ' + openssl if openssl else ''} (needed only for explicit secrets commands)")
    tic = shutil.which("tic")
    print(f"  {'available' if tic else 'not found'} tic{': ' + tic if tic else ''}")
    if not tic or not shutil.which("infocmp"):
        failures.append("terminfo tools")
    rendering = find_spec('jinja2') and find_spec('yaml')
    print(f"  {'available' if rendering else 'not found'} Jinja2 + PyYAML")
    if not rendering:
        failures.append("render dependencies")

    print("\nDefault formatter tools:")
    for name in ("gofmt", "rustfmt", "ruff", "prettier"):
        path = shutil.which(name) or managed_tool(name)
        print(f"  {'available' if path else 'not found'} {name}{': ' + path if path else ''}")
        if not path:
            failures.append(name)
    print("\nOptional applications:")
    for name in ("btop", "htop", "ghostty"):
        path = shutil.which(name)
        print(f"  {'available' if path else 'not found'} {name}{': ' + path if path else ''}")
    if failures:
        print("Run make install to supply missing dependencies; doctor never installs packages.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
