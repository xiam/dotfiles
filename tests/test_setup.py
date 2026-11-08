from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import hashlib
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("dotfiles_setup", ROOT / "scripts/setup.py")
SETUP = importlib.util.module_from_spec(spec)
spec.loader.exec_module(SETUP)
FORMAT_SPEC = importlib.util.spec_from_file_location("dotfiles_format", ROOT / "scripts/format.py")
FORMAT = importlib.util.module_from_spec(FORMAT_SPEC)
FORMAT_SPEC.loader.exec_module(FORMAT)


class CompleteSetupTests(unittest.TestCase):
    def setUp(self) -> None:
        previous = os.umask(0o077)
        self.addCleanup(os.umask, previous)


    def test_group_writable_existing_parent_is_preserved_and_refused_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            parent = home / '.local'
            parent.mkdir()
            marker = parent / 'owner-data'
            marker.write_text('preserve existing content')
            parent.chmod(0o775)
            with patch.object(SETUP, 'run') as commands:
                with self.assertRaises(RuntimeError):
                    SETUP.install_python_tools(SETUP.state_directory(home), home)
                commands.assert_not_called()
            self.assertEqual(parent.stat().st_mode & 0o777, 0o775)
            self.assertEqual(marker.read_text(), 'preserve existing content')
            self.assertEqual({path.name for path in parent.iterdir()}, {'owner-data'})

    def test_new_setup_directories_are_private(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            state = SETUP.state_directory(home)
            SETUP.safe_directory(state, home)
            for directory in (home / '.local', home / '.local/share', state):
                self.assertEqual(directory.stat().st_mode & 0o777, 0o700)


    def test_managed_formatters_are_available_without_path_change_and_local_wins(self) -> None:
        with tempfile.TemporaryDirectory(prefix="formatter home ") as temporary:
            home = Path(temporary)
            project = home / "project"
            project.mkdir()
            filename = project / "sample.py"
            for name, relative in (("ruff", "python"), ("prettier", "node")):
                tool = home / ".local/share/dotfiles" / relative / "bin" / name
                tool.parent.mkdir(parents=True)
                tool.write_text("#!/bin/sh\nexit 0\n")
                tool.chmod(0o755)
            with patch.dict(os.environ, {"DOTFILES_HOME": str(home)}), patch.object(FORMAT.shutil, "which", return_value=None):
                self.assertIn(".local/share/dotfiles/python/bin/ruff", FORMAT.formatter("python", filename)[0])
                self.assertIn(".local/share/dotfiles/node/bin/prettier", FORMAT.formatter("typescript", project / "sample.ts")[0])
                local = project / ".venv/bin/ruff"
                local.parent.mkdir(parents=True)
                local.touch()
                self.assertEqual(FORMAT.formatter("python", filename)[0], str(local))
                local.unlink()
                black = local.with_name("black")
                black.touch()
                self.assertEqual(FORMAT.formatter("python", filename)[0], str(black))

    def test_python_network_failure_is_not_marked_complete(self) -> None:
        with tempfile.TemporaryDirectory(prefix="setup home ") as temporary:
            home = Path(temporary)
            state = SETUP.state_directory(home)
            state.mkdir(parents=True)
            calls = []

            def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                calls.append(command)
                if "pip" in command:
                    raise subprocess.CalledProcessError(1, command)
                return subprocess.CompletedProcess(command, 0, "", "")

            with patch.object(SETUP, "run", side_effect=fake_run), patch.object(SETUP, "verify_venv_configuration"):
                with self.assertRaises(subprocess.CalledProcessError):
                    SETUP.install_python_tools(state, home)
            self.assertFalse((state / "python/.requirements").exists())
            self.assertTrue(any("venv" in command for command in calls))
            for flag in ("--require-hashes", "--no-deps", "--only-binary=:all:", "https://pypi.org/simple"):
                self.assertIn(flag, calls[-1])

    def test_symlinked_setup_ancestors_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory(prefix="setup home ") as temporary:
            base = Path(temporary)
            home, foreign = base / "home", base / "foreign"
            home.mkdir()
            foreign.mkdir()
            (home / ".local").symlink_to(foreign)
            with self.assertRaises(RuntimeError):
                SETUP.safe_directory(SETUP.state_directory(home), home)
            self.assertEqual(list(foreign.iterdir()), [])

    def test_cached_venv_cannot_enable_host_startup_modules_or_redirect_its_base(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            environment = Path(temporary)
            configuration = environment / "pyvenv.cfg"
            valid = f"home = {Path(sys._base_executable).resolve().parent}\ninclude-system-site-packages = false\nversion = {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}\n"
            configuration.write_text(valid)
            SETUP.verify_venv_configuration(environment)
            for altered in (valid.replace("= false", "= true"), valid.replace(str(Path(sys._base_executable).resolve().parent), "/unreviewed"), valid + "home = /unreviewed\n"):
                configuration.write_text(altered)
                with self.assertRaises(RuntimeError):
                    SETUP.verify_venv_configuration(environment)

    def test_cached_plugin_git_configuration_cannot_execute_hooks_or_filters(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            (source / ".git").mkdir()
            configuration = source / ".git/config"
            for extension in ("\tfsmonitor = unreviewed-command\n", "[filter \"custom\"]\n\tclean = unreviewed-command\n"):
                configuration.write_text("[core]\n\trepositoryformatversion = 0\n\tbare = false\n" + extension)
                with patch.object(SETUP.subprocess, "run") as commands:
                    self.assertFalse(SETUP.verified_plugin(source, "0" * 40))
                    commands.assert_not_called()
            with patch.dict(os.environ, {"GIT_CONFIG_COUNT": "1", "GIT_TRACE": "1", "GIT_TEMPLATE_DIR": "/unreviewed"}):
                environment = SETUP.plugin_git_environment()
            self.assertNotIn("GIT_CONFIG_COUNT", environment)
            self.assertNotIn("GIT_TRACE", environment)
            self.assertEqual(environment["GIT_CONFIG_GLOBAL"], "/dev/null")
            self.assertEqual(environment["GIT_TEMPLATE_DIR"], "")

    def test_native_npm_tls_overrides_are_rejected_before_execution(self) -> None:
        for override in ({"npm_config_strict_ssl": "false"}, {"NPM_CONFIG_STRICT_SSL": "false"},
                         {"NODE_TLS_REJECT_UNAUTHORIZED": "0"}):
            with self.subTest(override=override), patch.dict(os.environ, override), \
                 patch.object(SETUP.subprocess, "run") as commands:
                with self.assertRaisesRegex(RuntimeError, "TLS verification must remain enabled"):
                    SETUP.run(["npm", "config", "get", "strict-ssl"])
                commands.assert_not_called()

    def test_pinned_plugin_rejects_ignored_executable_files_without_deleting_them(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            checkout = Path(temporary)
            subprocess.run(["git", "init", "--quiet", str(checkout)], check=True)
            plugin = checkout / "plugin/original.vim"
            plugin.parent.mkdir()
            plugin.write_text("let g:original = 1\n")
            subprocess.run(["git", "-C", str(checkout), "add", "."], check=True)
            subprocess.run(["git", "-C", str(checkout), "-c", "user.name=Fixture", "-c",
                            "user.email=fixture@example.invalid", "commit", "--quiet", "-m", "fixture"], check=True)
            commit = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
            self.assertTrue(SETUP.verified_plugin(checkout, commit))
            ignored = checkout / "plugin/personal.vim"
            ignored.write_text("let g:personal = 1\n")
            (checkout / ".git/info/exclude").write_text("plugin/personal.vim\n")
            self.assertFalse(SETUP.verified_plugin(checkout, commit))
            self.assertEqual(ignored.read_text(), "let g:personal = 1\n")

    def test_pinned_plugin_ignores_cached_index_flags_and_preserves_changes(self) -> None:
        for flag, expected in (("--assume-unchanged", "h"), ("--skip-worktree", "S")):
            with self.subTest(flag=flag), tempfile.TemporaryDirectory() as temporary:
                checkout = Path(temporary) / "checkout"
                subprocess.run(["git", "init", "--quiet", str(checkout)], check=True)
                plugin = checkout / "plugin/main.vim"
                plugin.parent.mkdir()
                plugin.write_text("let g:original = 1\n")
                subprocess.run(["git", "-C", str(checkout), "add", "."], check=True)
                subprocess.run(["git", "-C", str(checkout), "-c", "user.name=Fixture", "-c",
                                "user.email=fixture@example.invalid", "commit", "--quiet", "-m", "fixture"], check=True)
                commit = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
                self.assertTrue(SETUP.verified_plugin(checkout, commit))
                subprocess.run(["git", "-C", str(checkout), "update-index", flag, "plugin/main.vim"], check=True)
                plugin.write_text("let g:personal_change = 1\n")
                self.assertFalse(SETUP.verified_plugin(checkout, commit))
                self.assertEqual(plugin.read_text(), "let g:personal_change = 1\n")
                index_state = subprocess.check_output(["git", "-C", str(checkout), "ls-files", "-v"], text=True)
                self.assertTrue(index_state.startswith(expected + " "), index_state)
                home = Path(temporary) / "home"
                home.mkdir()
                state = SETUP.state_directory(home)
                cache = state / "plugins"
                cache.mkdir(parents=True)
                source = cache / f"fixture-{commit}"
                checkout.rename(source)
                manifest_root = Path(temporary) / "source"
                manifest_root.mkdir()
                (manifest_root / "plugins.json").write_text(json.dumps({
                    "fixture": {"commit": commit, "url": "https://github.com/example/fixture.git"}}))
                with patch.object(SETUP, "ROOT", manifest_root), self.assertRaises(RuntimeError):
                    SETUP.install_plugins(state, home)
                self.assertFalse((home / ".vim/pack/dotfiles/start/fixture").exists())
                self.assertEqual((source / "plugin/main.vim").read_text(), "let g:personal_change = 1\n")

    def test_git_replace_refs_cannot_reinterpret_the_pinned_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            checkout = Path(temporary)
            subprocess.run(["git", "init", "--quiet", str(checkout)], check=True)
            plugin = checkout / "main.vim"
            plugin.write_text("original\n")
            commit_command = ["git", "-C", str(checkout), "-c", "user.name=Fixture", "-c",
                              "user.email=fixture@example.invalid", "commit", "--quiet", "-m", "fixture"]
            subprocess.run(["git", "-C", str(checkout), "add", "."], check=True)
            subprocess.run(commit_command, check=True)
            pinned = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
            plugin.write_text("replacement content\n")
            subprocess.run(["git", "-C", str(checkout), "add", "."], check=True)
            subprocess.run(commit_command, check=True)
            replacement = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
            subprocess.run(["git", "-C", str(checkout), "replace", pinned, replacement], check=True)
            subprocess.run(["git", "-C", str(checkout), "update-ref", "HEAD", pinned], check=True)
            self.assertFalse(SETUP.verified_plugin(checkout, pinned))
            self.assertEqual(plugin.read_text(), "replacement content\n")

    def test_help_and_unknown_options_never_mutate_installation_home(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            for option, expected in (("--help", 0), ("--unknown-option", 2)):
                result = subprocess.run([sys.executable, str(SETUP.ROOT / "scripts/setup.py"), option],
                                        env={**os.environ, "DOTFILES_HOME": str(home)},
                                        capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, expected)
                self.assertEqual(list(home.iterdir()), [])

    def test_lock_refresh_preserves_old_environment_without_executing_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            state = SETUP.state_directory(home)
            old = state / "python"
            (old / "bin").mkdir(parents=True)
            (old / "pyvenv.cfg").write_text("old environment\n")
            (old / ".requirements").write_text("obsolete lock\n")
            original = old / "bin/python"
            original.write_text("unverified old interpreter")
            commands = []

            def fake_run(command, **kwargs):
                commands.append(command)
                if "venv" in command:
                    environment = Path(command[-1])
                    (environment / "bin").mkdir(exist_ok=True)
                    (environment / "bin/python").symlink_to(sys.executable)
                    (environment / "pyvenv.cfg").write_text(f"home = {Path(sys._base_executable).resolve().parent}\ninclude-system-site-packages = false\nversion = {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}\n")
                return subprocess.CompletedProcess(command, 0, "", "")

            with patch.object(SETUP, "run", side_effect=fake_run):
                replacement = SETUP.install_python_tools(state, home)
            self.assertNotEqual(replacement.parent.parent, old)
            self.assertEqual((state / "python-current").resolve(), replacement.parent.parent)
            self.assertEqual(original.read_text(), "unverified old interpreter")
            self.assertFalse(any(command[0] == str(original) for command in commands))

    def test_existing_nonvenv_python_never_runs_pip(self) -> None:
        with tempfile.TemporaryDirectory(prefix="setup home ") as temporary:
            home = Path(temporary)
            state = SETUP.state_directory(home)
            binary = state / "python/bin/python"
            binary.parent.mkdir(parents=True)
            binary.symlink_to(sys.executable)
            with patch.object(SETUP, "run") as commands:
                with self.assertRaises(RuntimeError):
                    SETUP.install_python_tools(state, home)
                commands.assert_not_called()
            self.assertTrue(binary.is_symlink())
            self.assertFalse((state / "python/.requirements").exists())

    def test_same_lock_native_base_migration_preserves_old_runtime_without_execution(self) -> None:
        requirements = (ROOT / 'security/requirements-lock.txt').read_text()
        for tag, base_leaf in [('cpython-314', 'base-a'), ('cpython-314', 'base-b'), ('cpython-313', 'base-a')]:
            with self.subTest(cache_tag=tag, base=base_leaf), tempfile.TemporaryDirectory() as temporary:
                home = Path(temporary)
                state = SETUP.state_directory(home)
                old = state / 'python'
                (old / 'bin').mkdir(parents=True)
                configuration = 'home = /previous/native/bin\ninclude-system-site-packages = false\nversion = 3.11.9\n'
                (old / 'pyvenv.cfg').write_text(configuration)
                (old / '.requirements').write_text(requirements)
                original = old / 'bin/python'
                original.write_text('old interpreter must never execute')
                base = home / base_leaf / 'bin/python'
                base.parent.mkdir(parents=True)
                base.touch()
                commands = []

                def fake_run(command, **kwargs):
                    commands.append(command)
                    self.assertNotEqual(command[0], str(original))
                    if 'venv' in command:
                        environment = Path(command[-1])
                        (environment / 'bin').mkdir(exist_ok=True)
                        (environment / 'bin/python').symlink_to(sys.executable)
                        (environment / 'pyvenv.cfg').write_text(
                            f'home = {base.parent}\ninclude-system-site-packages = false\n'
                            f'version = {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}\n')
                    return subprocess.CompletedProcess(command, 0, '', '')

                with patch.object(SETUP.sys, '_base_executable', str(base)), patch.object(SETUP.sys.implementation, 'cache_tag', tag), \
                     patch.object(SETUP, 'run', side_effect=fake_run):
                    replacement = SETUP.install_python_tools(state, home)
                identity = hashlib.sha256((requirements + tag + str(base.resolve())).encode()).hexdigest()
                self.assertEqual(replacement.parent.parent, state / f'python-{identity}')
                self.assertEqual((state / 'python-current').resolve(), replacement.parent.parent)
                self.assertEqual((old / 'pyvenv.cfg').read_text(), configuration)
                self.assertEqual((old / '.requirements').read_text(), requirements)
                self.assertEqual(original.read_text(), 'old interpreter must never execute')
                self.assertTrue(any('venv' in command for command in commands))

    def test_same_lock_malformed_foreign_venv_configuration_rejects_without_execution(self) -> None:
        requirements = (ROOT / 'security/requirements-lock.txt').read_text()
        valid = 'home = /previous/native/bin\ninclude-system-site-packages = false\nversion = 3.11.9\n'
        for configuration in (valid.replace('= false', '= true'), valid + 'home = /duplicate\n',
                              valid.replace('/previous/native/bin', 'relative/bin'), valid.replace('3.11.9', 'unreviewed')):
            with self.subTest(configuration=configuration), tempfile.TemporaryDirectory() as temporary:
                home = Path(temporary)
                state = SETUP.state_directory(home)
                old = state / 'python'
                (old / 'bin').mkdir(parents=True)
                (old / 'pyvenv.cfg').write_text(configuration)
                (old / '.requirements').write_text(requirements)
                (old / 'bin/python').write_text('foreign interpreter')
                with patch.object(SETUP, 'run') as commands:
                    with self.assertRaisesRegex(RuntimeError, 'reviewed venv layout'):
                        SETUP.install_python_tools(state, home)
                    commands.assert_not_called()
                self.assertEqual((old / 'pyvenv.cfg').read_text(), configuration)
                self.assertFalse((state / 'python-current').exists())


    def test_nested_npm_directory_link_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory(prefix="setup home ") as temporary:
            home = Path(temporary)
            foreign = home / "personal tools"
            foreign.mkdir()
            (foreign / "keep").write_text("personal tool\n")
            state = SETUP.state_directory(home)
            prefix = state / "node"
            prefix.mkdir(parents=True)
            (prefix / "bin").symlink_to(foreign)
            with patch.object(SETUP, "run") as commands:
                with self.assertRaises(RuntimeError):
                    SETUP.install_prettier(state, home)
                commands.assert_not_called()
            self.assertEqual((foreign / "keep").read_text(), "personal tool\n")
            self.assertEqual([path.name for path in foreign.iterdir()], ["keep"])

    @unittest.skipUnless(shutil.which("tic") and shutil.which("infocmp"), "terminfo tools unavailable")
    def test_terminfo_compilation_cannot_follow_nested_foreign_links(self) -> None:
        with tempfile.TemporaryDirectory(prefix="terminfo home ") as temporary:
            home = Path(temporary)
            foreign = home / "personal database"
            foreign.mkdir()
            entry = foreign / "xterm-ghostty"
            entry.write_bytes(b"personal terminal definition")
            database = home / ".terminfo"
            database.mkdir()
            for name in ("x", "78"):
                (database / name).symlink_to(foreign)
            with self.assertRaises(RuntimeError):
                SETUP.install_terminfo(home)
            self.assertEqual(entry.read_bytes(), b"personal terminal definition")

    def test_different_terminfo_entries_are_preserved_in_both_layouts(self) -> None:
        for layout in ("x", "78"):
            with self.subTest(layout=layout), tempfile.TemporaryDirectory(prefix="terminfo conflict ") as temporary:
                home = Path(temporary)
                entry = home / ".terminfo" / layout / "xterm-ghostty"
                entry.parent.mkdir(parents=True)
                entry.write_bytes(b"personal terminal definition")

                def compile_fixture(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                    if command[0] == "tic":
                        compiled = Path(command[command.index("-o") + 1]) / layout / "xterm-ghostty"
                        compiled.parent.mkdir()
                        compiled.write_bytes(b"managed terminal definition")
                    return subprocess.CompletedProcess(command, 0, "xterm-ghostty", "")

                with patch.object(SETUP, "run", side_effect=compile_fixture):
                    with self.assertRaisesRegex(RuntimeError, "personal terminfo entry preserved"):
                        SETUP.install_terminfo(home)
                self.assertEqual(entry.read_bytes(), b"personal terminal definition")
                entry.write_bytes(b"managed terminal definition")
                with patch.object(SETUP, "run", side_effect=compile_fixture):
                    SETUP.install_terminfo(home)
                self.assertEqual(entry.read_bytes(), b"managed terminal definition")

    def test_prettier_uses_installation_node_ahead_of_stale_inherited_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="node selection ") as temporary:
            home = Path(temporary)
            state = SETUP.state_directory(home)
            old, new = home / "old/bin", home / "validated/bin"
            old.mkdir(parents=True)
            new.mkdir(parents=True)
            (old / "node").write_text("#!/bin/sh\nexit 9\n")
            (old / "node").chmod(0o755)
            (new / "node").write_text(f"#!{sys.executable}\nimport sys\nsys.stdout.write(sys.stdin.read().upper())\n")
            (new / "node").chmod(0o755)
            with patch.dict(os.environ, {"PATH": str(new) + os.pathsep + str(old)}):
                SETUP.record_runtime(state, home)
            prettier = state / "node/bin/prettier"
            prettier.parent.mkdir(parents=True)
            prettier.write_text("#!/usr/bin/env node\n")
            prettier.chmod(0o755)
            project = home / "project"
            project.mkdir()
            environment = os.environ.copy()
            environment.update(DOTFILES_HOME=str(home), PATH=str(old) + os.pathsep + "/usr/bin:/bin")
            result = subprocess.run([sys.executable, str(ROOT / "scripts/format.py"), "--filetype", "typescript",
                                     "--name", str(project / "sample.ts")], input="hello\n", text=True,
                                    capture_output=True, env=environment)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "HELLO\n")

    def test_doctor_checks_the_running_python_instead_of_stale_path_python(self) -> None:
        with tempfile.TemporaryDirectory(prefix="doctor selection ") as temporary:
            home = Path(temporary)
            binary = home / "bin"
            binary.mkdir()
            (binary / "python3").write_text("#!/bin/sh\nprintf 'Python 3.8.0\\n'\n")
            (binary / "python3").chmod(0o755)
            environment = os.environ.copy()
            environment.update(HOME=str(home), DOTFILES_HOME=str(home), PATH=str(binary) + os.pathsep + environment.get("PATH", ""))
            result = subprocess.run([sys.executable, str(ROOT / "scripts/doctor.py")], env=environment,
                                    capture_output=True, text=True)
            self.assertIn("OK python3", result.stdout)
            self.assertNotIn("MISSING/OLD python3", result.stdout)

    def test_pinned_plugin_fetch_and_repeat_without_source_git_metadata(self) -> None:
        with tempfile.TemporaryDirectory(prefix="plugin fixture ") as temporary:
            base = Path(temporary)
            upstream, source, home = base / "upstream", base / "snapshot", base / "home"
            upstream.mkdir()
            source.mkdir()
            home.mkdir()
            subprocess.run(["git", "init", "-q", str(upstream)], check=True)
            (upstream / "plugin").mkdir()
            (upstream / "plugin/fixture.vim").write_text("let g:fixture = 1\n")
            subprocess.run(["git", "-C", str(upstream), "add", "."], check=True)
            subprocess.run(["git", "-C", str(upstream), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture"], check=True)
            commit = subprocess.check_output(["git", "-C", str(upstream), "rev-parse", "HEAD"], text=True).strip()
            (source / "plugins.json").write_text(json.dumps({"fixture": {"commit": commit, "url": "https://github.com/example/fixture.git"}}))
            state = SETUP.state_directory(home)
            state.mkdir(parents=True)
            actual_run = SETUP.run
            fetches = []

            def local_fetch(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                if "fetch" in command:
                    fetches.append(command)
                    command = [str(upstream) if item == "https://github.com/example/fixture.git" else item for item in command]
                return actual_run(command, **kwargs)

            with patch.object(SETUP, "ROOT", source), patch.object(SETUP, "run", side_effect=local_fetch):
                SETUP.install_plugins(state, home)
                SETUP.install_plugins(state, home)
                self.assertEqual(len(fetches), 1)
                link = home / ".vim/pack/dotfiles/start/fixture"
                self.assertEqual((link / "plugin/fixture.vim").read_text(), "let g:fixture = 1\n")
                self.assertTrue(SETUP.verified_plugin(link.resolve(), commit))
                (link / "plugin/fixture.vim").write_text("personal change\n")
                with self.assertRaises(RuntimeError):
                    SETUP.install_plugins(state, home)
                self.assertEqual((link / "plugin/fixture.vim").read_text(), "personal change\n")

    def test_failed_plugin_fetch_never_links_a_partial_checkout(self) -> None:
        with tempfile.TemporaryDirectory(prefix="plugin fixture ") as temporary:
            home = Path(temporary)
            state = SETUP.state_directory(home)
            state.mkdir(parents=True)
            with patch.object(SETUP, "run", side_effect=subprocess.CalledProcessError(1, ["git", "fetch"])):
                with self.assertRaises(subprocess.CalledProcessError):
                    SETUP.install_plugins(state, home)
            self.assertFalse((home / ".vim/pack/dotfiles/start").exists())
            self.assertEqual(list((state / "plugins").iterdir()), [])

    @unittest.skipUnless(shutil.which("tic") and shutil.which("infocmp"), "terminfo tools unavailable")
    def test_ghostty_terminfo_is_discoverable_in_selected_home_on_repeat(self) -> None:
        with tempfile.TemporaryDirectory(prefix="terminfo home ") as temporary:
            home = Path(temporary)
            SETUP.install_terminfo(home)
            SETUP.install_terminfo(home)
            env = os.environ.copy()
            env.update(HOME=str(home), TERMINFO=str(home / ".terminfo"))
            result = subprocess.run(["infocmp", "xterm-ghostty"], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("xterm-ghostty", result.stdout)


if __name__ == "__main__":
    unittest.main()
