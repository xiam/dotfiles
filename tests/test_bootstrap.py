"""Exercise bootstrap in an isolated fake PATH, without package operations."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


BOOTSTRAP = Path(__file__).resolve().parents[1] / "scripts" / "bootstrap.sh"


class BootstrapTests(unittest.TestCase):
    def run_bootstrap(self, manager="apt-get", absent=(), uid="0", failure=False,
                      old=False, system="Linux"):
        with tempfile.TemporaryDirectory(prefix="bootstrap with spaces ") as temp:
            root = Path(temp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            for name in ("awk", "dirname", "uname", "id"):
                target = shutil.which(name)
                self.assertIsNotNone(target)
                (bin_dir / name).symlink_to(target)
            log = root / "calls"
            state = root / "installed"
            fixture = bin_dir / "fixture"
            fixture.write_text('''#!/bin/sh
name=${0##*/}
case "$name" in
 uname) printf '%s\\n' "$FIXTURE_SYSTEM"; exit 0 ;;
 id) printf '%s\\n' "$FIXTURE_UID"; exit 0 ;;
 sudo) printf 'sudo %s\\n' "$*" >> "$FIXTURE_LOG"; exec "$@" ;;
 apt-get|dnf|pacman|brew)
   printf '%s %s\\n' "$name" "$*" >> "$FIXTURE_LOG"
   [ "$FIXTURE_FAIL" = 0 ] || exit 23
   if [ "$1" = --prefix ]; then printf '%s\\n' "$FIXTURE_PREFIX"; else : > "$FIXTURE_STATE"; fi
   exit 0 ;;
esac
case " $FIXTURE_ABSENT " in
 *" $name "*) [ -f "$FIXTURE_STATE" ] || exit 1 ;;
esac
case "$name" in
 python3)
   if [ "$1" = -c ]; then
     [ "$FIXTURE_OLD" = 0 ] || [ -f "$FIXTURE_STATE" ] || exit 1
   else printf 'setup %s\\n' "$*" >> "$FIXTURE_LOG"; fi ;;
 vim) if [ "$FIXTURE_OLD" = 2 ] || { [ "$FIXTURE_OLD" = 1 ] && [ ! -f "$FIXTURE_STATE" ]; }; then printf 'VIM 8.2\\n'; else printf 'VIM 9.1\\n'; fi ;;
 tmux) printf 'tmux 3.4\\n' ;;
 zsh) printf 'zsh 5.9\\n' ;;
 node) printf 'v22.1.0\\n' ;;
 npm) printf '10.0\\n' ;;
 rustfmt) printf 'rustfmt 1.8\\n' ;;
esac
''')
            fixture.chmod(0o755)
            names = ["python3", "vim", "tmux", "zsh", "git", "make", "tic",
                     "infocmp", "node", "npm", "gofmt", "rustfmt", "sudo",
                     "uname", "id"]
            if manager:
                names.append(manager)
            for name in names:
                path = bin_dir / name
                if path.exists():
                    path.unlink()
                path.symlink_to(fixture)
            # Model an initially missing executable by its inability to run.
            env = dict(os.environ, PATH=str(bin_dir), FIXTURE_SYSTEM=system,
                       FIXTURE_UID=uid, FIXTURE_LOG=str(log), FIXTURE_STATE=str(state),
                       FIXTURE_ABSENT=" ".join(absent), FIXTURE_OLD=str(int(old)),
                       FIXTURE_FAIL=str(int(failure)), FIXTURE_PREFIX=str(root))
            result = subprocess.run(["/bin/sh", str(BOOTSTRAP), "--example"],
                                    env=env, text=True, capture_output=True)
            return result, log.read_text() if log.exists() else ""

    def test_complete_system_skips_package_manager(self):
        result, log = self.run_bootstrap()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(log.startswith("setup "), log)
        self.assertIn("setup.py --example", log)

    def test_pythonless_apt_bootstrap_installs_runtime_and_certificates(self):
        result, log = self.run_bootstrap(absent=("python3",))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("apt-get update", log)
        self.assertIn("python3 python3-venv python3-pip ca-certificates", log)
        self.assertNotIn("sudo", log)

    def test_nonroot_uses_sudo(self):
        result, log = self.run_bootstrap(absent=("python3",), uid="1000")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("sudo apt-get update", log)
        self.assertIn("sudo apt-get install", log)

    def test_manager_failure_stops_before_setup(self):
        result, log = self.run_bootstrap(absent=("python3",), failure=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("package index update failed", result.stderr)
        self.assertNotIn("setup ", log)

    def test_old_minimum_version_is_upgraded(self):
        result, log = self.run_bootstrap(old=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(" vim", log)
        self.assertIn("python3-venv", log)

    def test_unsupported_system_fails_clearly(self):
        result, log = self.run_bootstrap(manager=None, absent=("python3",))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unsupported system", result.stderr)
        self.assertEqual(log, "")

    def test_package_sources_that_cannot_supply_minimum_version_fail(self):
        result, log = self.run_bootstrap(old=2)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("below minimum versions: vim", result.stderr)
        self.assertNotIn("setup ", log)

    def test_other_package_manager_mappings(self):
        for manager, expected in (("dnf", "python3 python3-pip ca-certificates"),
                                  ("pacman", "python python-pip ca-certificates"),
                                  ("brew", "python ca-certificates")):
            with self.subTest(manager=manager):
                result, log = self.run_bootstrap(manager=manager, absent=("python3",),
                                                system="Darwin" if manager == "brew" else "Linux")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(expected, log)
                self.assertNotIn("sudo", log)


if __name__ == "__main__":
    unittest.main()
