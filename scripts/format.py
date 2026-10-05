#!/usr/bin/env python3
"""Format Vim buffer input safely, leaving buffer contents untouched on error."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


PRETTIER_FILETYPES = {"javascript", "javascriptreact", "typescript", "typescriptreact", "yaml", "json", "markdown"}


def managed_tool(name: str) -> str | None:
    home = Path(os.environ.get("DOTFILES_HOME") or str(Path.home())).expanduser()
    state = home / ".local/share/dotfiles"
    candidates = (state / "python/bin" / name, state / "node/bin" / name,
                  Path("/opt/homebrew/bin") / name, Path("/usr/local/bin") / name)
    return next((str(path) for path in candidates if path.is_file() and os.access(path, os.X_OK)), None)


def find_up(start: Path, relative: str) -> Path | None:
    for parent in (start, *start.parents):
        candidate = parent / relative
        if candidate.exists():
            return candidate
    return None


def project_root(filetype: str, filename: Path) -> Path:
    marker_sets = {
        "go": ("go.mod", "go.work"),
        "rust": ("Cargo.toml", "rustfmt.toml", ".rustfmt.toml"),
        "python": ("pyproject.toml", "ruff.toml", ".ruff.toml", "setup.cfg", "tox.ini"),
        "javascript": ("package.json", "prettier.config.js", ".prettierrc"),
        "javascriptreact": ("package.json", "prettier.config.js", ".prettierrc"),
        "typescript": ("package.json", "prettier.config.js", ".prettierrc"),
        "typescriptreact": ("package.json", "prettier.config.js", ".prettierrc"),
        "yaml": ("package.json", "prettier.config.js", ".prettierrc"),
        "json": ("package.json", "prettier.config.js", ".prettierrc"),
        "markdown": ("package.json", "prettier.config.js", ".prettierrc"),
    }
    markers = marker_sets.get(filetype, ())
    for parent in (filename.parent, *filename.parent.parents):
        if any((parent / marker).exists() for marker in markers):
            return parent
    return filename.parent


def formatter(filetype: str, name: Path) -> list[str] | None:
    local_prettier = find_up(name.parent, "node_modules/.bin/prettier")
    local_ruff = find_up(name.parent, ".venv/bin/ruff") or find_up(name.parent, "venv/bin/ruff")
    local_black = find_up(name.parent, ".venv/bin/black") or find_up(name.parent, "venv/bin/black")
    local_goimports = find_up(name.parent, "bin/goimports")
    local_gofmt = find_up(name.parent, "bin/gofmt")
    if filetype in {"go"}:
        tool = local_goimports or local_gofmt or shutil.which("goimports") or shutil.which("gofmt") or managed_tool("gofmt")
        return [str(tool)] if tool else None
    if filetype == "rust":
        local_rustfmt = find_up(name.parent, ".cargo/bin/rustfmt") or find_up(name.parent, "bin/rustfmt")
        path = str(local_rustfmt) if local_rustfmt else shutil.which("rustfmt") or managed_tool("rustfmt")
        return [path, "--emit", "stdout", "--edition", "2021"] if path else None
    if filetype == "python":
        if local_ruff:
            return [str(local_ruff), "format", "--stdin-filename", str(name), "-"]
        if local_black:
            return [str(local_black), "--quiet", "--stdin-filename", str(name), "-"]
        ruff = shutil.which("ruff") or managed_tool("ruff")
        if ruff:
            return [ruff, "format", "--stdin-filename", str(name), "-"]
        black = shutil.which("black")
        return [black, "--quiet", "--stdin-filename", str(name), "-"] if black else None
    if filetype in PRETTIER_FILETYPES:
        prettier = str(local_prettier) if local_prettier else shutil.which("prettier") or managed_tool("prettier")
        return [prettier, "--stdin-filepath", str(name)] if prettier else None
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--filetype", required=True)
    parser.add_argument("--name", required=True, type=Path)
    args = parser.parse_args()
    command = formatter(args.filetype, args.name.expanduser().resolve(strict=False))
    if command is None:
        print(f"No formatter configured for filetype {args.filetype!r} or required tool is missing.", file=sys.stderr)
        return 2
    if not command[0]:
        print("No compatible Go formatter found; install goimports or gofmt.", file=sys.stderr)
        return 2
    try:
        environment = os.environ.copy()
        # Prettier's launcher uses `env node`. Use the location validated by
        # installation ahead of any stale Node in an existing Vim session.
        home = Path(environment.get("DOTFILES_HOME") or str(Path.home())).expanduser()
        runtime = home / ".local/share/dotfiles/runtime.json"
        if args.filetype in PRETTIER_FILETYPES and runtime.exists():
            node = Path(json.loads(runtime.read_text())["node"])
            if not node.is_absolute() or not node.is_file() or not os.access(node, os.X_OK):
                raise OSError("Installed Node is unavailable; rerun make install")
            environment["PATH"] = str(node.parent) + os.pathsep + environment.get("PATH", "")
        result = subprocess.run(
            command,
            input=sys.stdin.buffer.read(),
            capture_output=True,
            check=False,
            cwd=project_root(args.filetype, args.name.expanduser().resolve(strict=False)),
            env=environment,
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Could not start formatter: {exc}", file=sys.stderr)
        return 2
    if result.returncode:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        print(f"Formatter failed ({result.returncode}); buffer was not changed. {message}", file=sys.stderr)
        return result.returncode
    sys.stdout.buffer.write(result.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
