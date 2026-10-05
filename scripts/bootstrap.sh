#!/bin/sh
# Bootstrap the system dependencies before running the Python installer.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
fail() { printf '%s\n' "Setup failed: $*" >&2; exit 1; }
has() { command -v "$1" >/dev/null 2>&1; }
version_ok() {
    printf '%s\n' "$1" | awk -v minimum="$2" '
      { if (match($0, /[0-9]+\.[0-9]+/)) {
          split(substr($0, RSTART, RLENGTH), got, "."); split(minimum, want, ".");
          exit !(got[1] > want[1] || (got[1] == want[1] && got[2] >= want[2]));
        } exit 1 }'
}
PYTHON=
find_python() {
    PYTHON=
    for candidate in python3 python3.14 python3.13 python3.12 python3.11 python3.10; do
        if has "$candidate" && "$candidate" -c 'import sys, ssl, venv, ensurepip, pip; assert sys.version_info >= (3,10); assert ssl.create_default_context().cert_store_stats()["x509_ca"] > 0' >/dev/null 2>&1; then
            PYTHON=$candidate
            return 0
        fi
    done
    return 1
}
missing=
add() { missing="$missing $1"; }
check() {
    missing=
    find_python || add python
    has vim && version_ok "$(vim --version 2>/dev/null)" 9.0 || add vim
    has tmux && version_ok "$(tmux -V 2>/dev/null)" 3.2 || add tmux
    has zsh && version_ok "$(zsh --version 2>/dev/null)" 5.8 || add zsh
    { has git && git --version >/dev/null 2>&1; } || add git
    { has make && make --version >/dev/null 2>&1; } || add make
    { has tic && tic -V >/dev/null 2>&1 && has infocmp && infocmp -V >/dev/null 2>&1; } || add terminfo
    { has node && version_ok "$(node --version 2>/dev/null)" 18.0 && has npm && npm --version >/dev/null 2>&1; } || add node
    has gofmt || add go
    { has rustfmt && rustfmt --version >/dev/null 2>&1; } || add rust
}
run_privileged() {
    if [ "$(id -u)" = 0 ]; then "$@"; else
        has sudo || fail "sudo is required to install system packages. Install sudo or run setup as root."
        sudo "$@"
    fi
}
brew_path() {
    for directory in /opt/homebrew/bin /usr/local/bin; do
        if [ -x "$directory/brew" ]; then PATH="$directory:$PATH"; export PATH; return; fi
    done
}
check
if [ -n "$missing" ]; then
    system=$(uname -s)
    manager=
    if [ "$system" = Darwin ]; then
        brew_path
        if ! has brew; then
            has curl || fail "curl is required to install Homebrew."
            has bash || fail "bash is required to install Homebrew."
            installer=$(mktemp) || fail "Cannot create Homebrew installer."
            trap 'rm -f "$installer"' EXIT HUP INT TERM
            curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh -o "$installer" || fail "Cannot download Homebrew installer."
            NONINTERACTIVE=1 bash "$installer" || fail "Homebrew installation failed."
            rm -f "$installer"
            trap - EXIT HUP INT TERM
            brew_path
        fi
        has brew || fail "Homebrew installation did not provide brew."
        manager=brew
    elif [ "$system" = Linux ]; then
        if has apt-get; then manager=apt; elif has dnf; then manager=dnf; elif has pacman; then manager=pacman; fi
    fi
    [ -n "$manager" ] || fail "Unsupported system: install the missing dependencies manually:$missing"
    packages=
    for requirement in $missing; do
        case "$manager:$requirement" in
            apt:python) package='python3 python3-venv python3-pip ca-certificates' ;;
            dnf:python) package='python3 python3-pip ca-certificates' ;;
            pacman:python) package='python python-pip ca-certificates' ;;
            brew:python) package='python ca-certificates' ;;
            apt:terminfo) package='ncurses-bin' ;;
            dnf:terminfo) package='ncurses' ;;
            pacman:terminfo|brew:terminfo) package='ncurses' ;;
            apt:node|dnf:node|pacman:node) package='nodejs npm' ;;
            brew:node) package='node' ;;
            apt:go) package='golang-go' ;;
            dnf:go) package='golang' ;;
            pacman:go|brew:go) package='go' ;;
            apt:rust) package='rustfmt rustc' ;;
            dnf:rust) package='rustfmt' ;;
            pacman:rust) package='rust' ;;
            brew:rust) package='rust' ;;
            *) package=$requirement ;;
        esac
        packages="$packages $package"
    done
    printf 'Installing required dependencies:%s\n' "$packages"
    # Package names above are fixed words, never user input.
    case "$manager" in
        apt) run_privileged apt-get update || fail "apt package index update failed."
             run_privileged apt-get install -y --no-install-recommends $packages || fail "apt dependency installation failed." ;;
        dnf) run_privileged dnf install -y $packages || fail "dnf dependency installation failed." ;;
        pacman) run_privileged pacman -Syu --needed --noconfirm $packages || fail "pacman dependency installation failed." ;;
        brew) brew install $packages || fail "Homebrew dependency installation failed."
              brew upgrade $packages || fail "Homebrew dependency upgrade failed."
              brew_path
              if has brew; then
                  prefix=$(brew --prefix)
                  PATH="$prefix/bin:$prefix/opt/python/libexec/bin:$prefix/opt/ncurses/bin:$PATH"
                  export PATH
              fi ;;
    esac
    check
    [ -z "$missing" ] || fail "Dependencies still unavailable or below minimum versions:$missing. Update the OS/package sources and retry."
fi
exec "$PYTHON" "$ROOT/scripts/setup.py" "$@"
