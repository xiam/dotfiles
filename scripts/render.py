#!/usr/bin/env python3
"""Render tracked workstation files from Jinja2 templates and semantic YAML."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
    from jinja2 import Environment, FileSystemLoader, StrictUndefined
except ImportError as exc:
    raise SystemExit(
        "Rendering requires Python 3.10+, Jinja2, and PyYAML. "
        "Install them with: python3 -m pip install -r requirements-render.txt"
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = {
    "vimrc.j2": "config/.vimrc",
    "tmux.conf.j2": "config/.tmux.conf",
    "zshrc.j2": "config/.zshrc",
    "gitconfig.j2": "config/.gitconfig",
    "vim-theme.vim.j2": "config/.vim/colors/dotfiles.vim",
    "btop.theme.j2": "config/.config/btop/themes/dotfiles.theme",
    "ghostty.conf.j2": "config/.config/ghostty/themes/dotfiles",
    "ghostty-config.j2": "config/.config/ghostty/config",
    "windows-terminal-color-scheme.json.j2": "exports/windows-terminal-color-scheme.json",
}


def rgb(color: str) -> str:
    return ",".join(str(int(color[index:index + 2], 16)) for index in (1, 3, 5))


def main() -> int:
    theme_data = yaml.safe_load((ROOT / "theme.yml").read_text(encoding="utf-8"))
    theme = theme_data.get("theme", {})
    required = {
        "name", "bg", "surface", "surface2", "fg", "fg_dim", "pane_inactive_fg",
        "muted", "subtle", "accent1", "accent2", "accent3", "cyan", "warning",
        "orange", "error", "success",
        "fallback_user", "fallback_host", "fallback_path", "fallback_git",
    }
    missing = sorted(required - set(theme))
    if missing:
        raise SystemExit(f"theme.yml is missing semantic tokens: {', '.join(missing)}")
    ansi = {"black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"}
    for key in ("fallback_user", "fallback_host", "fallback_path", "fallback_git"):
        if theme[key] not in ansi:
            raise SystemExit(f"theme token {key} must be a standard ANSI color name")
    color_tokens = required - {
        "name", "fallback_user", "fallback_host", "fallback_path", "fallback_git"
    }
    for key in color_tokens:
        value = theme[key]
        if not isinstance(value, str) or len(value) != 7 or not value.startswith("#"):
            raise SystemExit(f"theme token {key} must be a #RRGGBB color")
        try:
            int(value[1:], 16)
        except ValueError:
            raise SystemExit(f"theme token {key} must be a #RRGGBB color")

    env = Environment(
        loader=FileSystemLoader(ROOT / "templates"),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        autoescape=False,
    )
    env.filters["rgb"] = rgb
    for template_name, relative_output in OUTPUTS.items():
        output = ROOT / relative_output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            env.get_template(template_name).render(theme=theme),
            encoding="utf-8",
        )
        print(f"rendered {relative_output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
