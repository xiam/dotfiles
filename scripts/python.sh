#!/bin/sh
# Use the Python environment installed by make install without network activity.
set -eu
dotfiles_home=${DOTFILES_HOME:-$HOME}
python="$dotfiles_home/.local/share/dotfiles/python-current/bin/python"
[ -x "$python" ] || { printf '%s\n' 'Managed Python is absent; run make install separately.' >&2; exit 1; }
exec "$python" -I "$@"
