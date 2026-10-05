from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORMAT = ROOT / "scripts/format.py"


def executable(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/usr/bin/env python3\n" + body)
    path.chmod(0o755)


class FormatterTests(unittest.TestCase):
    def test_supported_filetypes_choose_deterministic_tools(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project with spaces ") as name:
            project = Path(name)
            cases = {
                "go": "gofmt", "rust": "rustfmt", "python": "ruff",
                "javascript": "prettier", "javascriptreact": "prettier",
                "typescript": "prettier", "typescriptreact": "prettier",
                "yaml": "prettier", "json": "prettier", "markdown": "prettier",
            }
            for filetype, tool in cases.items():
                filename = project / "file with spaces.txt"
                filename.touch()
                env = os.environ.copy()
                fake_bin = project / "fake-bin"
                fake_bin.mkdir(exist_ok=True)
                fake_tool = project / ".cargo/bin/rustfmt" if filetype == "rust" else fake_bin / tool
                executable(fake_tool, "import sys\nsys.stdout.buffer.write(sys.stdin.buffer.read())\n")
                env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")
                result = subprocess.run(
                    [sys.executable, str(FORMAT), "--filetype", filetype, "--name", str(filename)],
                    input="sample\n", text=True, capture_output=True, env=env,
                )
                self.assertEqual(result.returncode, 0, f"{filetype}: {result.stderr}")
                self.assertEqual(result.stdout, "sample\n")

    def test_project_local_prettier_wins_and_receives_spaced_filename(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project with spaces ") as name:
            project = Path(name)
            filename = project / "src" / "a file.tsx"
            filename.parent.mkdir()
            filename.touch()
            (project / "package.json").write_text("{}\n")
            record = project / "arguments.json"
            cwd_record = project / "formatter-cwd.txt"
            local_prettier = project / "node_modules/.bin/prettier"
            executable(
                local_prettier,
                "import json, os, sys\n"
                "open(os.environ['ARGS_RECORD'], 'w').write(json.dumps(sys.argv[1:]))\n"
                "open(os.environ['CWD_RECORD'], 'w').write(os.getcwd())\n"
                "sys.stdout.buffer.write(sys.stdin.buffer.read().upper())\n",
            )
            env = os.environ.copy()
            env["ARGS_RECORD"] = str(record)
            env["CWD_RECORD"] = str(cwd_record)
            result = subprocess.run(
                [sys.executable, str(FORMAT), "--filetype", "typescriptreact", "--name", str(filename)],
                input="hello\n", text=True, capture_output=True, env=env,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "HELLO\n")
            args = json.loads(record.read_text())
            self.assertEqual(args[0], "--stdin-filepath")
            self.assertEqual(args[1], str(filename.resolve()))
            self.assertEqual(cwd_record.read_text(), str(project))

    def test_go_prefers_goimports_when_both_tools_are_available(self) -> None:
        with tempfile.TemporaryDirectory(prefix="go project ") as name:
            root = Path(name)
            filename = root / "file.go"
            filename.touch()
            fake_bin = root / "bin"
            for tool in ("goimports", "gofmt"):
                executable(fake_bin / tool, f"import sys\nsys.stdout.write('{tool}')\n")
            env = os.environ.copy()
            env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")
            result = subprocess.run(
                [sys.executable, str(FORMAT), "--filetype", "go", "--name", str(filename)],
                input="source\n", text=True, capture_output=True, env=env,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "goimports")

    def test_real_gofmt_formats_stdin_without_a_dash_filename(self) -> None:
        gofmt = shutil.which("gofmt")
        if not gofmt:
            self.skipTest("gofmt is not installed")
        with tempfile.TemporaryDirectory(prefix="go project ") as name:
            filename = Path(name) / "file with spaces.go"
            filename.touch()
            env = os.environ.copy()
            env["PATH"] = str(Path(gofmt).parent) + os.pathsep + env.get("PATH", "")
            result = subprocess.run(
                [sys.executable, str(FORMAT), "--filetype", "go", "--name", str(filename)],
                input="package main\nfunc main(){println(\"ok\")}\n",
                text=True,
                capture_output=True,
                env=env,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, 'package main\n\nfunc main() { println("ok") }\n')

    def test_real_rustfmt_reads_stdin_without_a_dash_filename(self) -> None:
        rustfmt = shutil.which("rustfmt")
        if not rustfmt:
            self.skipTest("rustfmt is not installed")
        with tempfile.TemporaryDirectory(prefix="rust project ") as name:
            filename = Path(name) / "file with spaces.rs"
            filename.touch()
            env = os.environ.copy()
            env["PATH"] = str(Path(rustfmt).parent) + os.pathsep + env.get("PATH", "")
            result = subprocess.run(
                [sys.executable, str(FORMAT), "--filetype", "rust", "--name", str(filename)],
                input="fn main(){println!(\"ok\");}\n",
                text=True,
                capture_output=True,
                env=env,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, 'fn main() {\n    println!("ok");\n}\n')

    def test_formatter_failure_and_missing_tool_return_nonzero_without_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="formatter ") as name:
            root = Path(name)
            filename = root / "file.py"
            filename.touch()
            fake_bin = root / "bin"
            executable(fake_bin / "ruff", "import sys\nsys.stderr.write('synthetic failure')\nsys.exit(7)\n")
            env = os.environ.copy()
            env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")
            failed = subprocess.run(
                [sys.executable, str(FORMAT), "--filetype", "python", "--name", str(filename)],
                input="unchanged\n", text=True, capture_output=True, env=env,
            )
            self.assertEqual(failed.returncode, 7)
            self.assertEqual(failed.stdout, "")
            self.assertIn("buffer was not changed", failed.stderr)

            empty_path = subprocess.run(
                [sys.executable, str(FORMAT), "--filetype", "python", "--name", str(filename)],
                input="unchanged\n", text=True, capture_output=True, env={"PATH": str(fake_bin)},
            )
            self.assertNotEqual(empty_path.returncode, 0)
            self.assertEqual(empty_path.stdout, "")


if __name__ == "__main__":
    unittest.main()
