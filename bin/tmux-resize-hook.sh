#!/bin/bash -
last_width=$(tmux display -p "@last_width")
width=$(tmux display -p "#{client_width}")
if [ "$width" != "$last_width" ]; then
    tmux set -g @last_width "$width"
else
    exit 0    
fi
tmux run-shell "~/bin/tmux-set-plugins.sh"

if [ -f "~/.tmux/plugins/tmux2k/tmux2k.tmux" ]; then
  tmux source-file ~/.tmux/plugins/tmux2k/tmux2k.tmux >/dev/null 2>&1
else
  tmux source-file ~/.tmux.conf >/dev/null 2>&1
fi

# Force a status-line refresh
tmux refresh-client -S