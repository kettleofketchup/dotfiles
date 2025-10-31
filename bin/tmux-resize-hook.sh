#!/bin/bash -x
tmux run-shell "bash -x ~/bin/tmux-set-plugins.sh"
if [ -f ~/.tmux/plugins/tmux2k/tmux2k.tmux ]; then
  tmux source-file ~/.tmux/plugins/tmux2k/tmux2k.tmux >/dev/null 2>&1
else
  tmux source-file ~/.tmux.conf >/dev/null 2>&1
fi

# Force a status-line refresh
tmux refresh-client -S