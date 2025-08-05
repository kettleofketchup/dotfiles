#!/bin/bash
function install_fonts () {
    echo " we are assuming you are in the dotfiles directory"
    echo " Ubuntu 20-22"

    mkdir -p ~/.local/share/fonts/ >/dev/null 2>&1
    cp fonts/*.ttf ~/.local/share/fonts/
    fc-cache -f -v

}

install_fonts