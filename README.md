# Workstation dotfiles

Vim, tmux, and Zsh settings for Linux, macOS, and WSL2.
Tested on Linux; macOS and WSL2 have not been tested. Native Windows shells
are not supported.

## Install

Requires Git and Make to start. Installation supplies Vim 9.0+, tmux 3.2+,
Zsh 5.8+, Python 3.10+, pinned Vim plugins, formatters, and Ghostty terminfo.

```sh
git clone https://github.com/xiam/dotfiles.git
cd dotfiles
make install
```

`make install` uses apt, dnf, pacman, or Homebrew to install missing system tools.
It downloads user-local Python and JavaScript tools and pinned Vim plugins.
Linux package installation may ask for sudo access; secrets stay separate.
Conflicting personal files stay in place. Installation reports conflicts so you
can choose which personal settings to retain before rerunning.
Existing application settings and local overrides are preserved.

Run `make doctor` to inspect the installed tools.

## Format in Vim

Run `:Format` to format the current buffer. Installation includes gofmt, rustfmt,
Ruff, and Prettier:

| Language | Formatter, in preference order |
|---|---|
| Go | goimports, gofmt |
| Rust | rustfmt |
| Python | Ruff, Black |
| JS/TS/JSX/TSX, YAML, JSON, Markdown | Prettier |

Project-local tools and configuration take precedence. Missing tools or formatter
errors leave the buffer unchanged. Formatting on save is off by default.

## Local settings

Put machine-specific settings in these files; they load last:

- `~/.vimrc.local`
- `~/.tmux.conf.local`
- `~/.zshrc.local`
- `~/.gitconfig.local` — set your Git identity here.

## Secrets (optional)

Requires OpenSSL. Keep plaintext in the gitignored `secrets/` directory using
home-relative paths.

- `make secrets-encrypt` — create or replace `secrets.tar.gz.enc`.
- `make secrets-install` — decrypt and link files into your home.
- `make secrets-decrypt` — extract locally without installing.

These commands prompt for a password. Existing credentials or plaintext are
not overwritten; failed decryption installs nothing. Normal installation never
asks for a password.

See the [setup and customization guide](docs/README.md) for package examples,
themes, save-time formatting, alternate homes, and smoke checks.
