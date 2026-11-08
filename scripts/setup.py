#!/usr/bin/env python3
"""Complete per-user workstation setup after the system bootstrap."""

from __future__ import annotations

import json
import argparse
import configparser
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# The bootstrap uses Python isolation to avoid environment import paths.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import install


ROOT = Path(__file__).resolve().parents[1]
RUFF_VERSION = "0.11.13"
PRETTIER_VERSION = "3.5.3"


def python_command(executable: str | Path, *arguments: str) -> list[str]:
    return [str(executable), "-I", *arguments]


def venv_configuration(environment: Path) -> dict[str, str]:
    fields = {}
    for line in (environment / "pyvenv.cfg").read_text().splitlines():
        key, separator, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if not separator or key in fields or key not in {"home", "include-system-site-packages", "version", "executable", "command"}:
            raise RuntimeError("Managed Python configuration is outside the reviewed venv layout")
        fields[key] = value
    if (fields.get("include-system-site-packages") != "false"
            or not Path(fields.get("home", "")).is_absolute()
            or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", fields.get("version", ""))):
        raise RuntimeError("Managed Python configuration is outside the reviewed venv layout")
    return fields


def venv_base_matches(environment: Path) -> bool:
    fields = venv_configuration(environment)
    return (Path(fields["home"]).resolve() == Path(sys._base_executable).resolve().parent
            and tuple(map(int, fields["version"].split(".")[:2])) == sys.version_info[:2])


def verify_venv_configuration(environment: Path) -> None:
    if not venv_base_matches(environment):
        raise RuntimeError("Managed Python base or system-site configuration differs from the system interpreter")


def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
    print("setup:", " ".join(command), flush=True)
    if os.environ.get("NODE_TLS_REJECT_UNAUTHORIZED") == "0":
        raise RuntimeError("Node TLS verification must remain enabled")
    if any(name.lower() == "npm_config_strict_ssl" and value.lower() != "true"
           for name, value in os.environ.items()):
        raise RuntimeError("npm TLS verification must remain enabled")
    kwargs.setdefault("env", {name: value for name, value in os.environ.items()
                              if not name.startswith(("DYLD_", "LD_"))
                              and name not in {"NODE_OPTIONS", "NODE_PATH", "PYTHONPATH", "PYTHONHOME"}})
    return subprocess.run(command, check=True, text=True, **kwargs)


def safe_directory(path: Path, home: Path) -> None:
    if path != home and home not in path.parents:
        raise RuntimeError("Setup directory is outside its selected home")
    if install.has_symlink_ancestor(path, home, include_path=True):
        raise RuntimeError(f"Refusing a symlinked setup directory: {path}")
    current = path
    while current != home:
        if current.exists():
            details = current.stat()
            if not current.is_dir() or details.st_uid != os.getuid() or details.st_mode & 0o022:
                raise RuntimeError(f"Setup directory has foreign ownership or write access; preserved: {current}")
        current = current.parent
    path.mkdir(parents=True, exist_ok=True, mode=0o700)


def state_directory(home: Path) -> Path:
    # Keep alternate-home installs isolated from the invoking user's XDG dirs.
    return home / ".local/share/dotfiles"


def install_python_tools(state: Path, home: Path) -> Path:
    environment = state / "python"
    safe_directory(environment, home)
    requirements = (ROOT / "security/requirements-lock.txt").read_text()
    current = state / "python-current"
    if current.is_symlink():
        target = os.readlink(current)
        if target != "python" and not re.fullmatch(r"python-[0-9a-f]{64}", target):
            raise RuntimeError("Python runtime pointer is foreign; preserved")
        environment = state / target
        safe_directory(environment, home)
    elif current.exists():
        raise RuntimeError("Python runtime pointer is foreign; preserved")
    configuration = environment / "pyvenv.cfg"
    marker = environment / ".requirements"
    if configuration.is_symlink() or marker.is_symlink():
        raise RuntimeError(f"Python environment metadata is a foreign link; preserved: {environment}")
    if any(environment.iterdir()) and not configuration.is_file():
        raise RuntimeError(f"Unexpected Python environment content; preserved: {environment}")
    base_changed = configuration.is_file() and marker.is_file() and marker.read_text() == requirements and not venv_base_matches(environment)
    if marker.is_file() and (marker.read_text() != requirements or base_changed):
        # Preserve the old environment without executing its obsolete packages.
        identity = hashlib.sha256((requirements + sys.implementation.cache_tag + str(Path(sys._base_executable).resolve())).encode()).hexdigest()
        environment = state / f"python-{identity}"
        safe_directory(environment, home)
        configuration, marker = environment / "pyvenv.cfg", environment / ".requirements"
        if configuration.is_symlink() or marker.is_symlink() or (any(environment.iterdir()) and not configuration.is_file()):
            raise RuntimeError("Replacement Python environment is foreign; preserved")
    python = environment / "bin/python"
    fresh = not python.exists()
    if fresh and any(environment.iterdir()):
        # venv's ensurepip child imports site; never reuse unaudited remnants.
        raise RuntimeError("Incomplete Python environment is nonempty; preserved without execution")
    safe_directory(environment / "bin", home)
    if fresh:
        run(python_command(sys.executable, "-S", "-m", "venv", str(environment)))
    if python.exists() and python.resolve() != Path(sys.executable).resolve():
        raise RuntimeError("Managed Python launcher does not resolve to the system interpreter")
    verify_venv_configuration(environment)
    run(python_command(python, "-c", "import pathlib, sys; "
         f"assert pathlib.Path(sys.prefix).resolve() == pathlib.Path({str(environment)!r}).resolve(); "
         "assert sys.prefix != sys.base_prefix"))
    probe = python_command(python, "-c", "import jinja2, yaml; import importlib.metadata as m; "
                           f"assert m.version('ruff') == '{RUFF_VERSION}'")
    healthy = False
    if marker.exists() and marker.read_text() == requirements:
        result = subprocess.run(probe, capture_output=True, text=True)
        healthy = result.returncode == 0 and (environment / "bin/ruff").is_file()
    if not healthy:
        run(python_command(python, "-m", "pip", "--isolated", "install", "--disable-pip-version-check",
             "--index-url", "https://pypi.org/simple", "--no-deps", "--require-hashes", "--only-binary=:all:",
             "--force-reinstall",
             "-r", str(ROOT / "security/requirements-lock.txt")))
    # Do not let a missing or broken environment look like a successful rerun.
    run(probe)
    run([str(environment / "bin/ruff"), "--version"])
    marker.write_text(requirements)
    pending = state / ".python-current.pending"
    if pending.exists() or pending.is_symlink():
        raise RuntimeError("Pending Python runtime pointer is foreign; preserved")
    pending.symlink_to(environment.name)
    pending.replace(current)
    return python


def install_prettier(state: Path, home: Path) -> None:
    prefix = state / "node"
    safe_directory(prefix, home)
    safe_directory(prefix / "bin", home)
    package = prefix / "node_modules"
    if package.is_symlink():
        raise RuntimeError("npm package directory is a foreign link; preserved")
    prettier = prefix / "bin/prettier"
    expected_launcher = prefix / "node_modules/prettier/bin/prettier.cjs"
    old_launcher = prefix / "lib/node_modules/prettier/bin/prettier.cjs"
    if (prettier.exists() or prettier.is_symlink()) and (
            not prettier.is_symlink() or prettier.resolve(strict=False) not in {expected_launcher, old_launcher}):
        raise RuntimeError(f"Prettier launcher is foreign; preserved: {prettier}")
    for name in ("package.json", "package-lock.json"):
        destination = prefix / name
        if destination.is_symlink():
            raise RuntimeError(f"npm manifest is a foreign link; preserved: {destination}")
        shutil.copyfile(ROOT / "security" / name, destination)
    # npm ci enforces the committed lockfile and registry integrity hashes.
    run(["npm", "ci", "--prefix", str(prefix), "--ignore-scripts", "--no-audit", "--no-fund", "--strict-ssl=true"])
    if not expected_launcher.is_file():
        raise RuntimeError("Prettier installation is incomplete")
    if prettier.is_symlink():
        prettier.unlink()
    prettier.symlink_to("../node_modules/prettier/bin/prettier.cjs")
    result = run([str(prettier), "--version"], capture_output=True)
    if result.stdout.strip() != PRETTIER_VERSION:
        raise RuntimeError("Prettier installation did not produce the pinned version")


def plugin_git_environment() -> dict[str, str]:
    environment = {name: value for name, value in os.environ.items() if not name.startswith("GIT_")}
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_SYSTEM="/dev/null",
                       GIT_CONFIG_GLOBAL="/dev/null", GIT_TEMPLATE_DIR="", GIT_NO_REPLACE_OBJECTS="1")
    return environment


