autoload -Uz promptinit
promptinit
prompt restore

SAVEHIST=99999
HISTFILE=~/.zsh_history

autoload -Uz compinit
compinit

zstyle ':completion:*' auto-description 'specify: %d'
zstyle ':completion:*' completer _expand _complete _correct _approximate
zstyle ':completion:*' format 'Completing %d'
zstyle ':completion:*' group-name ''
zstyle ':completion:*' menu select=2
zstyle ':completion:*:default' list-colors ${(s.:.)LS_COLORS}
zstyle ':completion:*' list-colors ''
zstyle ':completion:*' list-prompt %SAt %p: Hit TAB for more, or the character to insert%s
zstyle ':completion:*' matcher-list '' 'm:{a-z}={A-Z}' 'm:{a-zA-Z}={A-Za-z}' 'r:|[._-]=* r:|=* l:|=*'
zstyle ':completion:*' menu select=long
zstyle ':completion:*' select-prompt %SScrolling active: current selection at %p%s
zstyle ':completion:*' use-compctl false
zstyle ':completion:*' verbose true

zstyle ':completion:*:*:kill:*:processes' list-colors '=(#b) #([0-9]#)*=0=01;31'
zstyle ':completion:*:kill:*' command 'ps -u $USER -o pid,%cpu,tty,cputime,cmd'

prompt suse

export LC_ALL=en_US.UTF-8

export VAGRANT_DEFAULT_PROVIDER=virtualbox

# Go
export GOROOT=/usr/local/go
export GOPATH=$HOME/go

export PATH=/usr/local/bin:$HOME/bin:$GOROOT/bin:$GOPATH/bin:$PATH

export EDITOR=vim

if [ -x "$(command -v keychain)" ]; then
  eval $(keychain -q --eval $(find ~/.ssh -type f \( -name "id_rsa*" -o -name "id_ed25519*" \) | grep -v '\.pub'))
fi

# Processing
export PATH=$PATH:$HOME/opt/processing

# Arduino
export PATH=$PATH:$HOME/opt/arduino

# NVM
export NVM_DIR="$HOME/.nvm"
if [ -d $NVM_DIR ]; then
  [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
fi

[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

# Android SDK (OSX)
if [ -d "/Users/$USER/Library/Android/sdk" ]; then
  export ANDROID_SDK_ROOT="/Users/$USER/Library/Android/sdk"
fi

# Android SDK (Linux)
if [ -d "/usr/lib/android-sdk" ]; then
  export ANDROID_SDK_ROOT="/usr/lib/android-sdk"
fi

if [ ! -z "$ANDROID_SDK_ROOT" ]; then
  export PATH=${PATH}:$ANDROID_SDK_ROOT/tools:$ANDROID_SDK_ROOT/platform-tools
fi


if [ -d "$HOME/.rvm/bin" ]; then
  # Add RVM to PATH for scripting. Make sure this is the last PATH variable change.
  export PATH="$PATH:$HOME/.rvm/bin"
fi

# add Pulumi to the PATH
if [ -d "$HOME/.pulumi/bin" ]; then
  export PATH="$PATH:$HOME/.pulumi/bin"
fi

# yarn
if [ -d "$HOME/.yarn/bin" ]; then
  export PATH="$HOME/.yarn/bin:$HOME/.config/yarn/global/node_modules/.bin:$PATH"
fi

# cygwin
if [ -d "/cygdrive" ]; then
  export PATH="$PATH:/cygdrive/c/Users/$USER/AppData/Roaming/npm/"
  export GOPATH="c:\\Users\\$USER\\go"
  export GOROOT=c:\\Program\ Files\\Go
  export PATH=$PATH:$GOPATH\\bin
fi

# nixOS
if [ -f $HOME/.nix-profile/etc/profile.d/nix.sh ]; then
  . $HOME/.nix-profile/etc/profile.d/nix.sh
fi

# The next line updates PATH for the Google Cloud SDK.
if [ -f '/tmp/google-cloud-sdk/path.zsh.inc' ]; then
  . '/tmp/google-cloud-sdk/path.zsh.inc';
fi

# The next line enables shell command completion for gcloud.
if [ -f '/tmp/google-cloud-sdk/completion.zsh.inc' ]; then
  . '/tmp/google-cloud-sdk/completion.zsh.inc';
fi

if [ -f "$HOME/.cargo/env" ]; then
  source "$HOME/.cargo/env"
fi

bindkey -e
