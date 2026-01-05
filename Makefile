export SHELL := /bin/bash

all: deps \
	config-vim \
	config-zsh \
	config-arduino \
	config-git \
	config-tmux \
	config-zsh \
	config-ghostty \
	config-misc

define link
	export TARGET_FILE=$$PWD/$2 && \
	export CONFIG_FILE=$3 && \
	export DIRNAME=$$(dirname $$CONFIG_FILE) && \
	echo "$1: $$CONFIG_FILE -> $$TARGET_FILE" && \
	mkdir -p $$DIRNAME && \
	rm -f $$CONFIG_FILE && \
	ln -sfn $$TARGET_FILE $$CONFIG_FILE
endef

define link_file
	$(call link,F,$1,$2)
endef

define link_directory
	$(call link,D,$1,$2)
endef

define link_subfiles
	for FILE in $$(find $(1) -mindepth 1 -maxdepth 1 -type f); do \
		$(call link_file,$$FILE,$(2)/$$(basename $$FILE)); \
	done
endef

define link_subdirectories
	for DIR in $$(find $(1) -mindepth 1 -maxdepth 1 -type d); do \
		$(call link_directory,$$DIR,$(2)/$$(basename $$DIR)); \
	done
endef

deps:
	git submodule init && \
	git submodule update

config-vim:
	if [ -L ~/.vim ]; then rm ~/.vim; fi
	mkdir -p ~/.vim
	find ~/.vim -xtype l -delete
	@$(call link_file,config/.vimrc,~/.vimrc)
	@$(call link_subfiles,config/.vim/autoload,~/.vim/autoload)
	@$(call link_subfiles,config/.vim/colors,~/.vim/colors)
	@$(call link_subdirectories,config/.vim/bundle,~/.vim/bundle)
	@$(call link_subdirectories,config/.vim/pack/ai/start,~/.vim/pack/ai/start)

config-zsh:
	@$(call link_file,config/.zshrc,~/.zshrc)

config-arduino:
	@$(call link_directory,config/.arduino15,~/.arduino15)

config-git:
	@$(call link_file,config/.gitconfig,~/.gitconfig)

config-tmux:
	@$(call link_file,config/.tmux.conf,~/.tmux.conf)

config-misc:
	if [ -L ~/.config ]; then rm ~/.config; fi
	@$(call link_subdirectories,config/.config,~/.config)

config-ghostty:
	tic -x ./third-party/xterm-ghostty.terminfo
