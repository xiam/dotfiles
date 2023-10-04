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
  eval $(keychain --eval $HOME/.ssh/id_rsa)
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

# Android SDK
if [ -d "/Users/$USER/Library/Android/sdk" ]; then
  export ANDROID_HOME="/Users/$USER/Library/Android/sdk"
  export PATH=${PATH}:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools
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

if [ -d "/cygdrive" ]; then
  export PATH="$PATH:/cygdrive/c/Users/josec/AppData/Roaming/npm/"
fi

bindkey -e
