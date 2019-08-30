# Set up the prompt

autoload -Uz promptinit
promptinit
prompt walters

# Use emacs keybindings even if our EDITOR is set to vi
bindkey -e

# Keep 1000 lines of history within the shell and save it to ~/.zsh_history:
SAVEHIST=1000
HISTFILE=~/.zsh_history

# Use modern completion system
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

export GOROOT=/usr/local/go
export GOPATH=$HOME/go
export PATH=$PATH:$GOROOT/bin:$GOPATH/bin:$HOME/bin

#PROMPT='%b%s%u%m:%B %3c %b%# %B'
#PROMPT=$'%{\e[0;37m%}%B%*%b %{\e[0;35m%}%m:%{\e[0;37m%}%~ %(!.#.>) %{\e[00m%} %B'
#PROMPT=$'%{\e[0;37m%}%B%*%b %{\e[0;35m%}%m:%{\e[0;37m%}%~ %(!.#.>) %{\e[00m%} %B'
#PROMPT=$'%{\e[0;32m%}%m:%{\e[0;37m%}%~ %(!.#.>) %{\e[00m%}%B'
#RPROMPT=""
#POSTEDIT=`print -P -n %b`

autoload -U promptinit
promptinit
prompt suse

export LC_ALL=en_US.UTF-8

if [ -d $HOME/Library ]; then
  export ANDROID_HOME=$HOME/Library/Android/sdk
  export ANDROID_SDK_TOOLS=$ANDROID_HOME/tools/
  export ANDROID_PLATFORM_TOOLS=$ANDROID_HOME/platform-tools/
  export ANDROID_NDK_PATH=/Users/rev/opt/android/android-ndk-r10e
  export ANDROID_BUILD_TOOLS_BIN=/Users/rev/Library/Android/sdk/build-tools/22.0.1/
  export PATH=$PATH:$ANDROID_SDK_TOOLS:$ANDROID_PLATFORM_TOOLS:$ANDROID_NDK_PATH:$ANDROID_BUILD_TOOLS_BIN
  export PATH=$PATH:/Users/rev/Library/Android/sdk/build-tools/22.0.1/aapt
fi

export VAGRANT_DEFAULT_PROVIDER=virtualbox

export PATH=$PATH:$PWD/fakebin
