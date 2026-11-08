# Setup and customization

[Quick start](../README.md)

## Automatic setup

Run `make install` after cloning. Git and Make are entry prerequisites.
Supported profiles cover Debian 13 amd64 and Ubuntu Server 24.04/26.04 amd64.
macOS installation remains disabled and untested. Other releases and architectures
are rejected; WSL-specific execution has not been tested. Installation normally
needs internet access and may request sudo on Linux.

APT installs the exact versions in `security/*.packages.txt` using the host's
configured repositories and standard repository signature and archive-hash checks.
Companion packages with exact version dependencies, such as Vim's runtime, are
pinned alongside their applications. Installation does not enable unauthenticated
repositories or automatic downgrades. A missing pinned version, incompatible
installed package, or failed authentication stops setup; adjust pins through a
normal repository change rather than disabling package-manager checks.

Python dependencies and Ruff live in a managed environment selected by
`~/.local/share/dotfiles/python-current`. Pip enforces
`security/requirements-lock.txt` with `--require-hashes`. Lock or Python-base changes
preserve the old environment and create a replacement. Prettier lives in
`~/.local/share/dotfiles/node`; `npm ci` enforces the existing package lock and
registry integrity hashes with lifecycle scripts disabled. Neither needs global
pip/npm changes. The formatter discovers these tools without a shell restart.
Installation records the Node location used for managed Prettier.

`plugins.json` records exact HTTPS Git URLs and commit IDs. Installation fetches
those commits, checks Git's checkout identity and clean working tree, and links
plugins from `~/.local/share/dotfiles/plugins`. Personal changes and foreign links
are preserved. Git checks pinned content; this does not assert a separate
maintainer signature or provenance policy.

`make doctor` reports tool availability and minimum versions. Rendering, formatting,
tests, and secrets commands run locally through the installed Python environment.
They do not contact registries, renew evidence, or require a custom policy date.
Missing dependencies require a separate `make install`. Native package-manager
updates remain the operating system's responsibility.

Applications such as btop, htop, and Ghostty are optional; install them separately
if you use them. The terminal configuration and Ghostty terminal entry are supplied
even on SSH hosts where the Ghostty application is absent.

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
your live sessions. Linux tests have passed. macOS installation remains disabled;
macOS and WSL2 checks have not been run. In WSL2, use the Linux shell.
