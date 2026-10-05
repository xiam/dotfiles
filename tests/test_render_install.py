from __future__ import annotations

import os
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def run(*args: str, env: dict[str, str] | None = None, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True)


class RenderAndInstallTests(unittest.TestCase):
    def test_templates_are_fresh_and_bindings_are_preserved(self) -> None:
        generated = [
            ROOT / "config/.vimrc", ROOT / "config/.tmux.conf", ROOT / "config/.zshrc",
            ROOT / "config/.gitconfig", ROOT / "config/.vim/colors/dotfiles.vim",
            ROOT / "config/.config/btop/themes/dotfiles.theme", ROOT / "config/.config/ghostty/themes/dotfiles",
            ROOT / "config/.config/ghostty/config", ROOT / "exports/windows-terminal-color-scheme.json",
        ]
        before = {path: path.read_bytes() for path in generated}
        result = run(sys.executable, "scripts/render.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(before, {path: path.read_bytes() for path in generated})

        vim = (ROOT / "config/.vimrc").read_text()
        tmux = (ROOT / "config/.tmux.conf").read_text()
        zsh = (ROOT / "config/.zshrc").read_text()
        for binding in (
            'let mapleader = " "', "nnoremap <C-T> :tabnew<CR>:e .<CR>",
            "nnoremap <C-P> :tabprev<CR>", "nnoremap <C-N> :tabnext<CR>",
            r"nnoremap <C-W>\| :vsplit .<CR>", r"nnoremap <C-W>- :split .<CR>",
            "nnoremap <C-h> <C-W>h", "nnoremap <C-j> <C-W>j", "nnoremap <C-k> <C-W>k",
            "nnoremap <C-l> <C-W>l", "nnoremap <C-Q> :q<CR>", "inoremap jk <Esc>",
            "nnoremap <leader>w :w<CR>", "nnoremap <leader>/ :nohlsearch<CR>",
            'nnoremap <leader>ap :%d _<CR>"0P',
        ):
            self.assertIn(binding, vim)
        for binding in (
            "set -g prefix C-b", "set -s set-clipboard off", "bind | split-window -h -c", "bind - split-window -v -c",
            "bind '\"' split-window -v -c", "bind % split-window -h -c", "bind r source-file",
            "bind h select-pane -L", "bind j select-pane -D", "bind k select-pane -U", "bind l select-pane -R",
            "bind -n M-h select-pane -L", "bind -n M-j select-pane -D", "bind -n M-k select-pane -U", "bind -n M-l select-pane -R",
            "bind -n M-Left select-pane -L", "bind -n M-Right select-pane -R", "bind -n M-Up select-pane -U", "bind -n M-Down select-pane -D",
            "bind -r H resize-pane -L 5", "bind -r J resize-pane -D 5", "bind -r K resize-pane -U 5", "bind -r L resize-pane -R 5",
            *[f"bind -n M-{i} select-window -t {i}" for i in range(1, 10)],
            "bind c new-window -c", "bind x kill-pane", "bind X kill-window",
            "bind S setw synchronize-panes", "bind m set-option -g mouse on", "bind M set-option -g mouse off",
            "bind -T copy-mode-vi v send -X begin-selection", "bind -T copy-mode-vi y send -X copy-selection-and-cancel",
            "bind -T root F12", "bind -T off F12",
        ):
            self.assertIn(binding, tmux)
        self.assertIn("bindkey -e", zsh)
        self.assertIn("38;2;149,127,184", zsh)
        self.assertIn("DOTFILES_COLOR_USER='%F{magenta}'", zsh)
        self.assertNotIn("<C-J>", vim)
        self.assertNotIn("vim_ai", vim.lower())
        self.assertNotIn("copilot", vim.lower())
        self.assertNotIn("pathogen", vim.lower())

    def test_semantic_theme_contrast_and_fallback_colors(self) -> None:
        theme = yaml.safe_load((ROOT / "theme.yml").read_text())["theme"]

        def luminance(color: str) -> float:
            channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
            linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
            return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

        def ratio(first: str, second: str) -> float:
            lighter, darker = sorted((luminance(first), luminance(second)), reverse=True)
            return (lighter + 0.05) / (darker + 0.05)

        for foreground in ("fg", "fg_dim", "muted", "pane_inactive_fg"):
            self.assertGreaterEqual(ratio(theme["bg"], theme[foreground]), 4.5, foreground)
        self.assertGreaterEqual(ratio(theme["surface"], theme["muted"]), 4.5)
        vim_theme = (ROOT / "config/.vim/colors/dotfiles.vim").read_text()
        self.assertIn("ctermfg=252", vim_theme)
        self.assertIn("ctermbg=234", vim_theme)
        windows_scheme = json.loads((ROOT / "exports/windows-terminal-color-scheme.json").read_text())
        self.assertEqual(windows_scheme["name"], "Kanagawa")
        self.assertEqual(windows_scheme["background"], theme["bg"])

    def test_disposable_home_repeat_override_and_mutable_settings(self) -> None:
        with tempfile.TemporaryDirectory(prefix="dotfiles home ") as name:
            home = Path(name)
            (home / ".vim").mkdir()
            (home / ".vim/pack/user/start/keep-plugin").mkdir(parents=True)
            (home / ".vim/pack/user/start/keep-plugin/marker").write_text("foreign\n")
            (home / ".vimrc.local").write_text("let g:local_override = 1\n")
            (home / ".tmux.conf.local").write_text("set -g status-interval 19\n")
            (home / ".zshrc.local").write_text("export DOTFILES_LOCAL_OVERRIDE=present\n")
            (home / ".gitconfig.local").write_text("[user]\n\tname = Local Name\n")
            (home / ".config/btop").mkdir(parents=True)
            (home / ".config/btop/btop.conf").write_text("color_theme = \"user-theme\"\n")
            (home / ".config/ghostty").mkdir(parents=True)
            (home / ".config/ghostty/config").write_text("font-size = 13\n")
            env = os.environ.copy()
            env["DOTFILES_HOME"] = str(home)
            first = run(sys.executable, "scripts/install.py", env=env)
            self.assertEqual(first.returncode, 0, first.stderr)
            second = run(sys.executable, "scripts/install.py", env=env)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertTrue((home / ".vimrc").is_symlink())
            self.assertTrue((home / ".tmux.conf").is_symlink())
            self.assertEqual((home / ".vimrc.local").read_text(), "let g:local_override = 1\n")
            self.assertEqual((home / ".tmux.conf.local").read_text(), "set -g status-interval 19\n")
            self.assertEqual((home / ".zshrc.local").read_text(), "export DOTFILES_LOCAL_OVERRIDE=present\n")
            self.assertEqual((home / ".gitconfig.local").read_text(), "[user]\n\tname = Local Name\n")
            self.assertEqual((home / ".config/btop/btop.conf").read_text(), "color_theme = \"user-theme\"\n")
            self.assertEqual((home / ".config/ghostty/config").read_text(), "font-size = 13\n")
            self.assertEqual((home / ".vim/pack/user/start/keep-plugin/marker").read_text(), "foreign\n")
            self.assertTrue((home / ".config/btop/themes/dotfiles.theme").is_file())

    def test_unmanaged_dotfile_conflict_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory(prefix="dotfiles home ") as name:
            home = Path(name)
            home.mkdir(exist_ok=True)
            (home / ".tmux.conf").write_text("user configuration\n")
            env = os.environ.copy()
            env["DOTFILES_HOME"] = str(home)
            result = run(sys.executable, "scripts/install.py", env=env)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual((home / ".tmux.conf").read_text(), "user configuration\n")
            self.assertIn("conflict preserved", result.stderr)

    def test_symlinked_application_directories_are_not_modified(self) -> None:
        with tempfile.TemporaryDirectory(prefix="dotfiles home ") as name:
            root = Path(name)
            home = root / "home"
            home.mkdir()
            foreign_vim = root / "user vim"
            foreign_vim.mkdir()
            vim_marker = foreign_vim / "keep"
            vim_marker.write_text("user plugin tree\n")
            (home / ".vim").symlink_to(foreign_vim, target_is_directory=True)
            foreign_config = root / "user config"
            foreign_config.mkdir()
            config_marker = foreign_config / "keep"
            config_marker.write_text("user app settings\n")
            (home / ".config").symlink_to(foreign_config, target_is_directory=True)
            env = os.environ.copy()
            env["DOTFILES_HOME"] = str(home)
            result = run(sys.executable, "scripts/install.py", env=env)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(vim_marker.read_text(), "user plugin tree\n")
            self.assertEqual(config_marker.read_text(), "user app settings\n")
            self.assertEqual(list(foreign_vim.iterdir()), [vim_marker])
            self.assertEqual(list(foreign_config.iterdir()), [config_marker])

    def test_repo_owned_legacy_link_is_removed_without_touching_foreign_tree(self) -> None:
        with tempfile.TemporaryDirectory(prefix="dotfiles home ") as name:
            root = Path(name)
            home = root / "home"
            home.mkdir()
            old_checkout = root / "old-dotfiles"
            arduino = old_checkout / "config/.arduino15"
            arduino.mkdir(parents=True)
            (arduino / "config.yaml").write_text("synthetic legacy config\n")
            (old_checkout / "README.md").write_text("unrelated tracked file\n")
            run("git", "init", "-q", str(old_checkout))
            run("git", "-C", str(old_checkout), "remote", "add", "origin", "https://github.com/xiam/dotfiles.git")
            run("git", "-C", str(old_checkout), "add", "config/.arduino15/config.yaml", "README.md")
            tracked = arduino
            link = home / ".arduino15"
            link.symlink_to(tracked, target_is_directory=True)
            unrelated_tracked_link = home / ".config/vim-ai"
            unrelated_tracked_link.parent.mkdir(parents=True)
            unrelated_tracked_link.symlink_to(old_checkout / "README.md")
            foreign_plugin = home / ".vim/pack/user/start/foreign"
            foreign_plugin.mkdir(parents=True)
            marker = foreign_plugin / "keep"
            marker.write_text("preserve\n")
            env = os.environ.copy()
            env["DOTFILES_HOME"] = str(home)
            result = run(sys.executable, "scripts/install.py", env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(link.exists())
            self.assertFalse(link.is_symlink())
            self.assertTrue(unrelated_tracked_link.is_symlink())
            self.assertEqual(marker.read_text(), "preserve\n")

    def test_moved_plugin_link_is_removed_only_when_its_old_path_was_tracked(self) -> None:
        with tempfile.TemporaryDirectory(prefix="dotfiles home ") as name:
            root = Path(name)
            home = root / "home"
            home.mkdir()
            old_checkout = root / "old-dotfiles"
            plugin_file = old_checkout / "config/.vim/bundle/rust.vim/plugin/rust.vim"
            plugin_file.parent.mkdir(parents=True)
            plugin_file.write_text("synthetic old plugin\n")
            run("git", "init", "-q", str(old_checkout))
            run("git", "-C", str(old_checkout), "config", "user.name", "Fixture")
            run("git", "-C", str(old_checkout), "config", "user.email", "fixture@example.invalid")
            run("git", "-C", str(old_checkout), "remote", "add", "origin", "https://github.com/xiam/dotfiles.git")
            run("git", "-C", str(old_checkout), "add", "config/.vim/bundle/rust.vim")
            run("git", "-C", str(old_checkout), "commit", "-qm", "old plugin path")
            stale_target = old_checkout / "config/.vim/bundle/rust.vim"
            link = home / ".vim/bundle/rust.vim"
            link.parent.mkdir(parents=True)
            link.symlink_to(stale_target, target_is_directory=True)
            run("git", "-C", str(old_checkout), "rm", "-qr", "config/.vim/bundle/rust.vim")
            run("git", "-C", str(old_checkout), "commit", "-qm", "move plugin path")
            env = os.environ.copy()
            env["DOTFILES_HOME"] = str(home)
            result = run(sys.executable, "scripts/install.py", env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(link.is_symlink())


if __name__ == "__main__":
    unittest.main()
