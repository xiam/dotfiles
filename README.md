# Workstation dotfiles

Vim, tmux, and Zsh settings for Linux, macOS, and WSL2.
Tested on Linux; macOS and WSL2 have not been tested. Native Windows shells
are not supported.

## Install

Requires Git and Make. Installation uses the operating system's package manager
for native tools, pip for Python packages, npm for Prettier, and Git for Vim plugins.

```sh
git clone https://github.com/xiam/dotfiles.git
cd dotfiles
make install
```

Supported installation profiles cover Debian 13 amd64 and Ubuntu Server 24.04
and 26.04 amd64. macOS installation remains disabled and untested. Other
platforms are rejected. WSL2 uses its supported Linux distribution; WSL-specific
execution has not been tested.

Native package versions are pinned in `security/*.packages.txt`. APT uses the
host's configured repositories and their normal signature and archive-hash checks.
Python packages use the committed requirements hashes; npm uses its lockfile's
integrity checks; Vim plugins use exact Git commits. TLS verification remains
enabled. These pins and hashes identify versions and content; they do not claim
independent authorship verification or continuous security assessment.

Installation needs network access and may request sudo on Linux. Missing pinned
versions or repository authentication failures stop installation. Update pins
through normal repository changes when needed. There is no custom admission,
freshness, renewal, or expiry policy.

Conflicting personal files stay in place. Installation reports conflicts so you
can choose which settings to retain before rerunning. Application settings and
local overrides are preserved. Secrets stay separate.

Run `make doctor` to inspect installed tools and minimum versions. Formatting,
rendering, tests, and secrets commands use the installed Python environment
without downloading packages or rechecking package evidence. Run `make install`
separately to install or update dependencies.

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
Owner-selected project/PATH formatter overrides and local configuration remain
trusted customization inputs.

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
