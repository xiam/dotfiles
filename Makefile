SHELL := /bin/sh
DOTFILES_HOME ?= $(HOME)

.PHONY: all install doctor render plugins terminfo secrets-encrypt secrets-decrypt secrets-install test

all: install

install:
	sh scripts/bootstrap.sh

doctor:
	sh scripts/python.sh scripts/doctor.py

render:
	sh scripts/python.sh scripts/render.py

# Install includes these pinned packages automatically.
plugins:
	sh scripts/bootstrap.sh

# Install includes this entry automatically, without changing system databases.
terminfo:
	tic -x -o "$${DOTFILES_HOME:-$$HOME}/.terminfo" third-party/xterm-ghostty.terminfo

secrets-encrypt:
	sh scripts/python.sh scripts/secrets.py encrypt

secrets-decrypt:
	sh scripts/python.sh scripts/secrets.py decrypt

secrets-install:
	sh scripts/python.sh scripts/secrets.py install

test:
	sh scripts/python.sh -m unittest discover -s tests -v
