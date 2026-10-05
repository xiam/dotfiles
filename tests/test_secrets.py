from __future__ import annotations

import importlib.util
import io
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("dotfiles_secrets", ROOT / "scripts/secrets.py")
secrets = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(secrets)


class SecretsTests(unittest.TestCase):
    def test_synthetic_encrypt_decrypt_install_and_repeated_install(self) -> None:
        with tempfile.TemporaryDirectory(prefix="synthetic credentials ") as name:
            root = Path(name) / "repo"
            home = Path(name) / "home with spaces"
            source = root / "secrets/.config/ssh keys/id_test"
            source.parent.mkdir(parents=True)
            source.write_text("synthetic credential only\n")
            source.chmod(0o600)
            bundle = root / "secrets.tar.gz.enc"
            secrets.encrypt_bundle(root, "synthetic passphrase", bundle)

            restored_root = Path(name) / "restored"
            restored_root.mkdir()
            restored = secrets.decrypt_bundle(restored_root, "synthetic passphrase", bundle)
            restored_file = restored / ".config/ssh keys/id_test"
            self.assertEqual(restored_file.read_text(), "synthetic credential only\n")
            self.assertEqual(restored.stat().st_mode & 0o777, 0o700)
            self.assertEqual(restored_file.stat().st_mode & 0o777, 0o600)

            installed, conflicts = secrets.install_secret_links(restored_root, home)
            self.assertEqual(conflicts, [])
            self.assertEqual(len(installed), 1)
            link = home / ".config/ssh keys/id_test"
            self.assertTrue(link.is_symlink())
            self.assertEqual(link.resolve(), restored_file.resolve())
            self.assertEqual(bundle.stat().st_mode & 0o777, 0o600)
            again, conflicts_again = secrets.install_secret_links(restored_root, home)
            self.assertEqual(conflicts_again, [])
            self.assertEqual(again, installed)

    def test_failed_decrypt_leaves_no_partial_secret_tree_or_home_link(self) -> None:
        with tempfile.TemporaryDirectory(prefix="synthetic credentials ") as name:
            root = Path(name) / "repo"
            root.mkdir()
            source_root = Path(name) / "source"
            (source_root / "secrets").mkdir(parents=True)
            (source_root / "secrets/token").write_text("synthetic token\n")
            bundle = root / "secrets.tar.gz.enc"
            secrets.encrypt_bundle(source_root, "right synthetic passphrase", bundle)
            with self.assertRaises(RuntimeError):
                secrets.decrypt_bundle(root, "wrong synthetic passphrase", bundle)
            self.assertFalse((root / "secrets").exists())
            self.assertEqual(list(root.glob(".secrets-stage-*")), [])
            self.assertFalse((Path(name) / "home/token").exists())

    def test_failed_encryption_preserves_previous_bundle(self) -> None:
        with tempfile.TemporaryDirectory(prefix="synthetic credentials ") as name:
            root = Path(name)
            (root / "secrets").mkdir()
            (root / "secrets/synthetic").write_text("synthetic only\n")
            bundle = root / "secrets.tar.gz.enc"
            bundle.write_bytes(b"previous encrypted bundle")
            with patch.object(secrets, "openssl", side_effect=RuntimeError("synthetic encryption failure")):
                with self.assertRaises(RuntimeError):
                    secrets.encrypt_bundle(root, "synthetic passphrase", bundle)
            self.assertEqual(bundle.read_bytes(), b"previous encrypted bundle")
            self.assertEqual(list(root.glob(".secrets-encrypted-*")), [])

    def test_archive_path_traversal_is_rejected(self) -> None:
        payload = io.BytesIO()
        with tarfile.open(fileobj=payload, mode="w:gz") as archive:
            member = tarfile.TarInfo("secrets/../../outside")
            content = b"must not escape"
            member.size = len(content)
            archive.addfile(member, io.BytesIO(content))
        with tempfile.TemporaryDirectory(prefix="synthetic secrets ") as name:
            with self.assertRaises(RuntimeError):
                secrets.extract_archive(payload.getvalue(), Path(name) / "stage")
            self.assertFalse((Path(name) / "outside").exists())

    def test_unmanaged_credential_conflict_is_preserved_and_reported(self) -> None:
        with tempfile.TemporaryDirectory(prefix="synthetic credentials ") as name:
            root = Path(name) / "repo"
            source = root / "secrets/.ssh/config"
            source.parent.mkdir(parents=True)
            source.write_text("Host synthetic\n")
            home = Path(name) / "home"
            (home / ".ssh").mkdir(parents=True)
            target = home / ".ssh/config"
            target.write_text("Host user-owned\n")
            installed, conflicts = secrets.install_secret_links(root, home)
            self.assertEqual(installed, [])
            self.assertEqual(conflicts, [str(target)])
            self.assertEqual(target.read_text(), "Host user-owned\n")

    def test_symlinked_credential_directory_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory(prefix="synthetic credentials ") as name:
            root = Path(name) / "repo"
            source = root / "secrets/.ssh/authorized keys"
            source.parent.mkdir(parents=True)
            source.write_text("synthetic key\n")
            home = Path(name) / "home"
            home.mkdir()
            foreign = Path(name) / "ssh directory"
            foreign.mkdir()
            (foreign / "keep").write_text("user data\n")
            (home / ".ssh").symlink_to(foreign, target_is_directory=True)
            installed, conflicts = secrets.install_secret_links(root, home)
            self.assertEqual(installed, [])
            self.assertEqual(conflicts, [str(home / ".ssh/authorized keys")])
            self.assertEqual(list(foreign.iterdir()), [foreign / "keep"])


if __name__ == "__main__":
    unittest.main()
