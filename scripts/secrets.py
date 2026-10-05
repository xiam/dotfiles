#!/usr/bin/env python3
"""Explicit encrypted secrets operations. Passwords travel through an inherited FD."""

from __future__ import annotations

import argparse
import getpass
import io
import os
import posixpath
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]


def openssl(operation: str, data: bytes, password: str) -> bytes:
    read_fd, write_fd = os.pipe()
    try:
        process = subprocess.Popen(
            ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", *( ["-d"] if operation == "decrypt" else [] ), "-pass", f"fd:{read_fd}"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            pass_fds=(read_fd,),
        )
        os.close(read_fd)
        read_fd = -1
        os.write(write_fd, password.encode("utf-8") + b"\n")
        os.close(write_fd)
        write_fd = -1
        output, error = process.communicate(data)
        if process.returncode:
            raise RuntimeError(error.decode("utf-8", errors="replace").strip() or "OpenSSL operation failed")
        return output
    finally:
        if read_fd >= 0:
            os.close(read_fd)
        if write_fd >= 0:
            os.close(write_fd)


def archive_secrets(directory: Path) -> bytes:
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:gz", format=tarfile.PAX_FORMAT) as archive:
        archive.add(directory, arcname="secrets", recursive=True)
    return stream.getvalue()


def encrypt_bundle(root: Path, password: str, bundle: Path | None = None) -> Path:
    source = root / "secrets"
    if not source.is_dir():
        raise RuntimeError("secrets/ directory not found")
    destination = bundle or root / "secrets.tar.gz.enc"
    if destination.is_symlink():
        raise RuntimeError("refusing to replace a symbolic-link bundle")
    encrypted = openssl("encrypt", archive_secrets(source), password)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=".secrets-encrypted-", dir=destination.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as output:
            output.write(encrypted)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def safe_members(archive: tarfile.TarFile) -> list[tarfile.TarInfo]:
    members = archive.getmembers()
    for member in members:
        name = PurePosixPath(member.name)
        if name.is_absolute() or ".." in name.parts or not name.parts or name.parts[0] != "secrets":
            raise RuntimeError("encrypted archive contains a path outside secrets/")
        if member.islnk() or member.isdev() or member.isfifo():
            raise RuntimeError("encrypted archive contains an unsupported special file")
        if member.issym():
            link = PurePosixPath(member.linkname)
            resolved = PurePosixPath(posixpath.normpath(str(name.parent / link)))
            if link.is_absolute() or ".." in link.parts or resolved.parts[0] != "secrets":
                raise RuntimeError("encrypted archive contains an unsafe symbolic link")
    return members


def extract_archive(payload: bytes, destination: Path) -> None:
    destination.mkdir(mode=0o700, parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
        members = safe_members(archive)
        root = destination.resolve()
        for member in members:
            relative = PurePosixPath(member.name).parts[1:]
            if not relative:
                continue
            target = destination.joinpath(*relative)
            parent = target.parent
            parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            if any(p.is_symlink() for p in (parent, *parent.parents) if p != destination.parent):
                raise RuntimeError("encrypted archive attempts to write through a symbolic link")
            if member.isdir():
                target.mkdir(mode=0o700, parents=True, exist_ok=True)
            elif member.isfile():
                source = archive.extractfile(member)
                if source is None:
                    raise RuntimeError("encrypted archive contains an unreadable file")
                with source, target.open("xb") as output:
                    shutil.copyfileobj(source, output)
                target.chmod(0o600)
            elif member.issym():
                target.symlink_to(member.linkname)
            else:
                raise RuntimeError("encrypted archive contains an unsupported member")
        for directory, dirs, _files in os.walk(destination, followlinks=False):
            Path(directory).chmod(0o700)


def decrypt_bundle(root: Path, password: str, bundle: Path | None = None) -> Path:
    source = bundle or root / "secrets.tar.gz.enc"
    if not source.is_file():
        raise RuntimeError("secrets.tar.gz.enc not found")
    destination = root / "secrets"
    if destination.exists():
        raise RuntimeError("secrets/ already exists; refusing to overwrite existing plaintext")
    encrypted = source.read_bytes()
    tar_data = openssl("decrypt", encrypted, password)
    with tempfile.TemporaryDirectory(prefix=".secrets-stage-", dir=root) as temp_name:
        stage_root = Path(temp_name)
        staged_secrets = stage_root / "secrets"
        extract_archive(tar_data, staged_secrets)
        os.replace(staged_secrets, destination)
    return destination


def install_secret_links(root: Path, home: Path) -> tuple[list[str], list[str]]:
    source_root = root / "secrets"
    installed, conflicts = [], []
    if not source_root.is_dir():
        raise RuntimeError("secrets/ is unavailable; run make secrets-decrypt first")
    for current, dirs, files in os.walk(source_root, followlinks=False):
        current_path = Path(current)
        dirs[:] = [name for name in dirs if not (current_path / name).is_symlink()]
        for name in files:
            source = current_path / name
            relative = source.relative_to(source_root)
            destination = home / relative
            ancestor = destination.parent
            while ancestor != home and ancestor != ancestor.parent:
                if ancestor.is_symlink():
                    conflicts.append(str(destination))
                    break
                ancestor = ancestor.parent
            else:
                ancestor = home
            if ancestor != home:
                continue
            destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            if destination.is_symlink():
                linked = Path(os.readlink(destination))
                if not linked.is_absolute():
                    linked = destination.parent / linked
                if linked.resolve(strict=False) == source.resolve():
                    installed.append(str(destination))
                    continue
                conflicts.append(str(destination))
                continue
            if destination.exists():
                conflicts.append(str(destination))
                continue
            os.chmod(source, 0o600, follow_symlinks=False)
            destination.symlink_to(source)
            installed.append(str(destination))
    return installed, conflicts


def prompt_password(confirm: bool = False) -> str:
    password = getpass.getpass("Secrets password: ")
    if not password:
        raise RuntimeError("empty secrets password refused")
    if confirm and password != getpass.getpass("Confirm secrets password: "):
        raise RuntimeError("password confirmation did not match")
    return password


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("encrypt", "decrypt", "install"))
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--home", type=Path, default=Path(os.environ.get("DOTFILES_HOME", str(Path.home()))))
    args = parser.parse_args()
    root, home = args.root.resolve(), args.home.expanduser().resolve()
    try:
        if args.operation == "encrypt":
            path = encrypt_bundle(root, prompt_password(confirm=True))
            print(f"Encrypted secrets bundle updated atomically: {path}")
        elif args.operation == "decrypt":
            path = decrypt_bundle(root, prompt_password())
            print(f"Decrypted secrets into {path} with restrictive permissions")
        else:
            if not (root / "secrets").is_dir():
                decrypt_bundle(root, prompt_password())
            installed, conflicts = install_secret_links(root, home)
            print(f"Installed or verified {len(installed)} secret links")
            for path in conflicts:
                print(f"conflict preserved: {path}", file=sys.stderr)
            if conflicts:
                return 1
        return 0
    except (OSError, RuntimeError, tarfile.TarError) as exc:
        print(f"secrets {args.operation} failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
