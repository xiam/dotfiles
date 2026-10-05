#!/bin/sh
# Use the installed user environment for rendering, tests, and secrets commands.
set -eu
dotfiles_home=${DOTFILES_HOME:-$HOME}
dotfiles_python="$dotfiles_home/.local/share/dotfiles/python/bin/python"
if [ -x "$dotfiles_python" ]; then
    exec "$dotfiles_python" "$@"
fi
exec python3 "$@"
