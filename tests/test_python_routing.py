"""Managed commands run locally through the installed venv, without renewal."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PythonRoutingTests(unittest.TestCase):
    def test_selected_home_runtime_receives_arguments_without_network_or_policy(self):
        with tempfile.TemporaryDirectory(prefix='python routing ') as temporary:
            home = Path(temporary)
            python = home / '.local/share/dotfiles/python-current/bin/python'
            python.parent.mkdir(parents=True)
            python.write_text('#!/bin/sh\nprintf "<%s>\\n" "$@"\n')
            python.chmod(0o755)
            result = subprocess.run(['sh', str(ROOT / 'scripts/python.sh'), 'scripts/doctor.py', 'with spaces'],
                                    env={**os.environ, 'DOTFILES_HOME': str(home)}, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.splitlines(), ['<-I>', '<scripts/doctor.py>', '<with spaces>'])

    def test_absent_runtime_requires_explicit_install(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(['sh', str(ROOT / 'scripts/python.sh'), 'scripts/doctor.py'],
                                    env={**os.environ, 'DOTFILES_HOME': temporary}, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Managed Python is absent', result.stderr)
            self.assertEqual(list(Path(temporary).iterdir()), [])
