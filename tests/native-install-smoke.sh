#!/bin/sh
# Run only in a disposable supported Linux container with a private HOME.
set -eu
[ -f /.dockerenv ] || { printf '%s\n' 'This smoke test requires a disposable Docker container.' >&2; exit 1; }
[ "$#" = 1 ] || exit 1
fixture=$(mktemp -d /tmp/dotfiles-install-smoke.XXXXXXXX)
cp -a "$1/." "$fixture/"
[ ! -f "$fixture/.git" ] || rm "$fixture/.git"
HOME=$(mktemp -d /tmp/dotfiles-home.XXXXXXXX)
export HOME
cd "$fixture"
sh scripts/bootstrap.sh
make install
make doctor
make render
make test