def verified_plugin(source: Path, commit: str) -> bool:
    if not source.is_dir() or not (source / ".git").exists():
        return False
    metadata = source / ".git"
    configuration = metadata / "config"
    if metadata.is_symlink() or not metadata.is_dir() or configuration.is_symlink() or not configuration.is_file():
        return False
    parsed = configparser.ConfigParser(interpolation=None)
    try:
        parsed.read_string(configuration.read_text())
        allowed = {"repositoryformatversion", "filemode", "bare", "logallrefupdates", "ignorecase", "precomposeunicode"}
        if parsed.sections() != ["core"] or parsed.defaults() or set(parsed["core"]) - allowed:
            return False
        if parsed["core"].get("repositoryformatversion") != "0" or parsed["core"].get("bare") != "false":
            return False
        if any(value not in {"true", "false"} for key, value in parsed["core"].items() if key != "repositoryformatversion"):
            return False
    except (OSError, UnicodeError, configparser.Error):
        return False
    result = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"],
                            text=True, capture_output=True, env=plugin_git_environment())
    if result.returncode or result.stdout.strip() != commit:
        return False
    # A private index ignores cached assume-unchanged/skip-worktree flags while
    # leaving the user's index and working files untouched. Git compares the
    # working tree against the pinned commit and reports ignored extras too.
    with tempfile.TemporaryDirectory(prefix="dotfiles-plugin-index-") as temporary:
        environment = plugin_git_environment()
        environment["GIT_INDEX_FILE"] = str(Path(temporary) / "index")
        result = subprocess.run(["git", "-C", str(source), "read-tree", commit],
                                text=True, capture_output=True, env=environment)
        if result.returncode:
            return False
        result = subprocess.run(["git", "-C", str(source), "status", "--porcelain", "--untracked-files=all", "--ignored"],
                                text=True, capture_output=True, env=environment)
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
                run(["git", "init", "--quiet", str(checkout)], env=plugin_git_environment())
                run(["git", "-C", str(checkout), "fetch", "--quiet", "--depth", "1", url, commit], env=plugin_git_environment())
                run(["git", "-C", str(checkout), "checkout", "--quiet", "--detach", "FETCH_HEAD"], env=plugin_git_environment())
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
        raise RuntimeError("The installed Node executable is no longer available")
    destination = state / "runtime.json"
    if destination.is_symlink():
        raise RuntimeError(f"Runtime metadata is a foreign link; preserved: {destination}")
    safe_directory(state, home)
    # Preserve the stable package-manager link rather than a versioned Cellar
    # target, so ordinary upgrades keep using the same installed Node location.
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
    argparse.ArgumentParser(description=__doc__).parse_args()
    os.umask(0o077)
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
        run(python_command(sys.executable, "-S", str(ROOT / "scripts/install.py"), "--home", str(home), "--skip-plugins"))
        install_plugins(state, home)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"Installation incomplete: {exc}. Rerun make install after resolving the failure.", file=sys.stderr)
        return 1
    print(f"Workstation setup complete in {home}. Secrets remain separately managed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
