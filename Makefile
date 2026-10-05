SHELL := /bin/sh

.PHONY: all install doctor render plugins terminfo secrets-encrypt secrets-decrypt secrets-install test

all: install

install:
	python3 scripts/install.py

doctor:
	python3 scripts/doctor.py

render:
	python3 scripts/render.py

# Network access is explicit. The submodule gitlinks pin each plugin revision.
plugins:
	git submodule update --init --recursive

# Optional Ghostty terminal entry; uses the system tic database for this user.
terminfo:
	tic -x third-party/xterm-ghostty.terminfo

secrets-encrypt:
	python3 scripts/secrets.py encrypt

secrets-decrypt:
	python3 scripts/secrets.py decrypt

secrets-install:
	python3 scripts/secrets.py install

test:
	python3 -m unittest discover -s tests -v
