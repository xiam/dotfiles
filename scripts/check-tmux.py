#!/usr/bin/env python3
"""Parse tmux config on a private socket without using live sessions."""

from __future__ import annotations

import os
import subprocess
import sys


def main() -> int:
    socket = f"dotfiles-check-{os.getpid()}"
    config = "config/.tmux.conf"
    command = ["tmux", "-f", config, "-L", socket, "new-session", "-d"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=15)
        if result.returncode:
            print(result.stderr.strip() or "tmux could not parse the generated configuration", file=sys.stderr)
            return result.returncode
        print("tmux config parsed on an isolated server")
        return 0
    finally:
        subprocess.run(["tmux", "-L", socket, "kill-server"], capture_output=True, text=True, timeout=10)


if __name__ == "__main__":
    raise SystemExit(main())
