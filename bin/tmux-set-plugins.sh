#!/bin/bash
width=$(tmux display -p "#{client_width}")
set_plugin_vars() {
  tmux set -gq @tmux2k-left-plugins "$1"
  tmux set -gq @tmux2k-right-plugins "$2"
}


# choose layout
if [ "$width" -ge 140 ]; then
    set_plugin_vars "session git gpu cpu ram" "ping bandwidth network time"

elif [ "$width" -ge 120 ]; then
    set_plugin_vars "session git cpu ram" "ping bandwidth network time"

elif [ "$width" -ge 100 ]; then
    set_plugin_vars "session git ram" "ping network time"
elif [ "$width" -ge 80 ]; then
    set_plugin_vars "session git" "network time"
elif [ "$width" -ge 60 ]; then
    set_plugin_vars "session git" "time"
else
    set_plugin_vars "session" "time"
fi
