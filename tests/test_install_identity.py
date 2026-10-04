from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location("installer", Path(__file__).resolve().parents[1] / "scripts/install.py")
assert SPEC and SPEC.loader
INSTALL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INSTALL)


class InstallerIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="installer identity ")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.invoking = self.checkout("invoking", "https://forge.example.invalid/team/dotfiles.git")
        self.root_patch = patch.object(INSTALL, "ROOT", self.invoking)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def git(self, repo: Path, *args: str) -> None:
        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)

    def checkout(self, name: str, origin: str | None) -> Path:
        repo = self.base / name
        repo.mkdir()
        self.git(repo, "init", "-q")
        if origin is not None:
            self.git(repo, "remote", "add", "origin", origin)
        for relative in ("config/.vimrc", "config/.arduino15/keep", "unrelated"):
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("preserve me\n")
        self.git(repo, "add", ".")
        self.git(repo, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "Fixture")
        return repo

    def test_transport_normalization_and_invalid_origins(self) -> None:
        expected = ("forge.example.invalid", None, "team/dotfiles")
        for origin in ("git@forge.example.invalid:team/dotfiles.git", "ssh://git@FORGE.EXAMPLE.INVALID:22/team/dotfiles.git", "https://forge.example.invalid:443/team/dotfiles"):
            with self.subTest(origin=origin):
                self.assertEqual(INSTALL.repository_identity(origin), expected)
        for origin in ("", "/local/repo", "file:///local/repo", "http://forge.example.invalid/team/dotfiles", "git://forge.example.invalid/team/dotfiles", "https://forge.example.invalid/team/../dotfiles", "https://forge.example.invalid/team//dotfiles", "https://forge.example.invalid/team/dotfiles/", "https://forge.example.invalid/team/dotfiles?other", "https://forge.example.invalid/team/%64otfiles", "https://forge.example.invalid:bad/team/dotfiles", "ssh://forge.example.invalid:2222/team/dotfiles", "https://forge.example.invalid:2222/team/dotfiles"):
            with self.subTest(origin=origin):
                self.assertIsNone(INSTALL.repository_identity(origin))

    def test_accepts_public_upstream_and_equivalent_invoking_origin(self) -> None:
        for index, origin in enumerate(("git@forge.example.invalid:team/dotfiles.git", "https://github.com/xiam/dotfiles.git", "git@github.com:xiam/dotfiles.git")):
            with self.subTest(origin=origin):
                repo = self.checkout(f"accepted-{index}", origin)
                self.assertTrue(INSTALL.tracked_dotfiles_target(repo / "config/.vimrc", "config/.vimrc"))
                self.assertFalse(INSTALL.tracked_dotfiles_target(repo / "unrelated", "config/.vimrc"))

    def test_rejects_foreign_repository_host_and_missing_origin(self) -> None:
        for index, origin in enumerate(("https://other.example.invalid/team/dotfiles.git", "https://forge.example.invalid/team/other.git", "https://github.com/other/dotfiles.git", None)):
            with self.subTest(origin=origin):
                repo = self.checkout(f"foreign-{index}", origin)
                self.assertFalse(INSTALL.tracked_dotfiles_target(repo / "config/.vimrc", "config/.vimrc"))
        self.git(self.invoking, "remote", "remove", "origin")
        repo = self.checkout("missing-invoking", "https://forge.example.invalid/team/dotfiles.git")
        self.assertFalse(INSTALL.tracked_dotfiles_target(repo / "config/.vimrc", "config/.vimrc"))

    def test_historical_dangling_links_require_exact_legacy_path(self) -> None:
        repo = self.checkout("historical", "git@forge.example.invalid:team/dotfiles.git")
        self.git(repo, "rm", "-r", "config/.arduino15", "unrelated")
        self.git(repo, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "Retire paths")
        target = repo / "config/.arduino15"
        self.assertFalse(target.exists())
        self.assertTrue(INSTALL.tracked_dotfiles_target(target, "config/.arduino15"))
        self.assertFalse(INSTALL.tracked_dotfiles_target(target))
        self.assertFalse(INSTALL.tracked_dotfiles_target(repo / "unrelated", "config/.arduino15"))
        home = self.base / "home"
        home.mkdir()
        link = home / ".arduino15"
        link.symlink_to(target)
        self.assertEqual(INSTALL.remove_owned_legacy(home), [str(link)])
        self.assertFalse(link.is_symlink())

    def test_migration_preserves_foreign_links_and_data(self) -> None:
        accepted = self.checkout("accepted", "git@forge.example.invalid:team/dotfiles.git")
        foreign = self.checkout("foreign", "https://other.example.invalid/team/dotfiles.git")
        home = self.base / "home"
        home.mkdir()
        link = home / ".vimrc"
        link.symlink_to(accepted / "config/.vimrc")
        self.assertEqual(INSTALL.ensure_link(self.invoking / "config/.vimrc", link, home), "linked")
        self.assertEqual(link.resolve(), self.invoking / "config/.vimrc")
        link.unlink()
        for target in (foreign / "config/.vimrc", accepted / "unrelated"):
            link.symlink_to(target)
            self.assertEqual(INSTALL.ensure_link(self.invoking / "config/.vimrc", link, home), "conflict")
            self.assertEqual(link.resolve(), target)
            link.unlink()
        legacy = home / ".arduino15"
        legacy.symlink_to(foreign / "config/.arduino15")
        self.assertEqual(INSTALL.remove_owned_legacy(home), [])
        self.assertTrue(legacy.is_symlink())
        self.assertEqual((foreign / "config/.arduino15/keep").read_text(), "preserve me\n")
        link.write_text("personal settings\n")
        self.assertEqual(INSTALL.ensure_link(self.invoking / "config/.vimrc", link, home), "conflict")
        self.assertEqual(link.read_text(), "personal settings\n")
