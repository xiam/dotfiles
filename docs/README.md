# Setup and customization

[Quick start](../README.md)

## Package examples

Install tools with your package manager, then check minimum versions with
`make doctor`:

```sh
# Debian / Ubuntu
sudo apt install vim tmux zsh git make python3 python3-venv
# macOS (Homebrew)
brew install vim tmux zsh git make python
```

Rendering and tests need Jinja2 and PyYAML. Install them in a virtual environment:

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-render.txt
```

OpenSSL is needed for secrets commands and their tests. Formatters and applications
such as btop, htop, and Ghostty are optional; install them separately if you use them.

## Customize

Use the local override files listed in the quick start for personal settings.
To enable format-on-save, add this to `~/.vimrc.local`:

```vim
let g:dotfiles_format_on_save = 1
```

To change colors, edit `theme.yml` and run `make render`. Change other generated
settings through `templates/`, then render again. Do not edit generated files
under `config/` or `exports/` directly.

The installer seeds btop, htop, and Ghostty settings only when their destination
files are absent. It preserves existing settings. For Ghostty's optional terminal
entry, run `make terminfo` (requires `tic`). Add
`exports/windows-terminal-color-scheme.json` manually in Windows Terminal if desired.

## Try another home

Set `DOTFILES_HOME` to choose the installation destination:

```sh
DOTFILES_HOME="$(mktemp -d)" make install
```

Normal installation does not need secrets. Encryption replaces the bundle only
after success; decryption refuses an existing `secrets/` directory. Keep the
password out of command arguments and environment variables; use the prompt.

## Smoke checks

After installing tools and the Python dependencies above:

```sh
make doctor
make test
tmux -f "$HOME/.tmux.conf" -L dotfiles-smoke new-session -d
tmux -L dotfiles-smoke kill-server
```

Run the tmux commands as a pair after `make install`; the isolated socket avoids
your live sessions. Linux tests have passed. macOS and WSL2 checks have not been
run; use these commands on those hosts. In WSL2, use the Linux shell.
