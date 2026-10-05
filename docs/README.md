# Setup and customization

[Quick start](../README.md)

## Automatic setup

Run `make install` after cloning. Git and Make are entry prerequisites.
The installer supports Debian/Ubuntu (including their WSL distributions), Fedora,
Arch, and macOS with Homebrew. Package installation needs internet access and
may request sudo on Linux. Unsupported package managers or insufficient package
versions fail with an error rather than report a complete installation.

Python dependencies and Ruff live in `~/.local/share/dotfiles/python`.
Prettier lives in `~/.local/share/dotfiles/node`; neither requires global pip/npm
changes. `make render` and `make test` discover the installed Python environment.
The formatter also discovers the managed tools without a PATH change or shell restart.
Installation records the validated Node location so an older inherited PATH cannot
override Node when Prettier runs. `make doctor` checks the selected Python runtime.
The generated Zsh configuration adds their directories to PATH for new shells.

`plugins.json` records exact public plugin URLs and revisions. Installation
verifies each checkout before linking it from `~/.local/share/dotfiles/plugins`,
including when the source is a downloaded snapshot without Git metadata.
Reruns reuse verified caches. Network or version failures leave installation
incomplete; rerun the same command after fixing access.

OpenSSL is needed only for optional secrets commands and their tests. Applications
such as btop, htop, and Ghostty are optional; install them separately if you use them.
The terminal configuration and Ghostty terminal entry are supplied even on SSH hosts
where the Ghostty application is not installed.

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
files are absent. It preserves existing settings. Installation compiles and checks
Ghostty terminfo in `~/.terminfo` for the selected user, without modifying system
databases. Install on each remote SSH host that receives `TERM=xterm-ghostty`. Add
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

After `make install`:

```sh
make doctor
make test
tmux -f "$HOME/.tmux.conf" -L dotfiles-smoke new-session -d
tmux -L dotfiles-smoke kill-server
```

Run the tmux commands as a pair after `make install`; the isolated socket avoids
your live sessions. Linux tests have passed. macOS and WSL2 checks have not been
run; use these commands on those hosts. In WSL2, use the Linux shell.
