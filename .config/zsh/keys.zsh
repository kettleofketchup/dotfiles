
# Keybindings
# bindkey -e
# bindkey '^p' history-search-backward
# bindkey '^n' history-search-forward
# bindkey '^[w' kill-region
bindkey "^A" beginning-of-line             # Ctrl-A
bindkey "^[[H" beginning-of-line           # xterm
bindkey "^[OH" beginning-of-line           # tmux / some terms
bindkey "\e[1~" beginning-of-line          # Linux console

bindkey '^E' end-of-line
bindkey "^E" end-of-line                  # Ctrl-E
bindkey "^[[F" end-of-line                 # xterm
bindkey "^[OF" end-of-line                 # tmux / some terms
bindkey "\e[4~" end-of-line                # Linux console

bindkey '^U' backward-kill-line
bindkey '^K' kill-line
bindkey '^W' backward-kill-word
bindkey '^H' backward-delete-char
bindkey '^A' beginning-of-line
bindkey '^E' end-of-line


bindkey "^[[2~" overwrite-mode


