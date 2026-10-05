from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PlatformTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory(prefix="dotfiles platform ")
        cls.home = Path(cls.temp.name)
        env = os.environ.copy()
        env["DOTFILES_HOME"] = str(cls.home)
        env["HOME"] = str(cls.home)
        install = subprocess.run(
            [sys.executable, str(ROOT / "scripts/install.py")], env=env, text=True, capture_output=True
        )
        if install.returncode:
            raise RuntimeError(install.stderr)
        cls.env = env

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def test_vim_builtin_filetypes_and_rich_editing(self) -> None:
        vim = shutil.which("vim")
        if not vim:
            self.skipTest("Vim is not installed")
        expected = {
            ".go": "go", ".rs": "rust", ".py": "python", ".js": "javascript",
            ".ts": "typescript", ".jsx": "javascriptreact", ".tsx": "typescriptreact",
            ".yml": "yaml", ".json": "json", ".md": "markdown", ".sh": "sh",
        }
        for extension, filetype in expected.items():
            with self.subTest(extension=extension):
                source = Path(self.temp.name) / ("fixture " + extension)
                result_file = Path(self.temp.name) / ("filetype " + extension)
                source.write_text("sample\n")
                command = [
                    vim, "-Nu", str(self.home / ".vimrc"), "-n", "-i", "NONE", "-es",
                    "-c", "set nomore", "-c", "execute 'edit' fnameescape(" + repr(str(source)) + ")",
                    "-c", "call writefile([&filetype, string(exists('b:current_syntax'))], " + repr(str(result_file)) + ")", "-c", "qa!",
                ]
                result = subprocess.run(command, env=self.env, text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result_file.read_text().splitlines(), [filetype, "1"])

        settings = subprocess.run(
            [vim, "-Nu", str(self.home / ".vimrc"), "-n", "-i", "NONE", "-es", "-c", "call writefile([string(&wrap), string(&undofile)], " + repr(str(Path(self.temp.name) / "vim-settings.txt")) + ")", "-c", "qa!"],
            env=self.env, text=True, capture_output=True,
        )
        self.assertEqual(settings.returncode, 0, settings.stderr)
        self.assertEqual((Path(self.temp.name) / "vim-settings.txt").read_text().splitlines(), ["1", "1"])

    def test_override_precedence_and_absence_are_harmless(self) -> None:
        zsh = shutil.which("zsh")
        git = shutil.which("git")
        vim = shutil.which("vim")
        if not (zsh and git and vim):
            self.skipTest("Vim, Zsh, and Git are required for override smoke checks")
        no_override = subprocess.run([zsh, "-n", str(self.home / ".zshrc")], env=self.env, capture_output=True, text=True)
        self.assertEqual(no_override.returncode, 0, no_override.stderr)

        (self.home / ".vimrc.local").write_text("let g:override_probe = 'vim-local'\n")
        (self.home / ".zshrc.local").write_text("export DOTFILES_OVERRIDE_PROBE=zsh-local\n")
        (self.home / ".gitconfig.local").write_text("[user]\n\tname = local-user\n")
        vim_out = Path(self.temp.name) / "vim-override.txt"
        vim_result = subprocess.run(
            [vim, "-Nu", str(self.home / ".vimrc"), "-n", "-i", "NONE", "-es", "-c", "call writefile([g:override_probe], " + repr(str(vim_out)) + ")", "-c", "qa!"],
            env=self.env, capture_output=True, text=True,
        )
        self.assertEqual(vim_result.returncode, 0, vim_result.stderr)
        self.assertEqual(vim_out.read_text().strip(), "vim-local")
        zsh_result = subprocess.run(
            [zsh, "-c", "source ~/.zshrc; print -r -- $DOTFILES_OVERRIDE_PROBE"],
            env=self.env, capture_output=True, text=True,
        )
        self.assertEqual(zsh_result.returncode, 0, zsh_result.stderr)
        self.assertIn("zsh-local", zsh_result.stdout)
        git_result = subprocess.run([git, "config", "--includes", "--global", "--get", "user.name"], env=self.env, capture_output=True, text=True)
        self.assertEqual(git_result.returncode, 0, git_result.stderr)
        self.assertEqual(git_result.stdout.strip(), "local-user")

    def test_zsh_theme_uses_semantic_truecolor_and_low_color_fallback(self) -> None:
        zsh = shutil.which("zsh")
        if not zsh:
            self.skipTest("Zsh is not installed")
        command = "source ~/.zshrc; print -r -- $DOTFILES_COLOR_USER"
        truecolor_env = self.env.copy()
        truecolor_env["COLORTERM"] = "truecolor"
        truecolor = subprocess.run([zsh, "-c", command], env=truecolor_env, capture_output=True, text=True)
        self.assertEqual(truecolor.returncode, 0, truecolor.stderr)
        self.assertIn("\x1b[38;2;149,127,184m", truecolor.stdout)

        fallback_env = self.env.copy()
        fallback_env["COLORTERM"] = "8bit"
        fallback = subprocess.run([zsh, "-c", command], env=fallback_env, capture_output=True, text=True)
        self.assertEqual(fallback.returncode, 0, fallback.stderr)
        self.assertEqual(fallback.stdout.strip(), "%F{magenta}")

    def test_android_sdk_environment_and_platform_discovery(self) -> None:
        zsh = shutil.which("zsh")
        if not zsh:
            self.skipTest("Zsh is not installed")
        command = 'source ~/.zshrc; print -r -- "HOME=$ANDROID_HOME"; print -r -- "ROOT=$ANDROID_SDK_ROOT"; print -rl -- "${path[@]}"'

        def run_android(env: dict[str, str]) -> tuple[str, str, list[str]]:
            result = subprocess.run([zsh, "-c", command], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            lines = result.stdout.splitlines()
            return lines[0], lines[1], lines[2:]

        home_sdk = self.home / "sdk with spaces"
        legacy_sdk = self.home / "legacy sdk"
        for sdk in (home_sdk, legacy_sdk):
            (sdk / "platform-tools").mkdir(parents=True, exist_ok=True)

        env = self.env.copy()
        env["ANDROID_HOME"] = str(home_sdk)
        env["ANDROID_SDK_ROOT"] = str(legacy_sdk)
        home_line, root_line, paths = run_android(env)
        self.assertEqual(home_line, f"HOME={home_sdk}")
        self.assertEqual(root_line, f"ROOT={legacy_sdk}")
        self.assertIn(str(home_sdk / "platform-tools"), paths)
        self.assertNotIn(str(legacy_sdk / "platform-tools"), paths)

        env = self.env.copy()
        env.pop("ANDROID_HOME", None)
        env["ANDROID_SDK_ROOT"] = str(legacy_sdk)
        home_line, root_line, paths = run_android(env)
        self.assertEqual(home_line, f"HOME={legacy_sdk}")
        self.assertEqual(root_line, f"ROOT={legacy_sdk}")
        self.assertIn(str(legacy_sdk / "platform-tools"), paths)

        env = self.env.copy()
        env["ANDROID_HOME"] = str(self.home / "missing sdk")
        env["ANDROID_SDK_ROOT"] = str(legacy_sdk)
        home_line, root_line, paths = run_android(env)
        self.assertEqual(home_line, f"HOME={legacy_sdk}")
        self.assertEqual(root_line, f"ROOT={legacy_sdk}")
        self.assertIn(str(legacy_sdk / "platform-tools"), paths)

        mac_sdk = self.home / "Library/Android/sdk"
        (mac_sdk / "platform-tools").mkdir(parents=True)
        env = self.env.copy()
        env.pop("ANDROID_HOME", None)
        env.pop("ANDROID_SDK_ROOT", None)
        home_line, root_line, paths = run_android(env)
        self.assertEqual(home_line, f"HOME={mac_sdk}")
        self.assertEqual(root_line, f"ROOT={mac_sdk}")
        self.assertIn(str(mac_sdk / "platform-tools"), paths)

        linux_sdk = self.home / "Android/Sdk"
        (linux_sdk / "platform-tools").mkdir(parents=True)
        (mac_sdk / "platform-tools").rmdir()
        mac_sdk.rmdir()
        env = self.env.copy()
        env.pop("ANDROID_HOME", None)
        env.pop("ANDROID_SDK_ROOT", None)
        home_line, root_line, paths = run_android(env)
        self.assertEqual(home_line, f"HOME={linux_sdk}")
        self.assertEqual(root_line, f"ROOT={linux_sdk}")
        self.assertIn(str(linux_sdk / "platform-tools"), paths)

        (linux_sdk / "platform-tools").rmdir()
        (linux_sdk).rmdir()
        (linux_sdk.parent).rmdir()
        (mac_sdk.parent).rmdir()
        (mac_sdk.parent.parent).rmdir()
        env = self.env.copy()
        env.pop("ANDROID_HOME", None)
        env.pop("ANDROID_SDK_ROOT", None)
        home_line, root_line, paths = run_android(env)
        self.assertEqual(home_line, "HOME=")
        self.assertEqual(root_line, "ROOT=")
        self.assertFalse(any("Android" in path for path in paths))

    def test_missing_optional_tools_are_reported_without_installing(self) -> None:
        doctor_path = os.pathsep.join((str(Path(sys.executable).parent), "/usr/bin", "/bin"))
        with tempfile.TemporaryDirectory(prefix="doctor home ") as home:
            doctor = subprocess.run([sys.executable, str(ROOT / "scripts/doctor.py")], env={"PATH": doctor_path, "HOME": home}, capture_output=True, text=True)
        self.assertEqual(doctor.returncode, 1, doctor.stderr)
        self.assertIn("Default formatter tools", doctor.stdout)
        self.assertIn("Optional applications", doctor.stdout)
        self.assertIn("not found prettier", doctor.stdout)
        self.assertNotIn("apt install", doctor.stdout)

    def test_vim_mapping_preserves_ctrl_j_and_named_formatter(self) -> None:
        vim = shutil.which("vim")
        if not vim:
            self.skipTest("Vim is not installed")
        output = Path(self.temp.name) / "vim-maps.txt"
        command = "call writefile([maparg('<C-j>', 'n'), string(exists(':Format')), string(get(g:, 'dotfiles_format_on_save', -1)), string(&mouse)], " + repr(str(output)) + ")"
        result = subprocess.run(
            [vim, "-Nu", str(self.home / ".vimrc"), "-n", "-i", "NONE", "-es", "-c", command, "-c", "qa!"],
            env=self.env, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        values = output.read_text().splitlines()
        self.assertEqual(values[0], "<C-W>j")
        self.assertEqual(values[1], "2")
        self.assertEqual(values[2], "0")
        self.assertEqual(values[3], "''")

    def test_format_command_keeps_unsaved_buffer_on_success_and_failure(self) -> None:
        vim = shutil.which("vim")
        if not vim:
            self.skipTest("Vim is not installed")
        fake_bin = Path(self.temp.name) / "formatters"
        prettier = fake_bin / "prettier"
        prettier.parent.mkdir(exist_ok=True)
        prettier.write_text("#!/usr/bin/env python3\nimport sys\nsys.stdout.buffer.write(sys.stdin.buffer.read().upper())\n")
        prettier.chmod(0o755)
        source = Path(self.temp.name) / "source files" / "unsaved buffer.tsx"
        source.parent.mkdir(exist_ok=True)
        source.write_text("on-disk\n")
        output = Path(self.temp.name) / "formatted.txt"
        env = self.env.copy()
        env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")
        edit = "execute 'edit' fnameescape(" + repr(str(source)) + ")"
        write = "call writefile(getline(1, '$'), " + repr(str(output)) + ")"
        success = subprocess.run(
            [vim, "-Nu", str(self.home / ".vimrc"), "-n", "-i", "NONE", "-es", "-c", edit,
             "-c", "call setline(1, ['unsaved', 'buffer'])", "-c", "Format", "-c", write, "-c", "qa!"],
            env=env, capture_output=True, text=True,
        )
        self.assertEqual(success.returncode, 0, success.stderr)
        self.assertEqual(output.read_text().splitlines(), ["UNSAVED", "BUFFER"])

        python_formatter = fake_bin / "ruff"
        python_formatter.write_text("#!/usr/bin/env python3\nimport sys\nsys.stderr.write('synthetic formatter failure')\nsys.exit(7)\n")
        python_formatter.chmod(0o755)
        py_source = Path(self.temp.name) / "source files" / "unsaved buffer.py"
        py_source.write_text("on-disk\n")
        edit = "execute 'edit' fnameescape(" + repr(str(py_source)) + ")"
        failure = subprocess.run(
            [vim, "-Nu", str(self.home / ".vimrc"), "-n", "-i", "NONE", "-es", "-c", edit,
             "-c", "call setline(1, ['still unsaved'])", "-c", "Format", "-c", write, "-c", "qa!"],
            env=env, capture_output=True, text=True,
        )
        self.assertEqual(failure.returncode, 0, failure.stderr)
        self.assertEqual(output.read_text().splitlines(), ["still unsaved"])

    def test_real_gofmt_formats_unsaved_go_buffer_and_failure_keeps_it(self) -> None:
        vim = shutil.which("vim")
        gofmt = shutil.which("gofmt")
        if not vim or not gofmt:
            self.skipTest("Vim and gofmt are required for the real Go formatter check")
        source = Path(self.temp.name) / "source files" / "unsaved buffer.go"
        source.parent.mkdir(exist_ok=True)
        source.write_text("package main\n\nfunc main() {}\n")
        output = Path(self.temp.name) / "formatted-go.txt"
        edit = "execute 'edit' fnameescape(" + repr(str(source)) + ")"
        write = "call writefile(getline(1, '$'), " + repr(str(output)) + ")"
        unformatted = ['package main', 'func main(){println("ok")}']
        success = subprocess.run(
            [vim, "-Nu", str(self.home / ".vimrc"), "-n", "-i", "NONE", "-es", "-c", edit,
             "-c", "call deletebufline('%', 2, '$')", "-c", "call setline(1, " + repr(unformatted) + ")", "-c", "Format", "-c", write, "-c", "qa!"],
            env=self.env, capture_output=True, text=True,
        )
        self.assertEqual(success.returncode, 0, success.stderr)
        self.assertEqual(output.read_text(), 'package main\n\nfunc main() { println("ok") }\n')
        self.assertEqual(source.read_text(), "package main\n\nfunc main() {}\n")

        fake_bin = Path(self.temp.name) / "failing gofmt"
        fake_bin.mkdir(exist_ok=True)
        failing_gofmt = fake_bin / "gofmt"
        failing_gofmt.write_text("#!/usr/bin/env python3\nimport sys\nsys.exit(7)\n")
        failing_gofmt.chmod(0o755)
        unchanged = ['package main', 'func main(){println("unsaved")}']
        failing_env = self.env.copy()
        failing_env["PATH"] = str(fake_bin) + os.pathsep + os.pathsep.join(
            part for part in self.env.get("PATH", "").split(os.pathsep) if Path(part, "gofmt").exists() is False
        )
        failure = subprocess.run(
            [vim, "-Nu", str(self.home / ".vimrc"), "-n", "-i", "NONE", "-es", "-c", edit,
             "-c", "call deletebufline('%', 2, '$')", "-c", "call setline(1, " + repr(unchanged) + ")", "-c", "silent! Format", "-c", write, "-c", "qa!"],
            env=failing_env, capture_output=True, text=True,
        )
        self.assertEqual(failure.returncode, 0, failure.stderr)
        self.assertEqual(output.read_text().splitlines(), unchanged)

    def test_persistent_undo_survives_vim_restart(self) -> None:
        vim = shutil.which("vim")
        if not vim:
            self.skipTest("Vim is not installed")
        source = Path(self.temp.name) / "undo-test.txt"
        result_path = Path(self.temp.name) / "undo-result.txt"
        source.write_text("before\n")
        first = subprocess.run(
            [vim, "-Nu", str(self.home / ".vimrc"), "-n", "-i", "NONE", "-es", str(source),
             "-c", "call setline(1, 'after')", "-c", "write", "-c", "qa!"],
            env=self.env, capture_output=True, text=True,
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        second = subprocess.run(
            [vim, "-Nu", str(self.home / ".vimrc"), "-n", "-i", "NONE", "-es", str(source),
             "-c", "undo", "-c", "call writefile(getline(1, '$'), " + repr(str(result_path)) + ")", "-c", "qa!"],
            env=self.env, capture_output=True, text=True,
        )
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(result_path.read_text().splitlines(), ["before"])

    def test_tmux_configuration_and_local_override_on_isolated_server(self) -> None:
        tmux = shutil.which("tmux")
        if not tmux:
            self.skipTest("tmux is not installed")
        (self.home / ".tmux.conf.local").write_text("set -g @dotfiles_override yes\n")
        socket = "dotfiles-override-" + str(os.getpid())
        start = subprocess.run(
            [tmux, "-f", str(self.home / ".tmux.conf"), "-L", socket, "new-session", "-d"],
            env=self.env, capture_output=True, text=True,
        )
        try:
            self.assertEqual(start.returncode, 0, start.stderr)
            option = subprocess.run([tmux, "-L", socket, "show-option", "-gqv", "@dotfiles_override"], env=self.env, capture_output=True, text=True)
            self.assertEqual(option.returncode, 0, option.stderr)
            self.assertEqual(option.stdout.strip(), "yes")
            mouse = subprocess.run([tmux, "-L", socket, "show-option", "-gqv", "mouse"], env=self.env, capture_output=True, text=True)
            self.assertEqual(mouse.stdout.strip(), "off")
            clipboard = subprocess.run([tmux, "-L", socket, "show-option", "-sqv", "set-clipboard"], env=self.env, capture_output=True, text=True)
            self.assertEqual(clipboard.stdout.strip(), "off")
        finally:
            subprocess.run([tmux, "-L", socket, "kill-server"], capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
