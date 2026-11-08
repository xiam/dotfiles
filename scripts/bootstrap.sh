#!/bin/sh
# Let the operating system package manager authenticate and install native tools.
set -eu
PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PATH
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
fail() { printf '%s\n' "Setup failed: $*" >&2; exit 1; }
[ -z "${APT_CONFIG:-}" ] || fail 'Inherited APT_CONFIG is unsupported; retain normal repository authentication.'
case "$(uname -s)" in
    Linux)
        [ -r /etc/os-release ] || fail 'Missing operating-system identity.'
        . /etc/os-release
        case "${ID:-}:${VERSION_ID:-}:$(dpkg --print-architecture 2>/dev/null || true)" in
            debian:13:amd64) profile=debian-13-amd64 ;;
            ubuntu:24.04:amd64) profile=ubuntu-24.04-amd64 ;;
            ubuntu:26.04:amd64) profile=ubuntu-26.04-amd64 ;;
            *) fail 'Unsupported operating system or architecture.' ;;
        esac
        if [ "$(id -u)" = 0 ]; then
            apt-get update --error-on=any -o Acquire::AllowInsecureRepositories=false -o Acquire::AllowDowngradeToInsecureRepositories=false
            sed '/^#/d; /^$/d' "$ROOT/security/$profile.packages.txt" | \
                xargs apt-get install --yes --no-install-recommends --no-remove --no-allow-unauthenticated
        else
            command -v sudo >/dev/null || fail 'Install sudo or run the installer as root.'
            sudo apt-get update --error-on=any -o Acquire::AllowInsecureRepositories=false -o Acquire::AllowDowngradeToInsecureRepositories=false
            sed '/^#/d; /^$/d' "$ROOT/security/$profile.packages.txt" | \
                xargs sudo apt-get install --yes --no-install-recommends --no-remove --no-allow-unauthenticated
        fi
        ;;
    Darwin) fail 'macOS installation is disabled and untested.' ;;
    *) fail 'Unsupported operating system.' ;;
esac
exec /usr/bin/python3 -I "$ROOT/scripts/setup.py" "$@"
