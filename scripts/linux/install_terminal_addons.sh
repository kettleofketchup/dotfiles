#!/bin/bash


curl -s https://ohmyposh.dev/install.sh | bash -s -- -d ~/bin



curl -sSfL https://raw.githubusercontent.com/ajeetdsouza/zoxide/main/install.sh | sh
WORKING_DIR=$(pwd)

if [ ! -d "$HOME/.fzf" ]; then
  git clone --depth 1 https://github.com/junegunn/fzf.git ~/.fzf
  bash ~/.fzf/install --bin
else 
    cd ~/.fzf
    git pull
    bash ~/.fzf/install --bin
fi



cd "$WORKING_DIR"





npm install --global autoenv

cargo install lsd

./scripts/universal/install_bat.sh