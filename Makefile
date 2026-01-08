export SHELL := /bin/bash

all: deps
	$(call check_cmd,vim,_config-vim)
	$(call check_cmd,zsh,_config-zsh)
	$(call check_cmd,arduino,_config-arduino)
	$(call check_cmd,git,_config-git)
	$(call check_cmd,tmux,_config-tmux)
	$(call check_cmd,ghostty,_config-ghostty)
	@$(MAKE) --no-print-directory _config-misc
	@$(MAKE) --no-print-directory config-secrets

define link
	export TARGET_FILE=$$PWD/$2 && \
	export CONFIG_FILE=$3 && \
	export DIRNAME=$$(dirname $$CONFIG_FILE) && \
	echo "$1: $$CONFIG_FILE -> $$TARGET_FILE" && \
	mkdir -p $$DIRNAME && \
	rm -rf $$CONFIG_FILE && \
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

define check_cmd
	@if command -v $(1) >/dev/null 2>&1; then \
		$(MAKE) --no-print-directory $(2); \
	else \
		echo "SKIP: $(1) not found, skipping $(2)"; \
	fi
endef

deps:
	git submodule init && \
	git submodule update

_config-vim:
	if [ -L ~/.vim ]; then rm ~/.vim; fi
	mkdir -p ~/.vim
	find ~/.vim -xtype l -delete
	@$(call link_file,config/.vimrc,~/.vimrc)
	@$(call link_subfiles,config/.vim/autoload,~/.vim/autoload)
	@$(call link_subfiles,config/.vim/colors,~/.vim/colors)
	@$(call link_subdirectories,config/.vim/bundle,~/.vim/bundle)
	@$(call link_subdirectories,config/.vim/pack/ai/start,~/.vim/pack/ai/start)

_config-zsh:
	@$(call link_file,config/.zshrc,~/.zshrc)

_config-arduino:
	@$(call link_directory,config/.arduino15,~/.arduino15)

_config-git:
	@$(call link_file,config/.gitconfig,~/.gitconfig)

_config-tmux:
	@$(call link_file,config/.tmux.conf,~/.tmux.conf)

_config-misc:
	if [ -L ~/.config ]; then rm ~/.config; fi
	@$(call link_subdirectories,config/.config,~/.config)

_config-ghostty:
	tic -x ./third-party/xterm-ghostty.terminfo

# Convenience targets with command checks
config-vim:
	$(call check_cmd,vim,_config-vim)

config-zsh:
	$(call check_cmd,zsh,_config-zsh)

config-arduino:
	$(call check_cmd,arduino,_config-arduino)

config-git:
	$(call check_cmd,git,_config-git)

config-tmux:
	$(call check_cmd,tmux,_config-tmux)

config-ghostty:
	$(call check_cmd,ghostty,_config-ghostty)

config-misc: _config-misc

secrets-encrypt:
	@if [ ! -d secrets ]; then \
		echo "ERROR: secrets/ directory not found"; \
		exit 1; \
	fi
	tar czf - secrets | openssl enc -aes-256-cbc -pbkdf2 -out secrets.tar.gz.enc
	@echo "Encrypted secrets/ -> secrets.tar.gz.enc"

secrets-decrypt:
	@if [ ! -f secrets.tar.gz.enc ]; then \
		echo "ERROR: secrets.tar.gz.enc not found"; \
		exit 1; \
	fi
	openssl enc -aes-256-cbc -pbkdf2 -d -in secrets.tar.gz.enc | tar xzf -
	@echo "Decrypted secrets.tar.gz.enc -> secrets/"

config-secrets:
	@if [ ! -f secrets.tar.gz.enc ]; then \
		echo "SKIP: secrets.tar.gz.enc not found"; \
		exit 0; \
	fi
	@if [ ! -d secrets ]; then \
		if [ -n "$$DOTFILES_SECRETS_PASS" ]; then \
			echo "Decrypting secrets (using DOTFILES_SECRETS_PASS)..."; \
			if ! echo "$$DOTFILES_SECRETS_PASS" | openssl enc -aes-256-cbc -pbkdf2 -d -pass stdin -in secrets.tar.gz.enc | tar xzf -; then \
				echo "SKIP: Failed to decrypt secrets (wrong password)"; \
				exit 0; \
			fi; \
		elif [ -t 0 ]; then \
			echo "Decrypting secrets..."; \
			if ! openssl enc -aes-256-cbc -pbkdf2 -d -in secrets.tar.gz.enc | tar xzf -; then \
				echo "SKIP: Failed to decrypt secrets (wrong password or cancelled)"; \
				exit 0; \
			fi; \
		else \
			echo "SKIP: Non-interactive mode, set DOTFILES_SECRETS_PASS to decrypt secrets"; \
			exit 0; \
		fi; \
	fi
	@echo "Installing secrets..."
	@find secrets -type f | while read -r file; do \
		src="$$PWD/$$file"; \
		dest="$$HOME/$${file#secrets/}"; \
		dir=$$(dirname "$$dest"); \
		mkdir -p "$$dir"; \
		rm -f "$$dest"; \
		ln -sfn "$$src" "$$dest"; \
		echo "S: $$dest -> $$src"; \
	done
