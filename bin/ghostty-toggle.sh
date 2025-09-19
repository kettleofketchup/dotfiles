#!/usr/bin/env bash
# Toggle Ghostty as a dropdown terminal (fullscreen on F1)
APP="ghostty"
WM_CLASS="Ghostty"
BASHCMD="bash -c tmux attach || tmux new"
CMD="ghostty --class=$WM_CLASS --fullscreen -e $BASHCMD"
# tdrop options:
# -ma   : match by WM_CLASS
# -w    : window width in %
# -h    : window height in %
# -y    : drop from top (y=0)
tdrop -ma -w 5000 -h 5000 -y 0 -a $CMD