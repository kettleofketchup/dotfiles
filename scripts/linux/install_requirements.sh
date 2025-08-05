#!/bin/bash
echo " we are assuming you are in the dotfiles directory"
sudo apt update -y
sudo apt install curl git build-essential stow zsh fzf imgcat -y

sudo apt install stow zsh p7zip-full catimg chafa libevent-dev \
    ncurses-dev libncurses-dev build-essential bison \
    pkg-config tmux bat -y




./scripts/linux/languages/nvm.sh
./scripts/linux/languages/rust.sh
./scripts/linux/languages/go.sh
./scripts/linux/languages/python.sh




