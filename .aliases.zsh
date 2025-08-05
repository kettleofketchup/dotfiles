#!/bin/zsh
command -v lsd > /dev/null && alias ls='lsd --config-file="$HOME/.ls.config"'
command -v lsd > /dev/null && alias tree='lsd --tree --config-file="$HOME/.ls.config"'
command -v bat > /dev/null && alias cat='bat --style=header,header-filename,header-filesize,grid'
alias cat='bat --style="grid,header"'
alias vim='nvim'
alias c='clear'

# alias cd='z'