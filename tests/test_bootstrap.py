"""Exercise platform routing and native package-manager failure propagation."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BootstrapTests(unittest.TestCase):
    def invoke(self, distribution='debian', version='13', arch='amd64', system='Linux', failure='', apt_config=''):
        with tempfile.TemporaryDirectory(prefix='bootstrap routing ') as temporary:
            root = Path(temporary)
            (root / 'scripts').mkdir()
            (root / 'security').mkdir()
            source = (ROOT / 'scripts/bootstrap.sh').read_text()
            source = source.replace('PATH=/usr/sbin:/usr/bin:/sbin:/bin', 'PATH="$FIXTURE_BIN:/usr/bin:/bin"')
            source = source.replace('$(uname -s)', '"$FIXTURE_SYSTEM"')
            source = source.replace('/etc/os-release', '"$FIXTURE_RELEASE"')
            source = source.replace('$(dpkg --print-architecture 2>/dev/null || true)', '"$FIXTURE_ARCH"')
            source = source.replace('$(id -u)', '0')
            source = source.replace('/usr/bin/python3', '"$FIXTURE_BIN/python3"')
            (root / 'scripts/bootstrap.sh').write_text(source)
            identity = root / 'os-release'
            identity.write_text(f'ID={distribution}\nVERSION_ID={version}\n')
            for pin in (ROOT / 'security').glob('*.packages.txt'):
                (root / 'security' / pin.name).write_bytes(pin.read_bytes())
            binaries = root / 'bin'
            binaries.mkdir()
            (binaries / 'apt-get').write_text('#!/bin/sh\nprintf "apt:%s\\n" "$*" >> "$FIXTURE_LOG"\n[ "$1" != "$FIXTURE_FAILURE" ]\n')
            (binaries / 'python3').write_text('#!/bin/sh\nprintf "python:%s\\n" "$*" >> "$FIXTURE_LOG"\n')
            for path in binaries.iterdir():
                path.chmod(0o755)
            log = root / 'calls'
            if apt_config:
                override = root / 'insecure-apt.conf'
                override.write_text('APT::Get::AllowUnauthenticated \"true\";\nAcquire::AllowInsecureRepositories \"true\";\n')
                apt_config = str(override)
            result = subprocess.run(['sh', str(root / 'scripts/bootstrap.sh')], text=True, capture_output=True,
                                    env={**os.environ, 'FIXTURE_BIN': str(binaries), 'FIXTURE_RELEASE': str(identity),
                                         'FIXTURE_SYSTEM': system, 'FIXTURE_ARCH': arch, 'FIXTURE_FAILURE': failure,
                                         'FIXTURE_LOG': str(log), 'APT_CONFIG': apt_config})
            return result, log.read_text() if log.exists() else ''

    def test_supported_linux_uses_exact_versions_and_normal_apt(self):
        for distribution, version in [('debian', '13'), ('ubuntu', '24.04'), ('ubuntu', '26.04')]:
            with self.subTest(distribution=distribution, version=version):
                result, log = self.invoke(distribution, version)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('apt:update', log)
                self.assertIn('install --yes --no-install-recommends --no-remove', log)
                self.assertIn('vim=', log)
                self.assertIn('vim-common=', log)
                self.assertIn('python:-I ', log)
                self.assertNotIn('--allow-unauthenticated', log)
                self.assertIn('--no-allow-unauthenticated', log)
                self.assertNotIn('allow-downgrades', log)

    def test_apt_authentication_or_pin_failure_prevents_setup(self):
        for failure in ('update', 'install'):
            result, log = self.invoke(failure=failure)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn('python:', log)

    def test_inherited_apt_configuration_is_rejected_before_root_transaction(self):
        result, log = self.invoke(apt_config='/tmp/unauthenticated-apt.conf')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('APT_CONFIG', result.stderr)
        self.assertEqual(log, '')

    def test_unsupported_platforms_never_install(self):
        for arguments in ({'version': '12'}, {'arch': 'arm64'}, {'system': 'Darwin'}, {'system': 'Windows_NT'}):
            result, log = self.invoke(**arguments)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(log, '')
