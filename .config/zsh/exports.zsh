#!/bin/sh
# HISTFILE="$XDG_DATA_HOME"/zsh/history

export EDITOR="nvim"
export TERMINAL="ghostty"
# export BROWSER="firefox"

export PATH="$HOME/.docker/bin":$PATH
# export PATH="$HOME/.local/nvim-macos-arm64/bin":$PATH
export MANWIDTH=999
export PATH=$PATH:/usr/local/go/bin



export PATH=$PATH:/usr/local/go/bin
[[ -d "$HOME/.local/share/go/bin" ]] && export PATH="$HOME/.local/share/go/bin:$PATH"
[[ -d "$HOME/.cargo/bin" ]] && export PATH="$HOME/.cargo/bin:$PATH"
[[ -d "$HOME/.local/bin" ]] && export PATH="$HOME/.local/bin:$PATH"
[[ -d "$HOME/bin" ]] && export PATH="$HOME/bin:$PATH"

export GOPATH=$HOME/.local/share/go
export PATH=$HOME/.fnm:$PATH
export PATH="$HOME/.local/share/neovim/bin":$PATH
export PATH="$HOME/.local/share/bob/nvim-bin":$PATH
# export XDG_CURRENT_DESKTOP="Wayland"
export HOMEBREW_NO_ANALYTICS=1
export HOMEBREW_NO_ENV_HINTS=1
#export PATH="$PATH:./node_modules/.bin"
# eval "$(fnm env)"
# eval "$(zoxide init zsh)"
# eval "`pip completion --zsh`"
export NVM_DIR="$HOME/.nvm"
if ! command -v kettle >/dev/null 2>&1; then
    echo "Kettle is not installed"
    echo "Installing kettle to ~/.local/bin/kettle"
    wget -O ~/.local/bin/kettle https://github.com/kettleofketchup/kettle/releases/latest/download/kettle
    chmod +x ~/.local/bin/kettle
    echo "Kettle installed. Make sure ~/.local/bin is in your PATH"

fi


