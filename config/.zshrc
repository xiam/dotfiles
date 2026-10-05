# Zsh Kanagawa workstation configuration
autoload -Uz promptinit
promptinit

SAVEHIST=99999
setopt SHARE_HISTORY INC_APPEND_HISTORY HIST_IGNORE_DUPS
HISTFILE=~/.zsh_history

autoload -Uz compinit
compinit
zstyle ':completion:*' menu select
zstyle ':completion:*' matcher-list '' 'm:{a-z}={A-Z}' 'm:{a-zA-Z}={A-Za-z}'

autoload -Uz vcs_info
precmd() { vcs_info }
if [[ "$COLORTERM" == truecolor || "$COLORTERM" == 24bit ]]; then
  typeset -g DOTFILES_COLOR_USER=$'%{\e[38;2;149,127,184m%}'
  typeset -g DOTFILES_COLOR_HOST=$'%{\e[38;2;152,187,108m%}'
  typeset -g DOTFILES_COLOR_PATH=$'%{\e[38;2;126,156,216m%}'
  typeset -g DOTFILES_COLOR_GIT=$'%{\e[38;2;230,195,132m%}'
else
  typeset -g DOTFILES_COLOR_USER='%F{magenta}'
  typeset -g DOTFILES_COLOR_HOST='%F{green}'
  typeset -g DOTFILES_COLOR_PATH='%F{blue}'
  typeset -g DOTFILES_COLOR_GIT='%F{yellow}'
fi
zstyle ':vcs_info:git:*' formats " ${DOTFILES_COLOR_GIT}(%b)%f"
setopt PROMPT_SUBST
PROMPT='${DOTFILES_COLOR_USER}%n%f@${DOTFILES_COLOR_HOST}%m%f:${DOTFILES_COLOR_PATH}%~%f${vcs_info_msg_0_}%# '
bindkey -e

export EDITOR=vim
export VISUAL=vim

# Add only existing user tool directories; preserve the inherited PATH.
typeset -U path PATH
for dotfiles_path in "$HOME/.local/share/dotfiles/python/bin" \
  "$HOME/.local/share/dotfiles/node/bin" "$HOME/.local/bin" "$HOME/bin" "$HOME/go/bin" \
  "/usr/local/go/bin" "$HOME/.cargo/bin" "$HOME/.pulumi/bin" \
  "$HOME/.yarn/bin" "$HOME/.local/share/pnpm" "$HOME/.rvm/bin" \
  "$HOME/opt/processing"; do
  [[ -d "$dotfiles_path" ]] && path=("$dotfiles_path" $path)
done

if [[ -d /opt/homebrew/bin ]]; then path=(/opt/homebrew/bin $path); fi
if [[ -d /usr/local/bin ]]; then path=(/usr/local/bin $path); fi

# Prefer the current Android variable, then its legacy alias, then existing
# platform defaults. Never invent SDK paths; valid caller values take precedence.
typeset dotfiles_android_sdk=''
if [[ -n "${ANDROID_HOME:-}" && -d "$ANDROID_HOME" ]]; then
  dotfiles_android_sdk="$ANDROID_HOME"
elif [[ -n "${ANDROID_SDK_ROOT:-}" && -d "$ANDROID_SDK_ROOT" ]]; then
  dotfiles_android_sdk="$ANDROID_SDK_ROOT"
  export ANDROID_HOME="$ANDROID_SDK_ROOT"
elif [[ -d "$HOME/Library/Android/sdk" ]]; then
  dotfiles_android_sdk="$HOME/Library/Android/sdk"
  export ANDROID_HOME="$dotfiles_android_sdk"
  export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$dotfiles_android_sdk}"
elif [[ -d "$HOME/Android/Sdk" ]]; then
  dotfiles_android_sdk="$HOME/Android/Sdk"
  export ANDROID_HOME="$dotfiles_android_sdk"
  export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$dotfiles_android_sdk}"
fi
if [[ -n "$dotfiles_android_sdk" && -d "$dotfiles_android_sdk/platform-tools" ]]; then
  path=("$dotfiles_android_sdk/platform-tools" $path)
fi
unset dotfiles_android_sdk

if [[ -d "$HOME/.nvm" ]]; then
  export NVM_DIR="$HOME/.nvm"
  [[ -s "$NVM_DIR/nvm.sh" ]] && source "$NVM_DIR/nvm.sh"
fi
[[ -f "$HOME/.cargo/env" ]] && source "$HOME/.cargo/env"
[[ -f "$HOME/.nix-profile/etc/profile.d/nix.sh" ]] && source "$HOME/.nix-profile/etc/profile.d/nix.sh"

# Workstation-specific settings load last. Absence is normal.
[[ -r "$HOME/.zshrc.local" ]] && source "$HOME/.zshrc.local"
