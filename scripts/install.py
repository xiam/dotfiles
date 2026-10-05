#!/usr/bin/env python3
"""Install tracked dotfiles without replacing foreign files or directories."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
LEGACY_PATHS = {
    ".arduino15": "config/.arduino15",
    ".config": "config/.config",
    ".config/btop": "config/.config/btop",
    ".config/ghostty": "config/.config/ghostty",
    ".config/htop": "config/.config/htop",
    ".config/vim-ai": "config/.config/vim-ai",
    ".vim/autoload/pathogen.vim": "config/.vim/autoload/pathogen.vim",
    ".vim/colors/tokyo-night.vim": "config/.vim/colors/tokyo-night.vim",
    ".vim/bundle/rust.vim": "config/.vim/bundle/rust.vim",
    ".vim/bundle/vim-prettier": "config/.vim/bundle/vim-prettier",
    ".vim/pack/ai/start/vim-ai": "config/.vim/pack/ai/start/vim-ai",
    ".vim/pack/ai/start/copilot.vim": "config/.vim/pack/ai/start/copilot.vim",
}
LINKS = {
    "config/.vimrc": ".vimrc",
    "config/.tmux.conf": ".tmux.conf",
    "config/.zshrc": ".zshrc",
    "config/.gitconfig": ".gitconfig",
    "config/.vim/colors/dotfiles.vim": ".vim/colors/dotfiles.vim",
}
SEEDS = {
    "config/.config/btop/btop.conf": ".config/btop/btop.conf",
    "config/.config/btop/themes/dotfiles.theme": ".config/btop/themes/dotfiles.theme",
    "config/.config/htop/htoprc": ".config/htop/htoprc",
    "config/.config/ghostty/themes/dotfiles": ".config/ghostty/themes/dotfiles",
    "config/.config/ghostty/config": ".config/ghostty/config",
}


def repository_identity(remote: str) -> tuple[str, int | None, str] | None:
    """Compare hosted Git origins exactly, independent of SSH/HTTPS transport."""
    if not remote or any(char.isspace() for char in remote):
        return None
    if "://" not in remote:
        match = re.fullmatch(r"(?:[^/@:]+@)?([A-Za-z0-9.-]+):(.+)", remote)
        if not match:
            return None
        remote = f"ssh://{match[1]}/{match[2]}"
    try:
        parsed = urlsplit(remote)
        if parsed.scheme not in {"https", "ssh"} or not parsed.hostname or parsed.query or parsed.fragment:
            return None
        port = parsed.port
        if port == {"https": 443, "ssh": 22}[parsed.scheme]:
            port = None
        elif port is not None:
            # A nonstandard port does not identify the same endpoint across
            # SSH and HTTPS. Require a standard hosted origin for migration.
            return None
        path = parsed.path.removeprefix("/").removesuffix(".git")
        if not path or any(part in {"", ".", ".."} for part in path.split("/")) or "%" in path or "\\" in path:
            return None
        return parsed.hostname.lower(), port, path
    except ValueError:
        return None


def origin_identity(checkout: Path) -> tuple[str, int | None, str] | None:
    try:
        remote = subprocess.run(
            ["git", "-C", str(checkout), "remote", "get-url", "origin"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        return repository_identity(remote)
    except (OSError, subprocess.CalledProcessError):
        return None


def tracked_dotfiles_target(target: Path, expected_relative: str | None = None) -> bool:
    """Prove a legacy link belongs to public upstream or the invoking origin."""
    resolved = target.resolve(strict=False)
    trusted_origins = {("github.com", None, "xiam/dotfiles")}
    invoking_origin = origin_identity(ROOT)
    if invoking_origin is not None:
        trusted_origins.add(invoking_origin)
    for parent in (resolved, *resolved.parents):
        if not (parent / ".git").exists() and not (parent / ".git").is_file():
            continue
        try:
            if origin_identity(parent) not in trusted_origins:
                continue
            relative = resolved.relative_to(parent)
            if expected_relative is not None and str(relative) != expected_relative:
                continue
            check = subprocess.run(
                ["git", "-C", str(parent), "ls-files", "-z", "--", str(relative)],
                capture_output=True,
            )
            if check.returncode == 0 and check.stdout:
                return True
            # A retired or moved dotfile can leave a dangling link after the
            # source path disappears from the current tree. Only the explicit
            # legacy path supplied by the caller may use history as proof.
            if expected_relative is not None and str(relative) == expected_relative:
                history = subprocess.run(
                    ["git", "-C", str(parent), "log", "-1", "--format=%H", "HEAD", "--", str(relative)],
                    capture_output=True,
                    text=True,
                )
                if history.returncode == 0 and history.stdout.strip():
                    return True
        except (OSError, ValueError, subprocess.CalledProcessError):
            continue
    return False


def has_symlink_ancestor(path: Path, home: Path, include_path: bool = False) -> bool:
    current = path if include_path else path.parent
    while current != home and current != current.parent:
        if current.is_symlink():
            return True
        current = current.parent
    return False


def ensure_link(source: Path, destination: Path, home: Path) -> str:
    if has_symlink_ancestor(destination, home):
        return "conflict"
    destination.parent.mkdir(parents=True, exist_ok=True)
    expected = source.resolve()
    if destination.is_symlink():
        current = Path(os.readlink(destination))
        if not current.is_absolute():
            current = destination.parent / current
        if current.resolve(strict=False) == expected:
            return "already-managed"
        try:
            expected_relative = str(source.resolve().relative_to(ROOT))
        except ValueError:
            # A complete install links verified plugins from a per-user cache.
            expected_relative = str(Path("config/.vim/pack/dotfiles/start") / destination.name)
        if not tracked_dotfiles_target(current, expected_relative):
            return "conflict"
    elif destination.exists():
        return "conflict"
    temp = destination.with_name(f".{destination.name}.dotfiles-tmp-{os.getpid()}")
    try:
        temp.symlink_to(source)
        os.replace(temp, destination)
    finally:
        if temp.is_symlink():
            temp.unlink()
    return "linked"


def seed_if_absent(source: Path, destination: Path, home: Path) -> str:
    if has_symlink_ancestor(destination, home):
        return "conflict"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        return "preserved"
    try:
        with source.open("rb") as src, destination.open("xb") as dst:
            shutil.copyfileobj(src, dst)
        destination.chmod(0o600 if destination.name in {"btop.conf", "htoprc"} else 0o644)
    except FileExistsError:
        return "preserved"
    return "seeded"


def remove_owned_legacy(home: Path) -> list[str]:
    removed: list[str] = []
    for relative, expected_target in LEGACY_PATHS.items():
        path = home / relative
        if has_symlink_ancestor(path, home):
            continue
        if not path.is_symlink():
            continue
        target = Path(os.readlink(path))
        if not target.is_absolute():
            target = path.parent / target
        if tracked_dotfiles_target(target, expected_target):
            path.unlink()
            removed.append(str(path))
    return removed


def install_plugins(home: Path) -> tuple[list[str], list[str]]:
    source_root = ROOT / "config/.vim/pack/dotfiles/start"
    installed, conflicts = [], []
    for source in sorted(source_root.iterdir() if source_root.exists() else []):
        if source.name.startswith("."):
            continue
        destination = home / ".vim/pack/dotfiles/start" / source.name
        result = ensure_link(source, destination, home)
        if result == "conflict":
            conflicts.append(str(destination))
        else:
            installed.append(str(destination))
    return installed, conflicts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=Path(os.environ.get("DOTFILES_HOME") or str(Path.home())))
    parser.add_argument("--skip-plugins", action="store_true", help="link settings only; plugins are supplied separately")
    args = parser.parse_args()
    home = args.home.expanduser().resolve()
    if sys.version_info < (3, 10):
        print("install requires Python 3.10 or newer", file=sys.stderr)
        return 2
    for source in [*LINKS, *SEEDS]:
        if not (ROOT / source).exists():
            print(f"missing generated file: {source}; run make render", file=sys.stderr)
            return 2

    removed = remove_owned_legacy(home)
    conflicts: list[str] = []
    for source_name, destination_name in LINKS.items():
        source, destination = ROOT / source_name, home / destination_name
        result = ensure_link(source, destination, home)
        if result == "conflict":
            conflicts.append(str(destination))
        else:
            print(f"{result}: {destination} -> {source}")

    plugin_paths, plugin_conflicts = ([], []) if args.skip_plugins else install_plugins(home)
    conflicts.extend(plugin_conflicts)
    for destination in plugin_paths:
        print(f"plugin link: {destination}")
    for source_name, destination_name in SEEDS.items():
        destination = home / destination_name
        result = seed_if_absent(ROOT / source_name, destination, home)
        if result == "conflict":
            conflicts.append(str(destination))
        else:
            print(f"{result}: {destination}")
    for path in removed:
        print(f"removed obsolete repository link: {path}")
    for path in conflicts:
        print(f"conflict preserved: {path}", file=sys.stderr)
    if conflicts:
        print("Resolve the listed conflicts by moving the unmanaged file, then rerun make install.", file=sys.stderr)
        return 1
    print(f"Installed dotfiles into {home}. Local override files were left untouched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
