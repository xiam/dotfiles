#!/usr/bin/env python3
"""Complete per-user workstation setup after the system bootstrap."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import install


ROOT = Path(__file__).resolve().parents[1]
RUFF_VERSION = "0.11.13"
PRETTIER_VERSION = "3.5.3"


def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
    print("setup:", " ".join(command), flush=True)
    return subprocess.run(command, check=True, text=True, **kwargs)


def safe_directory(path: Path, home: Path) -> None:
    if install.has_symlink_ancestor(path, home, include_path=True):
        raise RuntimeError(f"Refusing a symlinked setup directory: {path}")
    path.mkdir(parents=True, exist_ok=True)


def state_directory(home: Path) -> Path:
    # Keep alternate-home installs isolated from the invoking user's XDG dirs.
    return home / ".local/share/dotfiles"


def install_python_tools(state: Path, home: Path) -> Path:
    environment = state / "python"
    safe_directory(environment, home)
    configuration = environment / "pyvenv.cfg"
    marker = environment / ".requirements"
    if configuration.is_symlink() or marker.is_symlink():
        raise RuntimeError(f"Python environment metadata is a foreign link; preserved: {environment}")
    if any(environment.iterdir()) and not configuration.is_file():
        raise RuntimeError(f"Unexpected Python environment content; preserved: {environment}")
    safe_directory(environment / "bin", home)
    python = environment / "bin/python"
    if not python.exists():
        run([sys.executable, "-m", "venv", str(environment)])
    run([str(python), "-c", "import pathlib, sys; "
         f"assert pathlib.Path(sys.prefix).resolve() == pathlib.Path({str(environment)!r}).resolve(); "
         "assert sys.prefix != sys.base_prefix"])
    requirements = (ROOT / "requirements-render.txt").read_text() + f"\nruff=={RUFF_VERSION}\n"
    probe = [str(python), "-c", "import jinja2, yaml; import importlib.metadata as m; "
             f"assert m.version('ruff') == '{RUFF_VERSION}'"]
    healthy = False
    if marker.exists() and marker.read_text() == requirements:
        result = subprocess.run(probe, capture_output=True, text=True)
        healthy = result.returncode == 0 and (environment / "bin/ruff").is_file()
    if not healthy:
        run([str(python), "-m", "pip", "--isolated", "install", "--disable-pip-version-check",
             "-r", str(ROOT / "requirements-render.txt"), f"ruff=={RUFF_VERSION}"])
    # Do not let a missing or broken environment look like a successful rerun.
    run(probe)
    run([str(environment / "bin/ruff"), "--version"])
    marker.write_text(requirements)
    return python


def install_prettier(state: Path, home: Path) -> None:
    prefix = state / "node"
    safe_directory(prefix, home)
    for relative in ("bin", "lib", "lib/node_modules"):
        safe_directory(prefix / relative, home)
    if (prefix / "lib/node_modules/prettier").is_symlink():
        raise RuntimeError("Prettier package directory is a foreign link; preserved")
    prettier = prefix / "bin/prettier"
    if prettier.is_symlink() and not prettier.resolve(strict=False).is_relative_to(prefix):
        raise RuntimeError(f"Prettier launcher is a foreign link; preserved: {prettier}")
    version = None
    if prettier.exists():
        result = subprocess.run([str(prettier), "--version"], text=True, capture_output=True)
        if result.returncode == 0:
            version = result.stdout.strip()
    if version != PRETTIER_VERSION:
        run(["npm", "install", "--global", "--prefix", str(prefix), "--no-audit", "--no-fund",
             "--ignore-scripts", f"prettier@{PRETTIER_VERSION}"])
    result = run([str(prettier), "--version"], capture_output=True)
    if result.stdout.strip() != PRETTIER_VERSION:
        raise RuntimeError("Prettier installation did not produce the pinned version")


def verified_plugin(source: Path, commit: str) -> bool:
    if not source.is_dir() or not (source / ".git").exists():
        return False
    result = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"],
                            text=True, capture_output=True)
    if result.returncode or result.stdout.strip() != commit:
        return False
    result = subprocess.run(["git", "-C", str(source), "status", "--porcelain"],
                            text=True, capture_output=True)
    return result.returncode == 0 and not result.stdout.strip()


def install_plugins(state: Path, home: Path) -> None:
    cache = state / "plugins"
    safe_directory(cache, home)
    manifest = json.loads((ROOT / "plugins.json").read_text())
    for name, pin in sorted(manifest.items()):
        commit, url = pin["commit"], pin["url"]
        if not re.fullmatch(r"[a-zA-Z0-9_.-]+", name) or not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise RuntimeError("Invalid plugin manifest")
        if not url.startswith("https://github.com/") or not url.endswith(".git"):
            raise RuntimeError("Plugin upstream must be an HTTPS GitHub repository")
        source = cache / f"{name}-{commit}"
        if source.is_symlink() or (source.exists() and not verified_plugin(source, commit)):
            raise RuntimeError(f"Plugin cache has unexpected content; preserved: {source}")
        if not source.exists():
            with tempfile.TemporaryDirectory(prefix=f".{name}-", dir=cache) as temporary:
                checkout = Path(temporary) / "checkout"
                run(["git", "init", "--quiet", str(checkout)])
                run(["git", "-C", str(checkout), "fetch", "--quiet", "--depth", "1", url, commit])
                run(["git", "-C", str(checkout), "checkout", "--quiet", "--detach", "FETCH_HEAD"])
                if not verified_plugin(checkout, commit):
                    raise RuntimeError(f"Plugin revision verification failed: {name}")
                checkout.rename(source)
        destination = home / ".vim/pack/dotfiles/start" / name
        if install.has_symlink_ancestor(destination, home):
            raise RuntimeError(f"Plugin destination has a symlinked parent; preserved: {destination}")
        # Retarget only an old pin we can prove belongs to this managed cache,
        # or a tracked source plugin belonging to this dotfiles origin.
        if destination.is_symlink():
            current = destination.resolve(strict=False)
            old_pin = current.parent == cache and current.name.startswith(f"{name}-")
            if old_pin and re.fullmatch(r"[0-9a-f]{40}", current.name[len(name) + 1:]):
                if current != source and verified_plugin(current, current.name[len(name) + 1:]):
                    destination.unlink()
        result = install.ensure_link(source, destination, home)
        if result == "conflict":
            raise RuntimeError(f"Plugin conflict preserved: {destination}")
        print(f"{result}: {destination}")


def install_terminfo(home: Path) -> None:
    database = home / ".terminfo"
    safe_directory(database, home)
    # Compile off to the side. tic may choose letter or hexadecimal directories
    # and older implementations may emit aliases in addition to the main entry.
    with tempfile.TemporaryDirectory(prefix="dotfiles terminfo ") as temporary:
        compiled = Path(temporary)
        run(["tic", "-x", "-o", str(compiled), str(ROOT / "third-party/xterm-ghostty.terminfo")])
        entries = [path for path in compiled.rglob("*") if path.is_file()]
        for entry in entries:
            destination = database / entry.relative_to(compiled)
            if install.has_symlink_ancestor(destination, home, include_path=True):
                raise RuntimeError(f"Terminfo entry has a foreign link; preserved: {destination}")
            if destination.exists() and not destination.is_file():
                raise RuntimeError(f"Terminfo entry conflicts with personal content: {destination}")
            if destination.is_file() and destination.read_bytes() != entry.read_bytes():
                raise RuntimeError(f"Different personal terminfo entry preserved: {destination}")
        for entry in entries:
            destination = database / entry.relative_to(compiled)
            safe_directory(destination.parent, home)
            with tempfile.NamedTemporaryFile(mode="wb", dir=destination.parent, delete=False) as output:
                pending = Path(output.name)
                output.write(entry.read_bytes())
            try:
                pending.replace(destination)
            finally:
                pending.unlink(missing_ok=True)
    environment = os.environ.copy()
    environment.update(HOME=str(home), TERMINFO=str(database))
    result = run(["infocmp", "-x", "xterm-ghostty"], env=environment, capture_output=True)
    if "xterm-ghostty" not in result.stdout:
        raise RuntimeError("Ghostty terminfo lookup failed after compilation")


def record_runtime(state: Path, home: Path) -> None:
    node = shutil.which("node")
    if not node:
        raise RuntimeError("The validated Node executable is no longer available")
    destination = state / "runtime.json"
    if destination.is_symlink():
        raise RuntimeError(f"Runtime metadata is a foreign link; preserved: {destination}")
    safe_directory(state, home)
    # Preserve the stable package-manager link rather than a versioned Cellar
    # target, so ordinary upgrades keep using the same validated Node location.
    data = {"node": str(Path(node).absolute())}
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=state, delete=False) as output:
        temporary = Path(output.name)
        json.dump(data, output)
        output.write("\n")
    try:
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    home = Path(os.environ.get("DOTFILES_HOME") or str(Path.home())).expanduser().resolve()
    state = state_directory(home)
    try:
        safe_directory(state, home)
        record_runtime(state, home)
        install_python_tools(state, home)
        install_prettier(state, home)
        install_terminfo(home)
        # The offline installer keeps its original safe conflict behavior.
        # Complete setup supplies and links plugins separately from submodules.
        run([sys.executable, str(ROOT / "scripts/install.py"), "--home", str(home), "--skip-plugins"])
        install_plugins(state, home)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"Installation incomplete: {exc}. Rerun make install after resolving the failure.", file=sys.stderr)
        return 1
    print(f"Workstation setup complete in {home}. Secrets remain separately managed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
